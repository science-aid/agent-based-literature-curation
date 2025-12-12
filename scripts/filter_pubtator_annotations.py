"""
Script to fetch all species and gene annotations from PubTator for PMIDs from FINAL CSV,
then filter out model organisms and papers without species/gene annotations.

Input:
- CSV file (FINAL_*.csv) with PMIDs in first column
- CSV file with model organisms to exclude

Output:
- JSON file with all annotations before filtering
- JSON file with filtered annotations (no model organisms, has species and genes)
- Summary statistics
"""

import csv
import json
import logging
import os
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

import requests

# ==================== CONSTANTS ====================
API_SLEEP_DELAY = 1.0  # seconds between API calls
DEFAULT_TIMEOUT = 60  # seconds for API requests


# ==================== CONFIGURATION ====================
@dataclass
class PubTatorConfig:
    """Configuration for PubTator processing."""

    input_csv: str  # Path to FINAL_*.csv file
    model_organisms_config: str = "config/top20_organisms_with_taxid.csv"
    chunk_size: int = 900  # PMIDs per request for PubTator
    max_retries: int = 3  # Maximum retry attempts for failed chunks
    retry_delay: int = 10  # Seconds to wait between retries
    output_dir: str = "results/pubtator_filtered"


# ==================== LOGGING ====================
def setup_logging(project_root: str) -> logging.Logger:
    """Setup logging configuration."""
    log_dir = os.path.join(project_root, "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "pubtator2.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file, mode="a"), logging.StreamHandler()],
    )
    return logging.getLogger(__name__)


# ==================== INPUT LOADING ====================
def load_pmids_from_csv(
    csv_path: str, logger: Optional[logging.Logger] = None
) -> List[str]:
    """
    Load PMIDs from first column of CSV file.

    Args:
        csv_path: Path to CSV file with PMIDs in first column
        logger: Logger instance

    Returns:
        List of PMIDs (strings)
    """
    pmids = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Get first column value (pmid)
            pmid = row.get("pmid", "").strip()
            if pmid:
                pmids.append(pmid)

    if logger:
        logger.info(f"Loaded {len(pmids)} PMIDs from {csv_path}")

    return pmids


def load_model_organisms(
    config_path: str, logger: Optional[logging.Logger] = None
) -> Tuple[Set[str], Set[str]]:
    """
    Load model organism names and taxonomy IDs from CSV file.

    Args:
        config_path: Path to CSV file with 'species_name' and 'NCBI_taxonomy_id' columns
        logger: Logger instance

    Returns:
        Tuple of (species_names, taxonomy_ids) as sets
    """
    exclude_names = set()
    exclude_ids = set()

    with open(config_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            species_name = row["species_name"].strip()
            taxonomy_id = row["NCBI_taxonomy_id"].strip()
            if species_name:
                exclude_names.add(species_name)
            if taxonomy_id:
                exclude_ids.add(taxonomy_id)

    if logger:
        logger.info(
            f"Loaded {len(exclude_names)} model organism names and {len(exclude_ids)} taxonomy IDs"
        )

    return exclude_names, exclude_ids


# ==================== PUBTATOR FETCHING ====================
def fetch_all_pubtator_annotations(
    pmids: List[str], chunk_size: int = 1000, logger: Optional[logging.Logger] = None
) -> Tuple[Dict[str, Dict], List[List[str]]]:
    """
    Fetch ALL species and gene annotations from PubTator for given PMIDs.

    Args:
        pmids: List of PubMed IDs
        chunk_size: Number of PMIDs per request
        logger: Logger instance

    Returns:
        Tuple of (annotations_dict, failed_chunks)
        annotations_dict: {pmid: {"species": [...], "genes": [...]}}
    """
    base_url = "https://www.ncbi.nlm.nih.gov/research/pubtator3-api/publications/export/biocxml"
    annotations = {}
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
                if not pmid:
                    continue

                annots = doc.findall(".//passage/annotation")
                species_list = []
                gene_list = []

                species_seen = set()
                gene_seen = set()

                for a in annots:
                    ann_type = a.find("infon[@key='type']")
                    if ann_type is None:
                        continue

                    text_elem = a.find("text")
                    id_elem = a.find("infon[@key='identifier']")
                    text = text_elem.text if text_elem is not None else None
                    identifier = id_elem.text if id_elem is not None else None

                    if ann_type.text == "Species" and text:
                        # Use (name, id) tuple as unique key
                        key = (text, identifier)
                        if key not in species_seen:
                            species_seen.add(key)
                            species_list.append({"name": text, "id": identifier})
                    elif ann_type.text == "Gene" and text:
                        # Use (name, id) tuple as unique key
                        key = (text, identifier)
                        if key not in gene_seen:
                            gene_seen.add(key)
                            gene_list.append({"name": text, "id": identifier})

                # Store all annotations for this PMID
                annotations[pmid] = {"species": species_list, "genes": gene_list}

            if logger:
                logger.info(
                    f"PubTator chunk {i // chunk_size + 1}/{(len(pmids) - 1) // chunk_size + 1}: {len(chunk)} PMIDs processed"
                )

            time.sleep(API_SLEEP_DELAY)

        except Exception as e:
            if logger:
                logger.error(
                    f"Error fetching PubTator chunk {i // chunk_size + 1}: {e}"
                )
            failed_chunks.append(chunk)

    if logger:
        logger.info(
            f"Total PMIDs with annotations: {len(annotations)}, failed chunks: {len(failed_chunks)}"
        )

    return annotations, failed_chunks


# ==================== FILTERING ====================
def filter_annotations(
    annotations: Dict[str, Dict],
    exclude_names: Set[str],
    exclude_ids: Set[str],
    logger: Optional[logging.Logger] = None,
) -> Tuple[Dict, Dict, Dict, Dict]:
    """
    Filter annotations to:
    1. Remove PMIDs that contain any model organism (by name or ID)
    2. Keep only PMIDs that have at least one species annotation
    3. Keep only PMIDs that have at least one gene annotation

    Args:
        annotations: Dictionary of PMID annotations
        exclude_names: Set of model organism names to exclude
        exclude_ids: Set of taxonomy IDs to exclude
        logger: Logger instance

    Returns:
        Tuple of (filtered, excluded_by_model_organism, excluded_by_no_species, excluded_by_no_genes)
    """
    if logger:
        logger.info("=== Filtering annotations ===")
        logger.info(f"Initial PMIDs: {len(annotations)}")

    # Step 1: Remove PMIDs with model organisms
    no_model_organisms = {}
    excluded_by_model_organism = {}

    for pmid, data in annotations.items():
        has_model_organism = False

        for species in data["species"]:
            species_name = species.get("name")
            species_id = species.get("id")

            if species_name in exclude_names or species_id in exclude_ids:
                has_model_organism = True
                break

        if has_model_organism:
            excluded_by_model_organism[pmid] = data
        else:
            no_model_organisms[pmid] = data

    if logger:
        logger.info(
            f"After excluding model organisms: {len(no_model_organisms)} PMIDs remaining"
        )
        logger.info(
            f"Excluded by model organism: {len(excluded_by_model_organism)} PMIDs"
        )

    # Step 2: Keep only PMIDs with at least one species annotation
    with_species = {}
    excluded_by_no_species = {}

    for pmid, data in no_model_organisms.items():
        if len(data["species"]) > 0:
            with_species[pmid] = data
        else:
            excluded_by_no_species[pmid] = data

    if logger:
        logger.info(
            f"After requiring species annotations: {len(with_species)} PMIDs remaining"
        )
        logger.info(f"Excluded by no species: {len(excluded_by_no_species)} PMIDs")

    # Step 3: Keep only PMIDs with gene annotations
    filtered = {}
    excluded_by_no_genes = {}

    for pmid, data in with_species.items():
        if len(data["genes"]) > 0:
            filtered[pmid] = data
        else:
            excluded_by_no_genes[pmid] = data

    if logger:
        logger.info(
            f"After requiring gene annotations: {len(filtered)} PMIDs remaining"
        )
        logger.info(f"Excluded by no genes: {len(excluded_by_no_genes)} PMIDs")
        logger.info(
            f"Total excluded: {len(excluded_by_model_organism) + len(excluded_by_no_species) + len(excluded_by_no_genes)} PMIDs"
        )

    return (
        filtered,
        excluded_by_model_organism,
        excluded_by_no_species,
        excluded_by_no_genes,
    )


# ==================== STATISTICS ====================
def create_summary_stats(
    annotations: Dict[str, Dict], logger: Optional[logging.Logger] = None
) -> Dict:
    """Create summary statistics of the annotations."""
    stats = {
        "total_pmids": len(annotations),
        "pmids_with_species": 0,
        "pmids_with_genes": 0,
        "pmids_with_both": 0,
        "total_species_annotations": 0,
        "total_gene_annotations": 0,
        "avg_species_per_pmid": 0,
        "avg_genes_per_pmid": 0,
        "unique_species": set(),
        "unique_genes": set(),
    }

    total_species_count = 0
    total_gene_count = 0

    for pmid, data in annotations.items():
        has_species = len(data["species"]) > 0
        has_genes = len(data["genes"]) > 0

        if has_species:
            stats["pmids_with_species"] += 1
            stats["total_species_annotations"] += len(data["species"])
            total_species_count += len(data["species"])
            for species in data["species"]:
                if species["name"]:
                    stats["unique_species"].add(species["name"])

        if has_genes:
            stats["pmids_with_genes"] += 1
            stats["total_gene_annotations"] += len(data["genes"])
            total_gene_count += len(data["genes"])
            for gene in data["genes"]:
                if gene["name"]:
                    stats["unique_genes"].add(gene["name"])

        if has_species and has_genes:
            stats["pmids_with_both"] += 1

    # Calculate averages
    if stats["total_pmids"] > 0:
        stats["avg_species_per_pmid"] = round(
            total_species_count / stats["total_pmids"], 2
        )
        stats["avg_genes_per_pmid"] = round(total_gene_count / stats["total_pmids"], 2)

    # Convert sets to lists for JSON serialization
    stats["unique_species"] = sorted(list(stats["unique_species"]))
    stats["unique_genes"] = sorted(list(stats["unique_genes"]))
    stats["unique_species_count"] = len(stats["unique_species"])
    stats["unique_genes_count"] = len(stats["unique_genes"])

    if logger:
        logger.info("=== Summary Statistics ===")
        logger.info(f"Total PMIDs: {stats['total_pmids']}")
        logger.info(f"PMIDs with species: {stats['pmids_with_species']}")
        logger.info(f"PMIDs with genes: {stats['pmids_with_genes']}")
        logger.info(f"PMIDs with both: {stats['pmids_with_both']}")
        logger.info(f"Total species annotations: {stats['total_species_annotations']}")
        logger.info(f"Total gene annotations: {stats['total_gene_annotations']}")
        logger.info(f"Avg species per PMID: {stats['avg_species_per_pmid']}")
        logger.info(f"Avg genes per PMID: {stats['avg_genes_per_pmid']}")
        logger.info(f"Unique species: {stats['unique_species_count']}")
        logger.info(f"Unique genes: {stats['unique_genes_count']}")

    return stats


# ==================== FILE I/O ====================
def save_to_json(
    data: Dict, filepath: str, logger: Optional[logging.Logger] = None
) -> None:
    """Save dictionary to JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    if logger:
        logger.info(f"Saved annotations for {len(data)} PMIDs to {filepath}")


def save_failed_chunks(
    failed_chunks: List[List[str]],
    filepath: str,
    logger: Optional[logging.Logger] = None,
) -> None:
    """Save failed chunks to text file."""
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
    config: PubTatorConfig, project_root: str, logger: logging.Logger
) -> str:
    """
    Run the complete PubTator filtering workflow.

    Args:
        config: PubTator configuration
        project_root: Root directory of the project
        logger: Logger instance

    Returns:
        Path to filtered annotations JSON file
    """
    logger.info("=" * 60)
    logger.info("Starting PubTator annotation extraction and filtering")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Load PMIDs from CSV file
    csv_path = os.path.join(project_root, config.input_csv)
    pmids = load_pmids_from_csv(csv_path, logger)

    if not pmids:
        logger.error("No PMIDs found in input CSV file")
        return ""

    # Load model organisms to exclude
    model_config_path = os.path.join(project_root, config.model_organisms_config)
    exclude_names, exclude_ids = load_model_organisms(model_config_path, logger)

    # Fetch annotations from PubTator with retry
    logger.info("=== Fetching PubTator annotations ===")
    annotations, failed_chunks = fetch_all_pubtator_annotations(
        pmids, chunk_size=config.chunk_size, logger=logger
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
        retry_annotations, failed_chunks = fetch_all_pubtator_annotations(
            retry_pmids, chunk_size=config.chunk_size, logger=logger
        )
        annotations.update(retry_annotations)

    # Create output directory
    output_dir = os.path.join(project_root, config.output_dir)
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Output directory: {output_dir}")

    # Save all annotations before filtering
    all_annotations_path = os.path.join(output_dir, f"all_annotations_{timestamp}.json")
    save_to_json(annotations, all_annotations_path, logger)

    # Create and save statistics for all annotations
    all_stats = create_summary_stats(annotations, logger)
    all_stats_path = os.path.join(output_dir, f"all_stats_{timestamp}.json")
    save_to_json(all_stats, all_stats_path, logger)

    # Filter annotations
    (
        filtered,
        excluded_by_model_organism,
        excluded_by_no_species,
        excluded_by_no_genes,
    ) = filter_annotations(annotations, exclude_names, exclude_ids, logger)

    # Save filtered annotations
    filtered_path = os.path.join(output_dir, f"filtered_annotations_{timestamp}.json")
    save_to_json(filtered, filtered_path, logger)

    # Create and save statistics for filtered annotations
    filtered_stats = create_summary_stats(filtered, logger)
    filtered_stats_path = os.path.join(output_dir, f"filtered_stats_{timestamp}.json")
    save_to_json(filtered_stats, filtered_stats_path, logger)

    # Save excluded annotations
    excluded_by_model_organism_path = os.path.join(
        output_dir, f"excluded_by_model_organism_{timestamp}.json"
    )
    save_to_json(excluded_by_model_organism, excluded_by_model_organism_path, logger)

    excluded_by_no_species_path = os.path.join(
        output_dir, f"excluded_by_no_species_{timestamp}.json"
    )
    save_to_json(excluded_by_no_species, excluded_by_no_species_path, logger)

    excluded_by_no_genes_path = os.path.join(
        output_dir, f"excluded_by_no_genes_{timestamp}.json"
    )
    save_to_json(excluded_by_no_genes, excluded_by_no_genes_path, logger)

    # Save list of filtered PMIDs
    filtered_pmids_path = os.path.join(output_dir, f"filtered_pmids_{timestamp}.txt")
    with open(filtered_pmids_path, "w", encoding="utf-8") as f:
        for pmid in sorted(filtered.keys()):
            f.write(f"{pmid}\n")
    logger.info(f"Saved {len(filtered)} filtered PMIDs to {filtered_pmids_path}")

    # Save failed chunks if any
    if failed_chunks:
        failed_path = os.path.join(output_dir, f"failed_chunks_{timestamp}.txt")
        save_failed_chunks(failed_chunks, failed_path, logger)

    # Create summary report
    summary_report = {
        "input_file": config.input_csv,
        "total_input_pmids": len(pmids),
        "pmids_with_annotations": len(annotations),
        "pmids_excluded_by_model_organism": len(excluded_by_model_organism),
        "pmids_excluded_by_no_species": len(excluded_by_no_species),
        "pmids_excluded_by_no_genes": len(excluded_by_no_genes),
        "final_filtered_pmids": len(filtered),
        "timestamp": timestamp,
    }

    summary_path = os.path.join(output_dir, f"summary_report_{timestamp}.json")
    save_to_json(summary_report, summary_path, logger)

    logger.info("=" * 60)
    logger.info("FINAL SUMMARY")
    logger.info(f"Input PMIDs: {summary_report['total_input_pmids']}")
    logger.info(f"PMIDs with annotations: {summary_report['pmids_with_annotations']}")
    logger.info(
        f"Excluded by model organisms: {summary_report['pmids_excluded_by_model_organism']}"
    )
    logger.info(
        f"Excluded by no species: {summary_report['pmids_excluded_by_no_species']}"
    )
    logger.info(f"Excluded by no genes: {summary_report['pmids_excluded_by_no_genes']}")
    logger.info(f"Final filtered PMIDs: {summary_report['final_filtered_pmids']}")
    logger.info("=" * 60)
    logger.info("Processing completed successfully")
    logger.info("=" * 60)

    return filtered_path


def main() -> str:
    """
    Main entry point for the workflow.

    Returns:
        Path to filtered annotations JSON file
    """
    # Configuration
    config = PubTatorConfig(
        input_csv="results/wf_pre_agent/FINAL_20251117_172057_20241201_20241203.csv",
        model_organisms_config="config/top20_organisms_with_taxid.csv",
        chunk_size=900,
        max_retries=3,
        retry_delay=10,
        output_dir="results/pubtator_filtered",
    )

    # Setup
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    logger = setup_logging(project_root)

    # Run workflow
    return run_workflow(config, project_root, logger)


if __name__ == "__main__":
    main()
