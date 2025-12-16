# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-12-15

### Added
- Initial public release of AI agent-based literature curation system
- Complete research documentation (BACKGROUND, METHODS, RESULTS, DISCUSSION, LIMITATIONS)
- GitHub Pages site with MkDocs for research presentation
- Conference poster (PDF and PNG) from MBSJ 2025
- Docker environment setup for reproducible analysis
- Eight analysis scripts for complete workflow:
  - `wf_pre_agent.py`: PubMed paper collection and filtering
  - `filter_pubtator_annotations.py`: PubTator baseline dataset creation
  - `run_biomni_batch_experiment.py`: Batch orchestrator for Biomni agents
  - `biomni_experiment_worker.py`: Worker for individual paper processing
  - `filter_paper_default_biomni.py`: Parser for Default Biomni outputs
  - `select_model_species.py`: Top 20 model organism identification
  - `calculate_precision.py`: Precision metrics for Biomni methods
  - `calculate_precision_pubtator.py`: Precision metrics for PubTator
- Comprehensive README with Docker usage instructions
- Model organism coverage analysis with visualization
- Ground truth curation dataset
- Complete experimental results and analysis

### Research Findings
- Custom Biomni achieved 90.91% precision in identifying non-model organism genetics papers
- Default Biomni achieved 80.00% precision
- PubTator baseline achieved 60.00% precision
- Validated on corpus of 531 papers from December 1-3, 2024

## [Unreleased]

### Planned
- Recall and F1-score evaluation
- Expanded evaluation dataset with longer sampling window
- Additional validation with independent expert reviewers
- Enhanced classification framework refinements
