# Agent-based Literature Curation

AI agent-based system for precision literature curation for papers of genetic research of non-model species.

## Overview

This repository contains code and data for curation of scientific literature using AI agents. We compare three approaches for identifying non-model organism genetics papers.

## Key Features

- **AI Agent-based Curation**: Automated literature screening using large language model agents
- **Precision Comparison**: Benchmark of multiple NER systems (Biomni, Custom Biomni, PubTator)
- **Focus Area**: Non-model organism genetics research papers

## Methods Compared

- **Default Biomni**: Baseline biological entity recognition
- **Custom Biomni**: Enhanced with domain-specific customization
- **PubTator**: NCBI's literature annotation system

## Results

Our custom Biomni approach achieved higher precision in identifying relevant non-model organism genetics papers compared to existing methods.

## Publication

Presented at the 48th Annual Meeting of the Molecular Biology Society of Japan (第48回日本分子生物学会年会), December 3-6, 2025

## Getting Started

### Prerequisites

- Docker installed on your system

### Setup

#### 1. Build the Docker Image

```bash
docker build -f setup/Dockerfile -t res-agent .
```

This will create a Docker image named `res-agent` with all necessary dependencies for running the AI agent.

## Key Scripts

### Literature Collection and Filtering

- **`scripts/wf_pre_agent.py`**: Collects papers from PubMed and performs initial filtering to identify candidate non-model organism papers used in our evaluation

- **`scripts/filter_pubtator_annotations.py`**: Retrieves PubTator annotations and filters papers to create the PubTator baseline dataset

### AI Agent-based Curation

- **`scripts/run_Biomni_batch_experiment.py`**: Orchestrates batch processing of papers using Biomni agents (supports both Default and Custom configurations)

- **`scripts/Biomni_experiment_worker.py`**: Worker script that processes individual papers with the Biomni agent

- **`scripts/filter_paper_default_Biomni.py`**: Parses heterogeneous outputs from Default Biomni logs to extract structured annotations (required due to inconsistent output format)

### Data Preparation

- **`scripts/select_model_species.py`**: Identifies top 20 model organisms from genome editing meta-database (`results/gem/20251008_ge_metadata_all.csv`) and generates visualization (`figures/model_species/top20_organisms_bar_chart.png`)

### Evaluation and Analysis

- **`scripts/calculate_precision.py`**: Calculates precision metrics for Default Biomni and Custom Biomni results against manually curated ground truth

- **`scripts/calculate_precision_pubtator.py`**: Calculates precision metrics for PubTator baseline results

## Data Availability

**Note**: Full dataset and analysis code will be made available shortly after the conference presentation.

## Contact

name: Takayuki Suzuki
email: takayuki.suzuki@science-aid.com

## License

[To be determined]

---

*This repository is under active development. Full documentation and data will be released soon.*