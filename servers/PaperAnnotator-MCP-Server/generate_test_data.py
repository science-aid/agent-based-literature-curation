"""
Generate 100 rows of random test data for sample_core.py testing.
Output format matches the flat CSV format from paper_annotator.py.
"""

import pandas as pd
import random
import numpy as np

# Sample data pools
SPECIES_POOL = [
    ("Homo sapiens", "9606", "mammals"),
    ("Mus musculus", "10090", "mammals"),
    ("Rattus norvegicus", "10116", "mammals"),
    ("Danio rerio", "7955", "fishes"),
    ("Notothenia coriiceps", "8208", "fishes"),
    ("Takifugu rubripes", "31033", "fishes"),
    ("Arabidopsis thaliana", "3702", "plants"),
    ("Oryza sativa", "4530", "plants"),
    ("Zea mays", "4577", "plants"),
    ("Escherichia coli", "562", "bacteria"),
    ("Bacillus subtilis", "1423", "bacteria"),
    ("Drosophila melanogaster", "7227", "insects"),
    ("Caenorhabditis elegans", "6239", "nematodes"),
    ("Gallus gallus", "9031", "birds"),
    ("Xenopus laevis", "8355", "amphibians"),
    ("Anolis carolinensis", "28377", "reptiles"),
    ("Saccharomyces cerevisiae", "4932", "fungi"),
    ("HIV-1", "11676", "viruses"),
]

GENE_POOL = [
    ("TP53", "7157"),
    ("BRCA1", "672"),
    ("MYC", "4609"),
    ("HSP70", "3303"),
    ("GAPDH", "2597"),
    ("ACTB", "60"),
    ("EGFR", "1956"),
    ("KRAS", "3845"),
    ("PTEN", "5728"),
    ("AKT1", "207"),
    ("MAPK1", "5594"),
    ("TNF", "7124"),
    ("IL6", "3569"),
    ("VEGFA", "7422"),
    ("BCL2", "596"),
]

RESEARCH_TYPES = [
    "Expression Analysis",
    "Variant Analysis",
    "Mutation Analysis",
    "Functional Analysis",
    "Genome Structure Analysis",
    "Regulation Analysis",
]

SPECIES_TYPES = [
    "mammals", "plants", "fishes", "bacteria", "insects",
    "birds", "amphibians", "nematodes", "reptiles", "fungi", "viruses"
]

def generate_row(pmid: int) -> dict:
    """Generate one random row of paper data."""

    # Random number of species (1-3)
    n_species = random.randint(1, 3)
    species_list = random.sample(SPECIES_POOL, n_species)

    # Random number of genes (1-5)
    n_genes = random.randint(1, 5)
    gene_list = random.sample(GENE_POOL, n_genes)

    # Random number of research types (1-3)
    n_research = random.randint(1, 3)
    research_list = random.sample(RESEARCH_TYPES, n_research)

    # Create concatenated fields
    species_names = ";".join([sp[0] for sp in species_list])
    species_ids = ";".join([sp[1] for sp in species_list])
    species_types_set = set([sp[2] for sp in species_list])
    species_types = ";".join(sorted(species_types_set))

    gene_names = ";".join([g[0] for g in gene_list])
    gene_ids = ";".join([g[1] for g in gene_list])

    gene_research_types = ";".join(research_list)

    # One-hot encoding for research types
    has_expression = "Expression Analysis" in research_list
    has_variant = "Variant Analysis" in research_list
    has_mutation = "Mutation Analysis" in research_list
    has_functional = "Functional Analysis" in research_list
    has_genome = "Genome Structure Analysis" in research_list
    has_regulation = "Regulation Analysis" in research_list

    # One-hot encoding for species types
    species_type_flags = {
        f"is_{st}": st in species_types_set for st in SPECIES_TYPES
    }

    row = {
        "pmid": str(pmid),
        "species_names": species_names,
        "species_ids": species_ids,
        "species_types": species_types,
        "num_species": n_species,
        "gene_names": gene_names,
        "gene_ids": gene_ids,
        "num_genes": n_genes,
        "gene_research_types": gene_research_types,
        "num_research_types": n_research,
        "has_expression_analysis": has_expression,
        "has_variant_analysis": has_variant,
        "has_mutation_analysis": has_mutation,
        "has_functional_analysis": has_functional,
        "has_genome_structure_analysis": has_genome,
        "has_regulation_analysis": has_regulation,
        **species_type_flags,
    }

    return row

def main():
    """Generate 100 rows of test data."""
    random.seed(42)  # For reproducibility
    np.random.seed(42)

    # Generate 100 rows with random PMIDs
    base_pmid = 10000000
    rows = []
    for i in range(100):
        pmid = base_pmid + i * 1000 + random.randint(0, 999)
        row = generate_row(pmid)
        rows.append(row)

    # Create DataFrame
    df = pd.DataFrame(rows)

    # Save to CSV
    output_file = "test_papers_100rows.csv"
    df.to_csv(output_file, index=False)

    print(f"✓ Generated {len(df)} rows of test data")
    print(f"✓ Saved to: {output_file}")
    print(f"\nDataFrame info:")
    print(f"  Shape: {df.shape}")
    print(f"  Columns: {len(df.columns)}")
    print(f"\nColumn names:")
    for col in df.columns:
        print(f"  - {col}")

    print(f"\nSample statistics:")
    print(f"  num_species: mean={df['num_species'].mean():.2f}, range=[{df['num_species'].min()}, {df['num_species'].max()}]")
    print(f"  num_genes: mean={df['num_genes'].mean():.2f}, range=[{df['num_genes'].min()}, {df['num_genes'].max()}]")
    print(f"  num_research_types: mean={df['num_research_types'].mean():.2f}, range=[{df['num_research_types'].min()}, {df['num_research_types'].max()}]")

    print(f"\nFirst 3 rows:")
    print(df.head(3).to_string())

if __name__ == "__main__":
    main()
