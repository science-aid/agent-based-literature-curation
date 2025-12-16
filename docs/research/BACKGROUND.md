# Background

## Research Context

The systematic identification and curation of genetic research literature on non-model organisms presents substantial practical challenges. While model organisms—such as *Escherichia coli*, *Drosophila melanogaster*, and *Mus musculus*—have long served as cornerstones of genetic research, studies of non-model organisms offer complementary biological insights that are not fully captured by these established systems.

---

## Scientific Importance of Non-Model Organism Genetics

Non-model organisms play a critical role across multiple domains of biological research.

### Biodiversity and Functional Diversity

Non-model organisms often harbor unique metabolic pathways, adaptive strategies, and protein repertoires that are absent from conventional model systems. These features are essential for advancing evolutionary biology, ecology, and systems-level understanding of biological complexity.

### Applied Biotechnology Potential

Many non-model organisms represent largely untapped reservoirs of biotechnologically valuable traits, including novel enzymes, natural product biosynthesis pathways, and mechanisms of tolerance to environmental stresses such as salinity, drought, and disease.

### Phylogenetics and Comparative Genomics

Accurate inference of phylogenetic relationships and gene family evolution requires broad taxonomic sampling. Overreliance on model organisms constrains the resolution and generalizability of comparative genomic analyses.

### Addressing Taxonomic Bias

The disproportionate emphasis on model organisms introduces systematic taxonomic bias into the scientific literature. Incorporation of non-model organisms enables validation of general biological principles and promotes a more representative understanding of biological systems.

---

## Problem Statement

Despite their scientific importance, the identification of genetic research focused on non-model organisms remains challenging.

### Current Limitations

#### Labor-Intensive Manual Curation

To our knowledge, no fully automated or systematic method currently exists for efficiently identifying non-model organism genetics papers from large-scale literature databases. Existing approaches rely heavily on manual review, including:

* Individual examination of titles, abstracts, and MeSH terms across thousands of publications (e.g., 4,940 papers in our case)
* Construction of complex database queries requiring expert knowledge of biological nomenclature
* Iterative searches across multiple resources (e.g., NCBI Gene, NCBI Taxonomy)
* Manual extraction and structuring of gene names, gene identifiers, species names, taxonomy IDs, higher-level taxonomic classifications, and research categories

#### Complexity Beyond Traditional Workflows

Literature screening for non-model organism genetics involves challenges that exceed the capacity of traditional mechanical workflows, including:

* Multiple decision points requiring domain-specific expertise
* Autonomous task execution with adaptive query formulation
* Integration of heterogeneous biological databases
* Contextual interpretation that cannot be reliably captured by rule-based or simple keyword-matching approaches

These characteristics motivate the need for more sophisticated, AI-driven solutions.

---

## Motivation

### Hypothesis

While PubTator demonstrates strong performance in species recognition and gene annotation for model organisms, we hypothesize that gene annotation for non-model organisms is inherently more challenging. This difficulty likely arises from heterogeneous and inconsistent gene nomenclature, resulting in suboptimal annotation performance.

### Validation of Species Recognition Performance

To contextualize this hypothesis, we examined the composition of PubTator’s species recognition evaluation datasets to assess representation of non-model organisms:

* Analysis of the PubTator3 evaluation dataset revealed that **85.93% (104/635) of test cases correspond to non-model organisms** (AIONER test dataset: [https://github.com/ncbi/AIONER/blob/main/data/pubtator/SPECIES_Test.PubTator](https://github.com/ncbi/AIONER/blob/main/data/pubtator/SPECIES_Test.PubTator))
* Species named entity recognition and entity linking achieved high performance in these evaluations
* Validation results are documented in `data/species_match`, using `scripts/check_species_match.py`

**Working Assumption**
Based on this evidence, we assume that PubTator’s species recognition performance is reliable for non-model organisms and therefore focus our investigation on potential limitations in gene annotation.

---

## AI Agent-Based Approach

Given the complexity of multi-step decision-making, database integration, and contextual interpretation required for literature curation, we propose an **AI agent-based approach** as a suitable solution. AI agents are capable of:

* Autonomously navigating complex decision trees during literature evaluation
* Performing iterative database queries with adaptive refinement
* Integrating information across multiple biological databases
* Extracting and structuring relevant metadata, including gene identifiers, species information, taxonomic classifications, and research categories
* Scaling to large literature corpora while maintaining consistent evaluation criteria

---

## Related Work

### Existing Literature Annotation Systems

**PubTator**
PubTator, developed by the NCBI, provides automated bioconcept annotation for biomedical literature. Although effective for many annotation tasks, its performance in gene annotation for non-model organisms has not been systematically evaluated.

**Manual Curation**
Gold-standard annotations depend on expert manual curation, which remains prohibitively time-consuming and impractical for large-scale literature databases.

**Rule-Based Systems**
Traditional keyword-based and rule-based approaches lack the flexibility and contextual understanding required to accurately identify non-model organism genetics research.

### Gap in Current Approaches

To date, no existing system simultaneously provides:

1. High-precision identification of non-model organism genetics literature
2. Automated and scalable processing of large literature corpora
3. Structured extraction of genetic and taxonomic metadata
4. Domain-aware decision-making for ambiguous or borderline cases

This study addresses these gaps through the development and evaluation of AI agent-based literature curation systems specifically tailored to non-model organism genetics research.

