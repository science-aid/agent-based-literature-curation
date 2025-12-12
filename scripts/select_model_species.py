"""
Select top 20 most frequent organisms from metadata and retrieve their NCBI Taxonomy information.

This script:
1. Reads organism metadata from CSV
2. Counts and ranks all organisms by paper count
3. Queries NCBI Taxonomy API for taxonomy IDs, scientific names, and common names
4. Exports results to CSV
5. Creates bar chart visualization showing coverage of top 20 species
"""
import csv
import logging
import os
import time
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

import matplotlib.pyplot as plt
import requests


# ==================== CONSTANTS ====================
API_SLEEP_DELAY = 0.4  # seconds between NCBI API calls
DEFAULT_TIMEOUT = 10  # seconds for API requests
TOP_N_SPECIES = 20  # Number of top species to select


# ==================== CONFIGURATION ====================
@dataclass
class ModelSpeciesConfig:
    """Configuration for model species selection."""
    input_csv: str = "data/20251008_ge_metadata_all.csv"
    output_csv: str = "config/top20_organisms_with_taxid.csv"
    output_all_ranked: str = "config/all_ranked_organisms.csv"
    figures_dir: str = "figures/model_species"
    top_n: int = TOP_N_SPECIES


# ==================== LOGGING ====================
def setup_logging(project_root: str) -> logging.Logger:
    """Setup logging configuration."""
    log_dir = os.path.join(project_root, "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "select_model_species.log")

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, mode='a'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


# ==================== DATA LOADING ====================
def read_metadata_and_count_organisms(
    csv_path: str,
    logger: Optional[logging.Logger] = None
) -> Counter:
    """
    Read CSV and count organism_name occurrences.

    Args:
        csv_path: Path to metadata CSV file
        logger: Logger instance

    Returns:
        Counter object with organism counts
    """
    if logger:
        logger.info(f"Reading metadata from: {csv_path}")

    organism_counts = Counter()

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            organism_name = row.get('organism_name', '').strip()
            if organism_name and organism_name != 'NotFound':
                organism_counts[organism_name] += 1

    if logger:
        logger.info(f"Found {len(organism_counts)} unique organisms")

    return organism_counts


def get_top_organisms(
    organism_counts: Counter,
    top_n: int = 20,
    logger: Optional[logging.Logger] = None
) -> List[Tuple[str, int]]:
    """
    Get top N most frequent organisms.

    Args:
        organism_counts: Counter object with organism counts
        top_n: Number of top organisms to retrieve
        logger: Logger instance

    Returns:
        List of (organism_name, count) tuples
    """
    top_organisms = organism_counts.most_common(top_n)

    if logger:
        logger.info(f"Top {top_n} organisms:")
        for i, (name, count) in enumerate(top_organisms, 1):
            logger.info(f"  {i}. {name}: {count} occurrences")

    return top_organisms


# ==================== NCBI TAXONOMY QUERIES ====================
def fetch_taxonomy_info(
    organism_name: str,
    logger: Optional[logging.Logger] = None
) -> Dict[str, Optional[str]]:
    """
    Fetch NCBI Taxonomy information including ID, scientific name, and common name.

    Args:
        organism_name: Name of the organism to query
        logger: Logger instance

    Returns:
        Dictionary with 'tax_id', 'scientific_name', 'common_name' (None if not found)
    """
    # Step 1: Search for the organism name
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    search_params = {
        "db": "taxonomy",
        "term": organism_name,
        "retmode": "xml"
    }

    try:
        response = requests.get(search_url, params=search_params, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        root = ET.fromstring(response.content)

        # Get the first ID from search results
        id_list = root.findall(".//Id")
        if not id_list:
            if logger:
                logger.warning(f"No taxonomy ID found for: {organism_name}")
            return {"tax_id": None, "scientific_name": None, "common_name": None}

        tax_id = id_list[0].text

        # Step 2: Fetch detailed summary to get scientific name and common name
        summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        summary_params = {
            "db": "taxonomy",
            "id": tax_id,
            "retmode": "xml"
        }

        time.sleep(API_SLEEP_DELAY)  # Rate limiting
        response = requests.get(summary_url, params=summary_params, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        summary_root = ET.fromstring(response.content)

        # Extract scientific name and common name
        scientific_name_elem = summary_root.find(".//Item[@Name='ScientificName']")
        common_name_elem = summary_root.find(".//Item[@Name='CommonName']")

        scientific_name = scientific_name_elem.text if scientific_name_elem is not None else None
        common_name = common_name_elem.text if common_name_elem is not None else None

        if logger:
            logger.info(f"  {organism_name} -> TaxID: {tax_id}")
            logger.info(f"    Scientific: {scientific_name}, Common: {common_name}")

        return {
            "tax_id": tax_id,
            "scientific_name": scientific_name,
            "common_name": common_name
        }

    except Exception as e:
        if logger:
            logger.error(f"Error fetching taxonomy info for {organism_name}: {e}")
        return {"tax_id": None, "scientific_name": None, "common_name": None}


# ==================== FILE I/O ====================
def save_results_to_csv(
    results: List[List],
    output_path: str,
    logger: Optional[logging.Logger] = None
) -> None:
    """
    Save top organisms results to CSV file.

    Args:
        results: List of [species_name, english_name, NCBI_taxonomy_id, rank, count]
        output_path: Path to output CSV file
        logger: Logger instance
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['species_name', 'english_name', 'NCBI_taxonomy_id', 'rank', 'count'])
        writer.writerows(results)

    if logger:
        logger.info(f"Results saved to: {output_path}")


def save_all_ranked_organisms(
    organism_counts: Counter,
    output_path: str,
    logger: Optional[logging.Logger] = None
) -> None:
    """
    Save all ranked organisms with counts to CSV file.

    Args:
        organism_counts: Counter object with organism counts
        output_path: Path to output CSV file
        logger: Logger instance
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Sort by count (descending)
    ranked_organisms = organism_counts.most_common()

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['rank', 'organism_name', 'count'])
        for rank, (organism_name, count) in enumerate(ranked_organisms, 1):
            writer.writerow([rank, organism_name, count])

    if logger:
        logger.info(f"All ranked organisms saved to: {output_path}")
        logger.info(f"Total unique organisms: {len(ranked_organisms)}")


# ==================== VISUALIZATION ====================
def create_bar_chart_and_calculate_coverage(
    organism_counts: Counter,
    top_organisms_with_taxonomy: List[List],
    output_dir: str,
    top_n: int = 20,
    logger: Optional[logging.Logger] = None
) -> float:
    """
    Create bar chart for top N organisms and calculate coverage percentage.

    Args:
        organism_counts: Counter object with organism counts
        top_organisms_with_taxonomy: List of [scientific_name, common_name, tax_id, rank, count]
        output_dir: Directory to save the chart
        top_n: Number of top organisms to display
        logger: Logger instance

    Returns:
        Coverage percentage of top N organisms
    """
    os.makedirs(output_dir, exist_ok=True)

    # Get top N organisms from Counter
    top_organisms = organism_counts.most_common(top_n)
    counts = [count for _, count in top_organisms]

    # Create mapping from original organism names to scientific names
    organism_name_to_scientific = {}
    for row in top_organisms_with_taxonomy:
        scientific_name = row[0]
        rank = row[3]
        count = row[4]
        # Find corresponding organism in top_organisms by rank
        if rank <= len(top_organisms):
            original_name = top_organisms[rank - 1][0]
            organism_name_to_scientific[original_name] = scientific_name

    # Get scientific names for display
    scientific_names = []
    for name, _ in top_organisms:
        scientific_name = organism_name_to_scientific.get(name, name)
        scientific_names.append(scientific_name)

    # Calculate coverage
    total_papers = sum(organism_counts.values())
    top_n_papers = sum(counts)
    coverage_percentage = (top_n_papers / total_papers) * 100

    if logger:
        logger.info(f"Total papers: {total_papers:,}")
        logger.info(f"Top {top_n} papers: {top_n_papers:,}")
        logger.info(f"Coverage: {coverage_percentage:.2f}%")

    # Calculate "Others" count (all organisms beyond top N)
    others_count = total_papers - top_n_papers
    unique_others_count = len(organism_counts) - top_n

    # Create bar chart with more space for labels
    fig, ax = plt.subplots(figsize=(17, 10))

    # Plot top N organisms in blue
    x_positions = list(range(1, top_n + 1))
    bars = ax.bar(x_positions, counts, color='steelblue', edgecolor='black', label=f'Top {top_n}')

    # Plot "Others" bar in red
    others_position = top_n + 1
    others_bar = ax.bar(others_position, others_count, color='lightcoral', edgecolor='black',
                        label=f'Others (rank {top_n + 1}+)')

    ax.set_xlabel('Rank', fontsize=13, fontweight='bold')
    ax.set_ylabel('Count (Number of Papers)', fontsize=13, fontweight='bold')
    ax.set_title(f'Top {top_n} Organisms by Paper Count\n(Top {top_n} Coverage: {coverage_percentage:.2f}%)',
                 fontsize=15, fontweight='bold', pad=20)

    # Set x-axis ticks for top N and Others
    all_x_positions = x_positions + [others_position]
    ax.set_xticks(all_x_positions)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.legend(loc='upper right', fontsize=11)

    # Add count labels on top of bars for top N
    for i, (bar, count) in enumerate(zip(bars, counts), 1):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{count:,}',
                ha='center', va='bottom', fontsize=9, fontweight='bold')

    # Add count label on "Others" bar
    ax.text(others_bar[0].get_x() + others_bar[0].get_width()/2., others_count,
            f'{others_count:,}',
            ha='center', va='bottom', fontsize=9, fontweight='bold')

    # Add scientific names below x-axis with proper spacing
    # Move species names further down to avoid overlap with rank numbers
    max_count = max(max(counts), others_count)
    ax.set_ylim(bottom=-max_count * 0.25)  # Add more space below for labels (increased from 0.15 to 0.25)

    for i, scientific_name in enumerate(scientific_names, 1):
        # Place text below the x-axis
        ax.text(i, -max_count * 0.03, scientific_name,
                ha='right', va='top', fontsize=8,
                rotation=45, style='italic', fontweight='bold')

    # Add "Others" label
    ax.text(others_position, -max_count * 0.03, f'Others\n({unique_others_count} species)',
            ha='center', va='top', fontsize=8, fontweight='bold')

    plt.tight_layout()
    chart_path = os.path.join(output_dir, f'top{top_n}_organisms_bar_chart.png')
    plt.savefig(chart_path, dpi=300, bbox_inches='tight')
    plt.close()

    if logger:
        logger.info(f"Bar chart saved to: {chart_path}")

    # Save coverage statistics as text file using scientific names
    stats_path = os.path.join(output_dir, 'coverage_statistics.txt')
    with open(stats_path, 'w', encoding='utf-8') as f:
        f.write(f"Top {top_n} Organisms Coverage Statistics\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Total papers: {total_papers:,}\n")
        f.write(f"Top {top_n} papers: {top_n_papers:,}\n")
        f.write(f"Coverage: {coverage_percentage:.2f}%\n")
        f.write(f"Remaining papers: {total_papers - top_n_papers:,} ({100 - coverage_percentage:.2f}%)\n\n")
        f.write("Top organisms:\n")
        for i, scientific_name in enumerate(scientific_names, 1):
            count = counts[i - 1]
            percentage = (count / total_papers) * 100
            f.write(f"  {i:2d}. {scientific_name:35s} {count:6,} ({percentage:5.2f}%)\n")

    if logger:
        logger.info(f"Coverage statistics saved to: {stats_path}")

    return coverage_percentage


# ==================== MAIN WORKFLOW ====================
def run_workflow(config: ModelSpeciesConfig, project_root: str, logger: logging.Logger) -> str:
    """
    Run the complete model species selection workflow.

    Args:
        config: Model species configuration
        project_root: Root directory of the project
        logger: Logger instance

    Returns:
        Path to output CSV file
    """
    logger.info("=" * 60)
    logger.info("Starting organism selection and taxonomy ID retrieval")

    # Step 1: Read and count organisms
    input_path = os.path.join(project_root, config.input_csv)
    organism_counts = read_metadata_and_count_organisms(input_path, logger)

    # Step 2: Get top N organisms
    top_organisms = get_top_organisms(organism_counts, top_n=config.top_n, logger=logger)

    # Step 3: Fetch taxonomy information
    logger.info("=" * 60)
    logger.info("Fetching NCBI Taxonomy information...")

    results = []
    for rank, (organism_name, count) in enumerate(top_organisms, 1):
        logger.info(f"[{rank}/{config.top_n}] Querying: {organism_name}")
        tax_info = fetch_taxonomy_info(organism_name, logger)

        scientific_name = tax_info["scientific_name"] if tax_info["scientific_name"] else "NotFound"
        common_name = tax_info["common_name"] if tax_info["common_name"] else "NotFound"
        tax_id = tax_info["tax_id"] if tax_info["tax_id"] else "NotFound"

        results.append([scientific_name, common_name, tax_id, rank, count])
        time.sleep(API_SLEEP_DELAY)  # Rate limiting for NCBI API

    # Step 4: Save results
    logger.info("=" * 60)
    output_csv_path = os.path.join(project_root, config.output_csv)
    save_results_to_csv(results, output_csv_path, logger)

    # Step 5: Save all ranked organisms
    output_all_ranked_path = os.path.join(project_root, config.output_all_ranked)
    save_all_ranked_organisms(organism_counts, output_all_ranked_path, logger)

    # Step 6: Create visualization and calculate coverage
    logger.info("=" * 60)
    logger.info("Creating visualizations...")
    figures_dir = os.path.join(project_root, config.figures_dir)
    coverage = create_bar_chart_and_calculate_coverage(
        organism_counts,
        results,
        figures_dir,
        top_n=config.top_n,
        logger=logger
    )

    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info(f"Total unique organisms: {len(organism_counts)}")
    logger.info(f"Top {config.top_n} organisms cover {coverage:.2f}% of papers")
    logger.info(f"Results saved to: {output_csv_path}")
    logger.info(f"Figures saved to: {figures_dir}")
    logger.info("Completed successfully")
    logger.info("=" * 60)

    return output_csv_path


def main() -> str:
    """
    Main entry point for the workflow.

    Returns:
        Path to output CSV file
    """
    # Configuration
    config = ModelSpeciesConfig(
        input_csv="data/gem/20251008_ge_metadata_all.csv",
        output_csv="config/top20_organisms_with_taxid.csv",
        output_all_ranked="config/all_ranked_organisms.csv",
        figures_dir="figures/model_species",
        top_n=TOP_N_SPECIES
    )

    # Setup
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    logger = setup_logging(project_root)

    # Run workflow
    return run_workflow(config, project_root, logger)


if __name__ == "__main__":
    main()
