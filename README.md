# Agent-based Literature Curation

Validation of AI Agent-Based Curation for Low-Noise Literature Set Construction.

## Overview

This repository contains code and data for curation of scientific literature sets using AI agents (Biomni). We compare three approaches for identifying non-model organism genetics literature set.

**Built with Biomni**: This research is built upon [Biomni](https://biomni.stanford.edu/), an open-source AI agent framework developed at Stanford University for biological and biomedical research.

> Huang, K., Zhang, S., Wang, H., et al. (2025). Biomni: A General-Purpose Biomedical AI Agent. *bioRxiv*. https://doi.org/10.1101/2025.05.30.656746

## Key Features

- **AI Agent-based Curation**: Automated literature screening using large language model agents
- **Precision Comparison**: Benchmark of multiple NER systems (Biomni, Custom Biomni, PubTator)
- **Focus Area**: Non-model organism genetics research papers

## Methods Compared

- **Default Biomni**: Baseline biological entity recognition
- **Custom Biomni**: Enhanced with domain-specific customization
- **PubTator**: NCBI's literature annotation system

## Results

Our custom Biomni approach achieved **90.91% precision** in constructing a corpus of genetic research articles on non-model organisms, substantially outperforming Default Biomni (80.00%) and PubTator (60.00%).

**For detailed research documentation**, please visit our [GitHub Pages](https://science-aid.github.io/agent-based-literature-curation/) or see:

- [docs/research/BACKGROUND.md](docs/research/BACKGROUND.md) - Research context and motivation
- [docs/research/METHODS.md](docs/research/METHODS.md) - Detailed methodology and operational definitions
- [docs/research/RESULTS.md](docs/research/RESULTS.md) - Performance comparison and metrics
- [docs/research/DISCUSSION.md](docs/research/DISCUSSION.md) - Analysis of false positives/negatives
- [docs/research/LIMITATIONS.md](docs/research/LIMITATIONS.md) - Study constraints and future work

## Publication

Presented at the 48th Annual Meeting of the Molecular Biology Society of Japan (第48回日本分子生物学会年会), December 3, 2025

## Getting Started

### Prerequisites

- Docker installed on your system

### Setup

#### 1. Build the Docker Image

```bash
docker build -f setup/Dockerfile -t res-agent .
```

This will create a Docker image named `res-agent` with all necessary dependencies for running the AI agent.

#### 2. Run the Docker Container

To use the scripts in this repository, you need to run them inside the Docker container:

```bash
docker run -it --rm -v $(pwd):/workspace res-agent /bin/bash
```

This command:
- `-it`: Runs the container in interactive mode with a terminal
- `--rm`: Automatically removes the container when you exit
- `-v $(pwd):/workspace`: Mounts the current directory to `/workspace` in the container
- `res-agent`: Uses the image you built
- `/bin/bash`: Starts a bash shell

#### 3. Run Scripts Inside the Container

Once inside the container, you can run any Python script:

```bash
# Example: Calculate precision for Biomni results
python scripts/calculate_precision.py

# Example: Analyze model organisms
python scripts/select_model_species.py
```

**Note**: All Python scripts must be run inside the Docker container, as they require specific dependencies installed in the container environment.

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
X: [@sci_aid_tszk](https://x.com/sci_aid_tszk)

## License

### Code

The code in this repository is licensed under the **Apache License 2.0**. See the [LICENSE](LICENSE) file for details.

This project is built upon [Biomni](https://github.com/snap-stanford/biomni), which is also licensed under Apache License 2.0.

### Documentation and Data

The documentation and research data are licensed under the **Creative Commons Attribution 4.0 International License (CC BY 4.0)**.

You are free to:
- Share — copy and redistribute the material in any medium or format
- Adapt — remix, transform, and build upon the material for any purpose, even commercially

Under the following terms:
- **Attribution** — You must give appropriate credit, provide a link to the license, and indicate if changes were made

For more information, see https://creativecommons.org/licenses/by/4.0/
