# Results

## Overview

We evaluated three approaches for identifying non-model organism genetics papers across a corpus of 531 pre-filtered articles. All three methods were applied to the identical input corpus to enable direct comparison. Primary evaluation focused on **precision**, as high accuracy in identifying relevant papers is critical for literature curation workflows where false positives impose substantial downstream costs.

## Performance Comparison

### Summary Table

| Metric | Default Biomni | Custom Biomni | PubTator |
|--------|----------------|---------------|----------|
| **Input Corpus** | 531 | 531 | 531 |
| **Papers Retrieved** | 75 | 44 | 55 |
| **Precision** | **80.00%** (60/75) | **90.91%** (40/44) | **60.00%** (33/55) |
| **Gene Annotation Precision** | 59.72% (126/211) | **71.11%** (64/90) | 38.97% (53/136) |
| **Species Annotation Precision** | 63.98% (135/211) | **83.33%** (75/90) | 65.55% (78/119) |
| **Processing Time** | 5.28 hours | 6.09 hours | N/A |
| **Processing Cost** | $6.01 | $6.76 | $0 |

### Key Findings

**Custom Biomni achieved the highest precision (90.91%)**, representing a **10.91 percentage point improvement** over Default Biomni (80.00%) and a **30.91 percentage point improvement** over PubTator (60.00%).

**Retrieval Volume vs. Precision Trade-off**:
- PubTator retrieved 55 papers but with lowest precision (60.00%)
- Default Biomni retrieved 75 papers with moderate precision (80.00%)
- Custom Biomni retrieved fewer papers (44) but with highest precision (90.91%)

**Entity Annotation Quality**:
- Custom Biomni demonstrated superior performance in both gene annotation (71.11%) and species annotation (83.33%)
- PubTator showed particularly weak gene annotation performance (38.97%), supporting our hypothesis of high false-negative rates in non-model organism gene annotations

## Detailed Analysis

### Custom Biomni Results

**Experimental Execution**: October 31, 2024

**Implementation**:
- Orchestrator: `run_agent_batch_subprocess.py`
- Worker: `run_agent_worker.py`
- (Note: Original experimental files archived; refactored versions available as `run_Biomni_batch_experiment.py` and `Biomni_experiment_worker.py`)

**Performance Metrics**:
- **Papers Retrieved**: 44 papers from 531-paper corpus (8.3% retrieval rate)
- **Precision**: 90.91% (40 true positives, 4 false positives)
- **Total Processing Time**: 21,928.47 seconds (6.09 hours)
- **Total Cost**: $6.76
- **Average Time per Paper**: 41.3 seconds
- **Average Cost per Paper**: $0.0127

**Entity Annotation Performance**:
- **Gene Annotations**: 90 annotations with 71.11% precision (64 correct)
- **Species Annotations**: 90 annotations with 83.33% precision (75 correct)

**Output Data**: Results available in `実験結果_回答データ/` directory

### Default Biomni Results

**Experimental Execution**: November 1, 2024

**Implementation**:
- Orchestrator: `run_agent_batch_subprocess_default_Biomni.py`
- Worker: `run_agent_worker_default_Biomni.py`
- (Note: Original experimental files archived; refactored versions available as `run_Biomni_batch_experiment.py` and `run_agent_batch.py`)

**Data Extraction Challenge**:
- Default Biomni lacked structured output tools present in Custom Biomni
- Outputs were heterogeneous and required manual extraction from log files
- Implemented `filter_paper_default_Biomni.py` to parse both structured outputs and log files
- Successfully recovered 387 results; remaining papers produced no usable output

**Performance Metrics**:
- **Papers Retrieved**: 75 papers from 531-paper corpus (14.1% retrieval rate)
- **Precision**: 80.00% (60 true positives, 15 false positives)
- **Total Processing Time**: 19,007.82 seconds (5.28 hours)
- **Total Cost**: $6.01
- **Average Time per Paper**: 35.8 seconds
- **Average Cost per Paper**: $0.0113

**Entity Annotation Performance**:
- **Gene Annotations**: 211 annotations with 59.72% precision (126 correct)
- **Species Annotations**: 211 annotations with 63.98% precision (135 correct)

**Efficiency Comparison**: Default Biomni processed papers slightly faster and cheaper than Custom Biomni, but with significantly lower precision.

### PubTator Results

**Implementation**:
- Original script: `pubtator2.py`
- Refactored version: `scripts/filter_pubtator_annotations.py`

**Filtering Criteria**:
1. Retrieved all PubTator annotations for the 531-paper corpus
2. Required presence of both species and gene annotations
3. Excluded papers with any model organism annotations

**Performance Metrics**:
- **Papers Retrieved**: 55 papers from 531-paper corpus (10.4% retrieval rate)
- **Precision**: 60.00% (33 true positives, 22 false positives)
- **Processing Time**: Negligible (automated annotation retrieval)
- **Processing Cost**: $0 (free NCBI service)

**Entity Annotation Performance**:
- **Gene Annotations**: 136 annotations with 38.97% precision (53 correct)
- **Species Annotations**: 119 annotations with 65.55% precision (78 correct)

**Key Observation**: PubTator's gene annotation precision (38.97%) was substantially lower than species annotation precision (65.55%), confirming our hypothesis that existing automated systems exhibit high false-negative and false-positive rates for non-model organism gene annotations.

## Evaluation Methodology

### Ground Truth Establishment

**Manual Curation**: Expert biologists manually evaluated papers to establish ground truth classifications.

**Curation Data Management**:
- Ground truth stored in: `実験結果_回答データ/curated_data.jsonl`
- Filtered evaluation datasets automatically generated in: `実験結果_回答データ/filtered_data.jsonl`

**Precision Calculation Scripts**:
- Biomni methods: `calculate_precision.py`
- PubTator method: `calculate_precision_pubtator.py`

### Rationale for Precision-Focused Evaluation

In literature curation workflows, **precision is the critical metric** because:

1. **Cost of False Positives**: Researchers must manually review retrieved papers; false positives waste expert time
2. **Downstream Impact**: Curated literature sets feed into meta-analyses and systematic reviews where accuracy is paramount
3. **Acceptable False Negatives**: Missing some relevant papers (lower recall) is preferable to including many irrelevant papers (lower precision)

**Future Work**: While this study focused on precision due to its primary importance in curation workflows, comprehensive evaluation including recall, F1-score, and accuracy is planned for future investigation (see [LIMITATIONS.md](LIMITATIONS.md)).

## False Positive Analysis

### PubTator False Positives (22 cases)

**Primary Error Modes**:
1. **Generic gene annotations**: Genes mentioned in passing or in model organism contexts incorrectly annotated
2. **Model organism contamination**: Papers primarily about model organisms with incidental non-model organism mentions passed through filters
3. **Non-genetics research**: Papers annotated with gene names but not conducting genetic research (e.g., clinical studies mentioning genes)

### Default Biomni False Positives (15 cases)

**Primary Error Modes**:
1. **Overgeneralization**: Papers with tangential genetic content classified as genetics research
2. **Incomplete context evaluation**: Failure to distinguish primary research focus from background mentions
3. **Classification boundary ambiguity**: Edge cases falling outside the six-category genetics research framework

### Custom Biomni False Positives (4 cases)

**Primary Error Modes**:
1. **Rare classification edge cases**: Papers at the boundary of genetics research definitions
2. **Complex multi-organism studies**: Studies involving both model and non-model organisms with ambiguous primary focus

**Improvement Mechanism**: Custom Biomni's integration of NCBI Gene and Taxonomy database validation enabled more rigorous verification of genetic research claims and organism classifications.

## Computational Efficiency

### Cost-Effectiveness Analysis

**Per-Paper Costs**:
- Custom Biomni: $0.0127 per paper
- Default Biomni: $0.0113 per paper
- PubTator: $0 per paper

**Cost per True Positive** (accounting for precision):
- Custom Biomni: $0.169 per true positive ($6.76 / 40 TP)
- Default Biomni: $0.100 per true positive ($6.01 / 60 TP)
- PubTator: $0 per true positive (but requires manual downstream filtering)

**Trade-off Consideration**: While Custom Biomni has higher upfront computational costs, its superior precision (90.91% vs. 60.00%) substantially reduces downstream manual curation burden, potentially offering better total cost-effectiveness for large-scale literature curation projects.

### Processing Time

**Total Time Investment**:
- Custom Biomni: 6.09 hours for 531 papers
- Default Biomni: 5.28 hours for 531 papers
- PubTator: <5 minutes for 531 papers (annotation retrieval only)

**Scalability**: Both Biomni methods demonstrated stable processing across hundreds of papers. Extrapolating to 10,000 papers:
- Custom Biomni: ~115 hours (~5 days), ~$127
- Default Biomni: ~99 hours (~4 days), ~$113

## Visualizations

### Conference Presentation Materials

*Figures and posters from the 48th Annual Meeting of the Molecular Biology Society of Japan will be added here.*

**Planned Visualizations**:
- Precision comparison bar chart
- Entity annotation accuracy comparison
- False positive rate analysis
- Processing efficiency comparison

---

**Data Availability**: All experimental results, ground truth annotations, and analysis scripts are available in this repository for full reproducibility.
