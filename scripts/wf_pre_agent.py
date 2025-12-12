"""
Workflow for filtering PubMed papers by species and gene annotations.

This script implements a 4-step pipeline:
1. Fetch all PubMed IDs for specified date range (with chunking)
2. Get species/gene annotations from PubTator
3. Fetch title, abstract, MeSH from PubMed
4. Exclude model organisms and remove empty species rows

Based on MCP server implementations (sampling.py, species_annotation.py).
"""

import csv
import logging
import os
import time
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple

import requests

# ==================== CONSTANTS ====================
API_SLEEP_DELAY = 1.0  # seconds between API calls
DEFAULT_TIMEOUT = 30  # seconds for API requests


# ==================== CONFIGURATION ====================
@dataclass
class WorkflowConfig:
    """Configuration for the workflow."""

    date_start: str  # YYYYMMDD format
    date_end: str  # YYYYMMDD format
    days_per_chunk_step1: int = 3  # Days per chunk for PubMed ID fetching
    chunk_size_step2: int = 900  # PMIDs per request for PubTator
    chunk_size_step3: int = 500  # PMIDs per request for PubMed metadata
    max_retries: int = 3  # Maximum retry attempts for failed chunks
    retry_delay: int = 10  # Seconds to wait between retries
    model_species_config: str = "config/top20_organisms_with_taxid.csv"
    output_dir: str = "data/pre_agent"


# ==================== LOGGING ====================
def setup_logging(project_root: str) -> logging.Logger:
    """
    Setup logging configuration.

    Args:
        project_root: Root directory of the project

    Returns:
        Configured logger instance
    """
    log_dir = os.path.join(project_root, "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "wf_pre_agent.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file, mode="a"), logging.StreamHandler()],
    )
    return logging.getLogger(__name__)


# ==================== RETRY LOGIC ====================
def retry_failed_chunks(
    failed_items: List[Any],
    fetch_function: Callable,
    max_retries: int,
    retry_delay: int,
    logger: Optional[logging.Logger] = None,
    item_name: str = "items",
) -> Tuple[Any, List[Any]]:
    """
    Generic retry logic for failed chunks.

    Args:
        failed_items: List of items that failed to fetch
        fetch_function: Function to call for retrying (should return (results, failed_items))
        max_retries: Maximum number of retry attempts
        retry_delay: Seconds to wait between retries
        logger: Logger instance
        item_name: Name of items being retried (for logging)

    Returns:
        Tuple of (accumulated_results, remaining_failed_items)
    """
    all_results = []
    remaining_failed = failed_items

    for retry in range(max_retries):
        if not remaining_failed:
            break

        if logger:
            logger.info(
                f"Retrying {len(remaining_failed)} failed {item_name} (attempt {retry + 1}/{max_retries})"
            )

        time.sleep(retry_delay)
        retry_results, new_failed = fetch_function(remaining_failed)
        all_results.extend(retry_results) if isinstance(retry_results, list) else None
        remaining_failed = new_failed

    return all_results, remaining_failed


# ==================== STEP 1: FETCH PUBMED IDS ====================
def fetch_pubmed_ids_chunked(
    date_start: str,
    date_end: str,
    days_per_chunk: int = 3,
    retmax: int = 10000,
    logger: Optional[logging.Logger] = None,
) -> Tuple[List[str], List[Tuple[str, str]]]:
    """
    Fetch all PubMed IDs for date range with automatic chunking.

    Args:
        date_start: Start date in YYYYMMDD format
        date_end: End date in YYYYMMDD format
        days_per_chunk: Number of days per API request chunk
        retmax: Maximum results per request
        logger: Logger instance

    Returns:
        Tuple of (unique_pmids, failed_date_ranges)
    """
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    all_pmids = []
    failed_ranges = []

    current_date = datetime.strptime(date_start, "%Y%m%d")
    end_date = datetime.strptime(date_end, "%Y%m%d")

    if logger:
        logger.info(
            f"Fetching PMIDs from {date_start} to {date_end} using {days_per_chunk}-day chunks"
        )

    chunk_count = 0
    while current_date <= end_date:
        chunk_count += 1
        chunk_end = min(current_date + timedelta(days=days_per_chunk - 1), end_date)
        start_str = current_date.strftime("%Y/%m/%d")
        end_str = chunk_end.strftime("%Y/%m/%d")

        params = {
            "db": "pubmed",
            "term": "all[filter] AND pubmed pmc open access[filter] AND journal article[pt]",
            "mindate": start_str,
            "maxdate": end_str,
            "retmax": retmax,
            "retmode": "xml",
        }

        try:
            response = requests.get(base_url, params=params, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            pmids = [id_elem.text for id_elem in root.findall(".//Id") if id_elem.text]
            all_pmids.extend(pmids)

            if logger:
                logger.info(
                    f"Chunk {chunk_count}: {start_str} to {end_str} - {len(pmids)} PMIDs"
                )

            time.sleep(API_SLEEP_DELAY)

        except Exception as e:
            if logger:
                logger.error(
                    f"Error fetching chunk {chunk_count} ({start_str} to {end_str}): {e}"
                )
            failed_ranges.append((start_str, end_str))

        current_date = chunk_end + timedelta(days=1)

    unique_pmids = list(set(all_pmids))

    if logger:
        logger.info(
            f"Total: {len(all_pmids)} PMIDs, {len(unique_pmids)} unique, {len(failed_ranges)} failed chunks"
        )

    return unique_pmids, failed_ranges


def retry_failed_date_ranges(
    failed_ranges: List[Tuple[str, str]],
    days_per_chunk: int,
    logger: Optional[logging.Logger] = None,
) -> Tuple[List[str], List[Tuple[str, str]]]:
    """
    Retry failed date ranges.

    Args:
        failed_ranges: List of (start_str, end_str) tuples in YYYY/MM/DD format
        days_per_chunk: Number of days per chunk
        logger: Logger instance

    Returns:
        Tuple of (pmids, remaining_failed_ranges)
    """
    all_pmids = []
    new_failed = []

    for start_str, end_str in failed_ranges:
        # Convert back to YYYYMMDD format for retry
        start_date = datetime.strptime(start_str, "%Y/%m/%d").strftime("%Y%m%d")
        end_date = datetime.strptime(end_str, "%Y/%m/%d").strftime("%Y%m%d")
        retry_pmids, retry_failed = fetch_pubmed_ids_chunked(
            start_date, end_date, days_per_chunk=days_per_chunk, logger=logger
        )
        all_pmids.extend(retry_pmids)
        new_failed.extend(retry_failed)

    return all_pmids, new_failed


# ==================== STEP 2: FETCH PUBTATOR ANNOTATIONS ====================
def fetch_pubtator_annotations(
    pmids: List[str], chunk_size: int = 1000, logger: Optional[logging.Logger] = None
) -> Tuple[List[Dict[str, Optional[str]]], List[List[str]]]:
    """
    Fetch species and gene annotations from PubTator.

    Args:
        pmids: List of PubMed IDs
        chunk_size: Number of PMIDs per request
        logger: Logger instance

    Returns:
        Tuple of (annotations, failed_chunks)
        Each annotation is a dict with keys: pmid, species_name, species_id, gene_name, gene_id
    """
    base_url = "https://www.ncbi.nlm.nih.gov/research/pubtator3-api/publications/export/biocxml"
    annotations = []
    failed_chunks = []

    if logger:
        logger.info(
            f"Fetching PubTator annotations for {len(pmids)} PMIDs (chunk_size={chunk_size})"
        )

    for i in range(0, len(pmids), chunk_size):
        chunk = pmids[i : i + chunk_size]
        pmids_str = ",".join(map(str, chunk))

        try:
            response = requests.post(
                base_url, json={"pmids": pmids_str}, timeout=DEFAULT_TIMEOUT
            )
            response.raise_for_status()

            if not response.content:
                raise ValueError("Empty response from PubTator API")

            root = ET.fromstring(response.content)

            for doc in root.findall(".//document"):
                pmid = doc.find(".//id").text if doc.find(".//id") is not None else None
                annots = doc.findall(".//passage/annotation")
                species_data = []
                gene_data = []

                for a in annots:
                    ann_type = a.find("infon[@key='type']")
                    if ann_type is None:
                        continue

                    text_elem = a.find("text")
                    id_elem = a.find("infon[@key='identifier']")
                    text = text_elem.text if text_elem is not None else None
                    identifier = id_elem.text if id_elem is not None else None

                    if ann_type.text == "Species" and text:
                        species_data.append((text, identifier))
                    elif ann_type.text == "Gene" and text:
                        gene_data.append((text, identifier))

                # Get most common species and gene
                species_name = (
                    Counter([s[0] for s in species_data]).most_common(1)[0][0]
                    if species_data
                    else None
                )
                species_id = (
                    next((s[1] for s in species_data if s[0] == species_name), None)
                    if species_name
                    else None
                )
                gene_name = (
                    Counter([g[0] for g in gene_data]).most_common(1)[0][0]
                    if gene_data
                    else None
                )
                gene_id = (
                    next((g[1] for g in gene_data if g[0] == gene_name), None)
                    if gene_name
                    else None
                )

                annotations.append(
                    {
                        "pmid": pmid,
                        "species_name": species_name,
                        "species_id": species_id,
                        "gene_name": gene_name,
                        "gene_id": gene_id,
                    }
                )

            if logger:
                logger.info(f"PubTator chunk {i // chunk_size + 1}: {len(chunk)} PMIDs")

            time.sleep(API_SLEEP_DELAY)

        except Exception as e:
            if logger:
                logger.error(
                    f"Error fetching PubTator chunk {i // chunk_size + 1}: {e}"
                )
            failed_chunks.append(chunk)

    if logger:
        logger.info(
            f"Total annotations: {len(annotations)}, failed chunks: {len(failed_chunks)}"
        )

    return annotations, failed_chunks


# ==================== STEP 3: FETCH PUBMED METADATA ====================
def fetch_pubmed_metadata(
    pmids: List[str], chunk_size: int = 400, logger: Optional[logging.Logger] = None
) -> Tuple[Dict[str, Dict[str, Optional[str]]], List[List[str]]]:
    """
    Fetch title, abstract, and MeSH terms from PubMed.

    Args:
        pmids: List of PubMed IDs
        chunk_size: Number of PMIDs per request
        logger: Logger instance

    Returns:
        Tuple of (metadata_dict, failed_chunks)
        metadata_dict maps PMID to dict with keys: title, abstract, mesh
    """
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    metadata = {}
    failed_chunks = []

    if logger:
        logger.info(
            f"Fetching PubMed metadata for {len(pmids)} PMIDs (chunk_size={chunk_size})"
        )

    for i in range(0, len(pmids), chunk_size):
        chunk = pmids[i : i + chunk_size]
        # Use POST to avoid URL length limitations
        data = {"db": "pubmed", "id": ",".join(chunk), "retmode": "xml"}

        try:
            response = requests.post(base_url, data=data, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()

            if not response.content:
                raise ValueError("Empty response from PubMed API")

            root = ET.fromstring(response.content)

            for article in root.findall(".//PubmedArticle"):
                pmid_elem = article.find(".//PMID")
                pmid = pmid_elem.text if pmid_elem is not None else None

                title_elem = article.find(".//ArticleTitle")
                title = title_elem.text if title_elem is not None else None

                abstract_elem = article.find(".//AbstractText")
                abstract = abstract_elem.text if abstract_elem is not None else None

                mesh_terms = [
                    m.find("DescriptorName").text
                    for m in article.findall(".//MeshHeading")
                    if m.find("DescriptorName") is not None
                ]
                mesh = "; ".join(mesh_terms) if mesh_terms else None

                if pmid:
                    metadata[pmid] = {
                        "title": title,
                        "abstract": abstract,
                        "mesh": mesh,
                    }

            if logger:
                logger.info(f"EFetch chunk {i // chunk_size + 1}: {len(chunk)} PMIDs")

            time.sleep(API_SLEEP_DELAY)

        except Exception as e:
            if logger:
                logger.error(
                    f"Error fetching metadata chunk {i // chunk_size + 1}: {e}"
                )
            failed_chunks.append(chunk)

    if logger:
        logger.info(
            f"Total metadata: {len(metadata)}, failed chunks: {len(failed_chunks)}"
        )

    return metadata, failed_chunks


# ==================== STEP 4: EXCLUDE MODEL ORGANISMS ====================
def load_model_species_config(config_path: str) -> Tuple[List[str], List[str]]:
    """
    Load model species configuration from CSV file.

    Args:
        config_path: Path to CSV file with columns 'species_name' and 'NCBI_taxonomy_id'

    Returns:
        Tuple of (species_names, taxonomy_ids)
    """
    exclude_names = []
    exclude_ids = []

    with open(config_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            exclude_names.append(row["species_name"].strip())
            exclude_ids.append(row["NCBI_taxonomy_id"].strip())

    return exclude_names, exclude_ids


def exclude_model_organisms(
    annotations: List[Dict[str, Optional[str]]],
    exclude_names: List[str],
    exclude_ids: List[str],
    logger: Optional[logging.Logger] = None,
) -> Tuple[List[Dict[str, Optional[str]]], List[Dict[str, Optional[str]]]]:
    """
    Exclude model organisms by name AND ID, and remove rows with empty species.

    Args:
        annotations: List of annotation dictionaries
        exclude_names: List of species names to exclude
        exclude_ids: List of taxonomy IDs to exclude
        logger: Logger instance

    Returns:
        Tuple of (filtered_annotations, excluded_annotations)
    """
    initial_count = len(annotations)

    if logger:
        logger.info(f"Starting species exclusion: Initial count = {initial_count}")
        logger.info(f"Exclude by name: {len(exclude_names)} species")
        logger.info(f"Exclude by ID: {len(exclude_ids)} taxonomy IDs")

    filtered = []
    excluded = []

    # Exclude by name
    excluded_by_name = 0
    for ann in annotations:
        if ann.get("species_name") in exclude_names:
            excluded.append(ann)
            excluded_by_name += 1
        else:
            filtered.append(ann)

    if logger:
        logger.info(f"Excluded {excluded_by_name} entries by species name")

    # Exclude by ID from filtered list
    excluded_by_id = 0
    temp_filtered = []
    for ann in filtered:
        if ann.get("species_id") in exclude_ids:
            excluded.append(ann)
            excluded_by_id += 1
        else:
            temp_filtered.append(ann)

    filtered = temp_filtered

    if logger:
        logger.info(f"Excluded {excluded_by_id} entries by species ID")

    # Remove rows with empty species_name AND species_id
    excluded_by_empty = 0
    final_filtered = []
    for ann in filtered:
        species_name = ann.get("species_name")
        species_id = ann.get("species_id")
        # Remove if both are None or empty string
        if not species_name and not species_id:
            excluded.append(ann)
            excluded_by_empty += 1
        else:
            final_filtered.append(ann)

    if logger:
        logger.info(
            f"Excluded {excluded_by_empty} entries with empty species_name and species_id"
        )
        logger.info(
            f"Total entries: {initial_count} -> {len(final_filtered)} (removed {len(excluded)} entries)"
        )

    return final_filtered, excluded


# ==================== FILE I/O ====================
def save_to_csv(
    data: List[Dict[str, Any]], filepath: str, logger: Optional[logging.Logger] = None
) -> None:
    """
    Save list of dictionaries to CSV.

    Args:
        data: List of dictionaries to save
        filepath: Output CSV file path
        logger: Logger instance
    """
    if not data:
        if logger:
            logger.warning(f"No data to save to {filepath}")
        return

    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

    if logger:
        logger.info(f"Saved {len(data)} records to {filepath}")


def save_failed_chunks(
    failed_chunks: List[List[str]],
    filepath: str,
    logger: Optional[logging.Logger] = None,
) -> None:
    """
    Save failed chunks to text file.

    Args:
        failed_chunks: List of failed PMID chunks
        filepath: Output text file path
        logger: Logger instance
    """
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"Total failed chunks: {len(failed_chunks)}\n")
        f.write(f"Total failed PMIDs: {sum(len(chunk) for chunk in failed_chunks)}\n\n")
        for i, chunk in enumerate(failed_chunks, 1):
            f.write(f"Failed chunk {i} ({len(chunk)} PMIDs):\n")
            f.write(",".join(chunk) + "\n\n")

    if logger:
        logger.warning(f"Failed chunks saved to: {filepath}")


# ==================== MAIN WORKFLOW ====================
def run_workflow(
    config: WorkflowConfig, project_root: str, logger: logging.Logger
) -> str:
    """
    Run the complete workflow.

    Args:
        config: Workflow configuration
        project_root: Root directory of the project
        logger: Logger instance

    Returns:
        Path to final output CSV file
    """
    logger.info("=" * 60)
    logger.info("Starting wf_pre_agent workflow")
    logger.info(f"Date range: {config.date_start} to {config.date_end}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    period = f"{config.date_start}_{config.date_end}"

    # Create output directory
    output_dir = os.path.join(project_root, config.output_dir)
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Output directory: {output_dir}")

    # ==================== STEP 1: FETCH PUBMED IDS ====================
    logger.info("=== Step 1: Fetching PubMed IDs ===")
    pmids, failed_ranges = fetch_pubmed_ids_chunked(
        config.date_start,
        config.date_end,
        days_per_chunk=config.days_per_chunk_step1,
        logger=logger,
    )

    # Retry failed date ranges
    for retry in range(config.max_retries):
        if not failed_ranges:
            break
        logger.info(
            f"Retrying {len(failed_ranges)} failed date ranges (attempt {retry + 1}/{config.max_retries})"
        )
        time.sleep(config.retry_delay)
        retry_pmids, failed_ranges = retry_failed_date_ranges(
            failed_ranges, config.days_per_chunk_step1, logger
        )
        pmids.extend(retry_pmids)
        pmids = list(set(pmids))  # Deduplicate

    # Save PMIDs
    pmid_path = os.path.join(output_dir, f"{timestamp}_{period}.txt")
    with open(pmid_path, "w", encoding="utf-8") as f:
        f.write("\n".join(pmids))
    logger.info(f"PMIDs saved to: {pmid_path}")

    # ==================== STEP 2: FETCH PUBTATOR ANNOTATIONS ====================
    logger.info("=== Step 2: Fetching PubTator annotations ===")
    annotations, failed_chunks = fetch_pubtator_annotations(
        pmids, chunk_size=config.chunk_size_step2, logger=logger
    )

    # Retry failed chunks
    for retry in range(config.max_retries):
        if not failed_chunks:
            break
        logger.info(
            f"Retrying {len(failed_chunks)} failed PubTator chunks (attempt {retry + 1}/{config.max_retries})"
        )
        time.sleep(config.retry_delay)
        retry_pmids = [pmid for chunk in failed_chunks for pmid in chunk]
        retry_annotations, failed_chunks = fetch_pubtator_annotations(
            retry_pmids, chunk_size=config.chunk_size_step2, logger=logger
        )
        annotations.extend(retry_annotations)

    # Save PubTator annotations (Step 2 output)
    pubtator_only_path = os.path.join(
        output_dir, f"step2_pubtator_{timestamp}_{period}.csv"
    )
    save_to_csv(annotations, pubtator_only_path, logger)

    # Save failed PubTator chunks if any
    if failed_chunks:
        failed_pubtator_path = os.path.join(
            output_dir, f"step2_failed_chunks_{timestamp}_{period}.txt"
        )
        save_failed_chunks(failed_chunks, failed_pubtator_path, logger)

    # ==================== STEP 3: FETCH PUBMED METADATA ====================
    logger.info("=== Step 3: Fetching PubMed metadata ===")
    metadata, failed_chunks = fetch_pubmed_metadata(
        [a["pmid"] for a in annotations],
        chunk_size=config.chunk_size_step3,
        logger=logger,
    )

    # Retry failed chunks
    for retry in range(config.max_retries):
        if not failed_chunks:
            break
        logger.info(
            f"Retrying {len(failed_chunks)} failed metadata chunks (attempt {retry + 1}/{config.max_retries})"
        )
        time.sleep(config.retry_delay)
        retry_pmids = [pmid for chunk in failed_chunks for pmid in chunk]
        retry_metadata, failed_chunks = fetch_pubmed_metadata(
            retry_pmids, chunk_size=config.chunk_size_step3, logger=logger
        )
        metadata.update(retry_metadata)

    # Merge metadata
    for ann in annotations:
        pmid = ann["pmid"]
        if pmid in metadata:
            ann["title"] = metadata[pmid]["title"]
            ann["abstract"] = metadata[pmid]["abstract"]
            ann["mesh"] = metadata[pmid]["mesh"]
        else:
            ann["title"] = None
            ann["abstract"] = None
            ann["mesh"] = None

    # Save full annotations with metadata (Step 3 output)
    step3_path = os.path.join(
        output_dir, f"step3_with_metadata_{timestamp}_{period}.csv"
    )
    save_to_csv(annotations, step3_path, logger)

    # Save failed metadata chunks if any
    if failed_chunks:
        failed_metadata_path = os.path.join(
            output_dir, f"step3_failed_chunks_{timestamp}_{period}.txt"
        )
        save_failed_chunks(failed_chunks, failed_metadata_path, logger)

    # ==================== STEP 4: EXCLUDE MODEL ORGANISMS ====================
    logger.info("=== Step 4: Excluding model organisms and empty species ===")
    config_path = os.path.join(project_root, config.model_species_config)
    exclude_names, exclude_ids = load_model_species_config(config_path)
    filtered, excluded = exclude_model_organisms(
        annotations, exclude_names, exclude_ids, logger
    )

    # Save excluded results (model organisms + empty species)
    excluded_path = os.path.join(output_dir, f"step4_excluded_{timestamp}_{period}.csv")
    save_to_csv(excluded, excluded_path, logger)

    # Save final filtered results
    final_path = os.path.join(output_dir, f"FINAL_{timestamp}_{period}.csv")
    save_to_csv(filtered, final_path, logger)

    logger.info("Workflow completed successfully")
    logger.info("=" * 60)

    return final_path


def main() -> str:
    """
    Main entry point for the workflow.

    Returns:
        Path to final output CSV file
    """
    # Configuration
    config = WorkflowConfig(
        date_start="20241201",
        date_end="20241203",
        days_per_chunk_step1=1,
        chunk_size_step2=900,
        chunk_size_step3=400,
        max_retries=3,
        retry_delay=10,
        model_species_config="config/top20_organisms_with_taxid.csv",
        output_dir="data/pre_agent",
    )

    # Setup
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    logger = setup_logging(project_root)

    # Run workflow
    return run_workflow(config, project_root, logger)


def test_step4_only(input_csv_path: str) -> str:
    """
    Test Step 4 only using existing CSV file.

    Args:
        input_csv_path: Path to input CSV file with annotations

    Returns:
        Path to final filtered CSV file
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    # Setup logging
    logger = setup_logging(project_root)
    logger.info("=" * 60)
    logger.info("Testing Step 4 only")
    logger.info(f"Input file: {input_csv_path}")

    # Read input CSV
    annotations = []
    with open(input_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            annotations.append(row)

    logger.info(f"Loaded {len(annotations)} records from input CSV")

    # Step 4: Exclude model organisms
    logger.info("=== Step 4: Excluding model organisms and empty species ===")
    model_species_config = "config/top20_organisms_with_taxid.csv"
    config_path = os.path.join(project_root, model_species_config)

    exclude_names, exclude_ids = load_model_species_config(config_path)
    filtered, excluded = exclude_model_organisms(
        annotations, exclude_names, exclude_ids, logger
    )

    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(project_root, "data/pre_agent")
    os.makedirs(output_dir, exist_ok=True)

    # Save results
    excluded_path = os.path.join(output_dir, f"test_step4_excluded_{timestamp}.csv")
    save_to_csv(excluded, excluded_path, logger)

    final_path = os.path.join(output_dir, f"test_step4_FINAL_{timestamp}.csv")
    save_to_csv(filtered, final_path, logger)

    logger.info("Step 4 test completed successfully")
    logger.info("=" * 60)

    return final_path


if __name__ == "__main__":
    import sys

    # Check if testing Step 4 only
    if len(sys.argv) > 1 and sys.argv[1] == "--test-step4":
        if len(sys.argv) < 3:
            print("Usage: python wf_pre_agent.py --test-step4 <input_csv_path>")
            sys.exit(1)
        test_step4_only(sys.argv[2])
    else:
        main()
