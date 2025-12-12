#!/usr/bin/env python3
"""
Calculate Precision for PubTator results.

This script:
1. Filters curated_data.jsonl based on criteria
2. Calculates precision for filtered_pmids_20251113_092548.txt (55 PMIDs)
"""

import csv
import json
from pathlib import Path
from typing import Dict, Set


def load_top20_organisms(csv_path: str) -> tuple[set[str], set[str]]:
    """Load top 20 organisms data from CSV."""
    species_names = set()
    taxonomy_ids = set()

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            species_names.add(row["species_name"].strip())
            taxonomy_ids.add(row["NCBI_taxonomy_id"].strip())

    return species_names, taxonomy_ids


def has_gene_info(species_gene_list: list[dict]) -> bool:
    """Check if any entry has gene_name or gene_id."""
    for entry in species_gene_list:
        gene_name = entry.get("gene_name", "").strip()
        gene_id = entry.get("gene_id", "").strip()
        if gene_name or gene_id:
            return True
    return False


def contains_top20_organism(
    species_gene_list: list[dict], top20_species: set[str], top20_taxids: set[str]
) -> bool:
    """Check if any entry contains top 20 organisms."""
    for entry in species_gene_list:
        species_name = entry.get("species_name", "").strip()
        species_id = entry.get("species_id", "").strip()

        if species_name in top20_species or species_id in top20_taxids:
            return True

    return False


def filter_jsonl(
    input_path: str, output_path: str, top20_csv_path: str
) -> tuple[Dict[str, int], Set[str]]:
    """Filter JSONL file and return statistics and correct PMIDs."""

    # Load top 20 organisms
    top20_species, top20_taxids = load_top20_organisms(top20_csv_path)

    stats = {"total": 0, "removed_no_gene": 0, "removed_top20": 0, "kept": 0}

    kept_lines = []
    correct_pmids = set()

    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            stats["total"] += 1

            try:
                data = json.loads(line)
                pmid = data.get("PMID", "")
                species_gene_list = data.get("species_gene_list", [])

                # Skip if no gene info
                if not has_gene_info(species_gene_list):
                    stats["removed_no_gene"] += 1
                    continue

                # Skip if contains top 20 organisms
                if contains_top20_organism(
                    species_gene_list, top20_species, top20_taxids
                ):
                    stats["removed_top20"] += 1
                    continue

                # Keep this line
                kept_lines.append(line)
                correct_pmids.add(pmid)
                stats["kept"] += 1

            except json.JSONDecodeError as e:
                print(f"Warning: Failed to parse line: {e}")
                continue

    # Write filtered data
    with open(output_path, "w", encoding="utf-8") as f:
        for line in kept_lines:
            f.write(line + "\n")

    return stats, correct_pmids


def load_pmids_from_txt(txt_path: str) -> Set[str]:
    """Load PMIDs from a text file (one PMID per line)."""
    pmids = set()

    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f:
            pmid = line.strip()
            if pmid:
                pmids.add(pmid)

    return pmids


def calculate_precision(
    result_pmids: Set[str], correct_pmids: Set[str]
) -> Dict[str, any]:
    """Calculate precision metrics."""

    total = len(result_pmids)
    correct_set = result_pmids & correct_pmids
    false_positive_set = result_pmids - correct_pmids
    correct = len(correct_set)
    incorrect = total - correct

    precision = (correct / total * 100) if total > 0 else 0.0

    return {
        "total": total,
        "correct": correct,
        "incorrect": incorrect,
        "precision": precision,
        "false_positives": sorted(false_positive_set),
    }


def main():
    # Define paths
    base_dir = Path(__file__).parent.parent
    input_jsonl = base_dir / "results" / "curated_data" / "curated_data_20251212.jsonl"
    output_jsonl = (
        base_dir / "results" / "curated_data" / "filtered_data_pubtator.jsonl"
    )
    top20_csv = base_dir / "config" / "top20_organisms_with_taxid.csv"

    pubtator_txt = (
        base_dir
        / "results"
        / "pubtator_filtered"
        / "filtered_pmids_20251212_145202.txt"
    )

    print("=" * 70)
    print("STEP 1: Filtering curated data")
    print("=" * 70)
    print(f"Input: {input_jsonl}")
    print(f"Output: {output_jsonl}")
    print(f"Top20 CSV: {top20_csv}")
    print()

    # Run filtering
    stats, correct_pmids = filter_jsonl(
        str(input_jsonl), str(output_jsonl), str(top20_csv)
    )

    # Print filtering statistics
    print("Filtering Results:")
    print(f"  Total lines processed: {stats['total']}")
    print(f"  Removed (no gene info): {stats['removed_no_gene']}")
    print(f"  Removed (top 20 organisms): {stats['removed_top20']}")
    print(f"  Kept (correct PMIDs): {stats['kept']}")
    print()

    # Load PMIDs from PubTator result file
    print("=" * 70)
    print("STEP 2: Loading PMIDs from PubTator result file")
    print("=" * 70)

    pubtator_pmids = load_pmids_from_txt(str(pubtator_txt))

    # print(f"PubTator PMIDs loaded: {len(pubtator_pmids)}")
    print()

    # Calculate precision
    print("=" * 70)
    print("STEP 3: Calculating Precision")
    print("=" * 70)
    print()

    pubtator_metrics = calculate_precision(pubtator_pmids, correct_pmids)

    # Print results
    print("【PubTator Results】")
    print(f"  Total PMIDs: {pubtator_metrics['total']}")
    print(f"  Correct: {pubtator_metrics['correct']}")
    print(f"  Incorrect: {pubtator_metrics['incorrect']}")
    print(f"  Precision: {pubtator_metrics['precision']:.2f}%")
    print()

    # Print False Positives
    print("=" * 70)
    print("False Positives (PMIDs in results but not correct)")
    print("=" * 70)
    print()

    print("【PubTator False Positives】")
    if pubtator_metrics["false_positives"]:
        print(f"  Count: {len(pubtator_metrics['false_positives'])}")
        # print(f"  PMIDs: {', '.join(pubtator_metrics['false_positives'])}")
    else:
        print("  None")
    print()

    # Save False Positives to file
    fp_dir = base_dir / "results" / "curated_data"
    pubtator_fp_file = fp_dir / "false_positives_pubtator.txt"

    with open(pubtator_fp_file, "w", encoding="utf-8") as f:
        f.write("False Positives - PubTator\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Count: {len(pubtator_metrics['false_positives'])}\n\n")
        f.write("PMIDs:\n")
        for pmid in pubtator_metrics["false_positives"]:
            f.write(f"{pmid}\n")

    print("=" * 70)
    print(f"Filtered data saved to: {output_jsonl}")
    print(f"PubTator FP saved to: {pubtator_fp_file}")
    print("=" * 70)


if __name__ == "__main__":
    main()
