# Methods

## Overview

This study compares three approaches for constructing a high-precision corpus of genetic research articles on non-model organisms: (1) PubTator-based annotation filtering, (2) a Biomni AI agent with default configuration, and (3) a Biomni AI agent with custom enhancements. We evaluated these methods on a corpus of open-access journal articles published over a three-day period, assessing their precision in identifying relevant literature.

## Operational Definitions

### Model vs. Non-Model Organisms

**Model Organism Definition**: We operationally defined model organisms as the top 20 most frequently studied species in genetic research, based on annotation frequency in genome editing meta-database (https://doi.org/10.1016/j.ggedit.2022.100024).

**Data Source**: Genome editing meta-database (`data/20251008_ge_metadata_all.csv`) (downloaded from https://github.com/szktkyk/gem_api)

**Selection Criteria**:
- Analyzed species frequency in studies using genome editing tools since 2000
- Top 20 species classified as "model organisms"
- All other species classified as "non-model organisms"
- Implementation: `scripts/select_model_species.py`

**Coverage Analysis**:
- The top 20 model organisms accounted for **92.21%** of all papers in the database
- Results documented in `config/top20_organisms_with_taxid.csv`
- Visualization available in `figures/model_species/top20_organisms_bar_chart.png`
- coverage statistics available in `figures/model_species/coverage_statistics.txt`

**Reference Sources**:
- NIH Model Organisms FAQ: https://public.csr.nih.gov/FAQs/ReviewersFAQs/ModelOrganisms
- Howe et al. (2017). The Model Organism as a System: Integrating 'Omics' Data Sets. *BMC Biology*, 15:45. https://doi.org/10.1186/s12915-017-0391-5

### Genetics Research Classification

**Scope Definition**: The scope of this study was operationally defined to focus on genetic research conducted within non-model organisms. Given the lack of a widely accepted definition of “non-model organism genetics research” in the literature, we adopted a pragmatic scope tailored to the objectives of this analysis. Specifically, we excluded studies in which non-model organisms were primarily investigated in the context of their effects on model organism genomes or biology (e.g., bacterial effects on human genomes), as such studies are centered on model organisms rather than on the genetics of non-model species themselves.

**Classification Framework*: In the absence of standardized taxonomies for classifying genetic research in non-model organisms, we developed a six-category classification framework to capture the major types of genetic studies observed in the literature. 

The six genetics research categories used in this study are as follows:

1. **Genomic Sequencing & Identification**: Genome sequencing and novel gene identification
2. **Comparative Analysis & Annotation**: Ortholog/homolog analysis for functional inference through sequence homology
3. **Gene Expression Profiling**: Expression analysis across conditions, tissues, or developmental stages
4. **Phylogenetic and Evolutionary Analysis**: Gene family expansion/contraction and evolutionary adaptation signatures
5. **Functional Validation & Bioengineering**: Experimental validation using techniques such as CRISPR or RNAi
6. **Methodological Development & Diagnostics**: Development of genetic diagnostic techniques and methodological advances

**Inclusion Criteria**: Papers satisfying at least one of the above six categories were classified as genetics research.

**Note**: This classification system represents an initial framework. More refined categorization may be possible upon completion of comprehensive literature annotation.

## Data Collection

### Literature Corpus

**Search Query**: `all[filter] AND pubmed pmc open access[filter] AND journal article[pt]`

**Date Range**: December 1-3, 2024 (3-day window)

**Initial Corpus Size**: 4,959 articles 

**Limitation**: The narrow 3-day sampling window represents a methodological limitation. Ideally, a 1-month window with random sampling would provide more representative coverage. See [LIMITATIONS.md](LIMITATIONS.md) for detailed discussion.

### Workflow for AI Agent Input Selection

**Implementation**: `wf_pre_agent.py`

**Configuration Parameters**:
```python
config = WorkflowConfig(
    date_start="20241201",
    date_end="20241203",
    days_per_chunk_step1=1,
    chunk_size_step2=900,
    chunk_size_step3=400,
    max_retries=3,
    retry_delay=10,
    model_species_config="config/top20_organisms_with_taxid.csv",
    output_dir="data/pre_agent"
)
```

**Filtering Criteria**:
- Used PubTator annotations on titles and abstracts
- Selected papers where the most frequently mentioned species was a non-model organism
- **Filtered Corpus Size**: 531 papers

**Quality Control**:
- Manual validation of `main()` function
- Unit tests implemented in `test_wf_pre_agent.py`
- Venn diagram visualization generated using `create_venn_diagram.py` (output: `figures/wf_filtering/`)

### Workflow for PubTator Baseline

**Implementation**: `filter_pubtator_annotations.py`

**Input**: 531-paper corpus from AI agent workflow

**Filtering Criteria**:
1. Retrieved all PubTator annotations (species and genes) from titles and abstracts
2. Excluded papers with any model organism annotations
3. Excluded papers lacking both species and gene annotations

**Filtered Corpus Size**: 55 papers (10.4% of 531-paper corpus)

**Stability Check**: Replication in November 2024 yielded identical 55-paper result, confirming reproducibility.

## Experimental Setup

### PubTator Baseline

**Approach**: Rule-based filtering using existing PubTator annotations

**Rationale**: Establishes baseline performance of current state-of-the-art automated annotation systems

**Process**:
1. Extract species and gene annotations from PubTator API
2. Apply filtering rules (exclude model organisms, require gene annotations)
3. No manual intervention or AI-based decision making

### Default Biomni Agent

**Framework**: Biomni (https://biomni.stanford.edu/) with CodeAct architecture

**Model**: GPT-4.1-mini (selected over GPT-5-mini due to 20-40 second latency reduction)

**Tools Available**: Standard Biomni toolkit for literature analysis and database queries

**Limitations of Batch Processing**:
- Initial attempts to process all 531 papers in a single agent session failed
- CodeAct architecture generated loop-based code that applied uniform processing to all PMIDs
- This prevented the desired "organic processing" (identify gene → query database → validate → compare with species → query alternative candidates)
- **Solution**: Implemented paper-by-paper processing approach

### Custom Biomni Agent

**Enhancements over Default Biomni**:

#### 1. MCP Server Integration

**NCBI Gene Database Access** (Enhanced Entity Linking):
- Query NCBI Gene database for gene information
- Retrieve gene names, IDs, and synonyms
- Validate consistency by cross-referencing gene name with species taxonomy ID

**NCBI Taxonomy Database Access** (Enhanced Entity Linking):
- Query NCBI Taxonomy database for species information
- Retrieve taxonomy IDs, scientific names, and taxonomic classifications (class level)
- Enable precise species identification and validation

**Structured Data Generation** (Robust Data Capture):
- Incrementally append validated annotations to structured output files
- Ensure data persistence in case of agent interruption
- Enable resumable processing for large batches

#### 2. Iterative Development and Validation

Conducted six rounds of agent behavior validation and prompt refinement:
- [Trial 1-6 documentation links preserved for internal reference]
- Final prompt design and paper-level processing approach determined in Trial 6
- Implementation: `run_agent_20251030.py`

#### 3. Batch Processing Architecture

**Challenge**: Memory accumulation from repeated `agent.go()` calls
- Accumulated message history and MCP connections
- All log_messages retained in memory
- Memory exhaustion (OOM Killer) after ~76 papers

**Solution**: Subprocess-based batch processing
- Implementation: `run_agent_batch_subprocess.py` (orchestrator) + `run_agent_worker.py` (worker)
- Process papers in small batches with agent restart between batches
- Achieved stable processing of 419 papers without interruption

## Performance and Cost Analysis

**Processing Volume**: 419 papers (manual termination; system remained stable)

**Results**: 62 papers identified as non-model organism genetics research (14.8% hit rate)

**Computational Cost** (300-paper subset):
- Total Cost: $3.76
- Total Processing Time: 11,182.65 seconds (3.11 hours)
- Average Time per Paper: 37.3 seconds
- Average Cost per Paper: $0.0125

## Evaluation Metrics

### Precision

**Definition**:
$$\text{Precision} = \frac{\text{True Positives}}{\text{True Positives + False Positives}}$$

**Rationale for Focus on Precision**:
- For this project, minimizing false positives (irrelevant papers incorrectly classified as relevant) has been mostly paid attention
- High precision ensures curated sets contain primarily relevant papers
- Recall (sensitivity) and F1-score evaluation deferred to future work

**Ground Truth Establishment**: Manual curation of sampled papers to establish true positive classifications

**Evaluation Scope**: This study reports precision only. Comprehensive evaluation including accuracy, recall, and F1-score remains for future investigation (see [LIMITATIONS.md](LIMITATIONS.md)).

## Implementation Details

**Programming Language**: Python 3.11.14

**Key Dependencies**:
- Biomni framework
- OpenAI API (GPT-4.1-mini)
- NCBI E-utilities
- PubTator API

**Code Availability**:
- Workflow implementations: `wf_pre_agent.py`, `filter_pubtator_annotations.py`
- Agent implementations: `run_agent_batch_subprocess.py`, `run_agent_worker.py`
- Analysis scripts: `scripts/select_model_species.py`, `scripts/check_species_match.py`
- Configuration files: `config/top20_organisms_with_taxid.csv`, `config/mcp_config.yaml`

**Docker Environment**:
- Dockerfile: `setup/Dockerfile`
- Environment specifications: `setup/environment.yml`, `setup/customized_bio_env.yml`

**Reproducibility**: All code, configurations, and processed data are available in this repository to enable full reproduction of results.
