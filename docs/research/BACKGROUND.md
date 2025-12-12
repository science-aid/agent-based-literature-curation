# Background

## Research Context

The systematic identification and curation of genetic research literature on non-model organisms represents a critical challenge in modern biological sciences. While model organisms such as *Escherichia coli*, *Drosophila melanogaster*, and *Mus musculus* have historically dominated genetic research, non-model organisms harbor essential biological insights that cannot be fully captured through model species alone.

### Scientific Importance of Non-Model Organism Genetics

Non-model organisms are crucial for advancing multiple domains of biological research:

**Biodiversity and Functional Diversity**: Non-model organisms frequently exhibit metabolic pathways, adaptation mechanisms, and protein diversity that are absent in conventional model systems. These unique features are essential for comprehensive understanding in evolutionary biology and ecology.

**Applied Biotechnology Potential**: Non-model organisms serve as repositories for novel enzymes, natural product biosynthesis pathways, and stress resistance mechanisms (e.g., salt tolerance, drought resistance, disease resistance), offering substantial biotechnological applications.

**Phylogenetics and Comparative Genomics**: Robust phylogenetic positioning and gene family evolution analyses require broad taxonomic sampling that extends beyond model organisms.

**Addressing Taxonomic Bias**: Over-reliance on model organisms introduces systematic biases in biological research. Incorporating non-model organisms enables validation of generalizable biological principles and mitigates taxonomic bias in the literature.

## Problem Statement

Despite their scientific value, identifying relevant genetic research on non-model organisms presents substantial challenges:

### Current Limitations

**Labor-Intensive Manual Curation**: To our knowledge, no automated or systematic method exists for efficiently identifying non-model organism genetics papers from large literature databases. Current approaches require extensive manual review of:

- Individual examination of titles, abstracts, and MeSH terms across thousands of publications (e.g., 4,940 papers)
- Strategic database queries requiring expert knowledge of biological nomenclature
- Iterative searches across multiple databases (e.g., NCBI Gene, NCBI Taxonomy)
- Structured extraction of gene names, gene IDs, species names, taxonomy IDs, taxonomic classifications (class level), and research types

**Complexity Beyond Traditional Workflows**: Literature screening for non-model organism genetics requires:

- Multiple decision points requiring domain expertise
- Autonomous task execution with adaptive query formulation
- Integration of information across heterogeneous biological databases
- Contextual understanding that cannot be captured by rule-based or simple keyword-matching approaches

These characteristics make traditional mechanical workflows insufficient, necessitating more sophisticated AI-based solutions.

## Motivation

### Hypothesis

We hypothesize that existing automated literature annotation systems, particularly PubTator, exhibit high false-negative rates for gene annotations in non-model organisms. While PubTator demonstrates robust performance for species recognition (evidenced by high Named Entity Recognition and Linking performance in PubTator3 evaluations), its gene annotation capabilities for non-model organisms remain questionable.

### Validation of Species Recognition Performance

To validate our hypothesis, we examined PubTator's species recognition performance on non-model organisms:

- PubTator3 evaluation dataset analysis revealed that **85.93% (104/635) of test cases represented non-model organisms** (AIONER test data: https://github.com/ncbi/AIONER/blob/main/data/pubtator/SPECIES_Test.PubTator)
- Species NER and entity linking showed high performance metrics in these evaluations
- Results are documented in `data/species_match` (validation performed using `scripts/check_species_match.py`)

**Working Assumption**: Based on this evidence, we proceed under the assumption that PubTator's species recognition is reliable, and focus our investigation on potential limitations in gene annotation for non-model organisms.

### AI Agent-Based Approach

Given the complexity of multi-step decision-making, database integration, and contextual interpretation required for literature curation, we propose an **AI agent-based approach** as the appropriate solution. AI agents can:

- Autonomously navigate complex decision trees for literature evaluation
- Perform iterative database queries with adaptive query refinement
- Integrate information across multiple biological databases
- Extract and structure relevant metadata (gene names/IDs, species information, taxonomic classifications, research types)
- Scale to large literature corpora with consistent evaluation criteria

## Related Work

### Existing Literature Annotation Systems

**PubTator**: The NCBI's PubTator system provides automated bioconcept annotation for biomedical literature. While effective for many annotation tasks, its performance on non-model organism gene annotation has not been systematically evaluated.

**Manual Curation**: Gold-standard annotations rely on expert manual curation, which remains prohibitively time-consuming for large-scale literature databases.

**Rule-based Systems**: Traditional keyword-matching and rule-based approaches lack the flexibility and contextual understanding necessary for accurate identification of non-model organism genetics research.

### Gap in Current Approaches

No existing system combines:
1. High-precision identification of non-model organism genetics papers
2. Automated, scalable processing for large literature corpora
3. Structured extraction of relevant genetic and taxonomic information
4. Domain-aware decision-making for ambiguous cases

This research addresses these gaps through the development and evaluation of AI agent-based literature curation systems specifically designed for non-model organism genetics research.
