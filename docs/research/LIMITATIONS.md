# Limitations

## Scope and Evaluation Metrics

This study focused on evaluating **precision** in constructing a corpus of genetic research articles on non-model organisms, reflecting the primary requirement of high-precision literature curation workflows. Other performance metrics, including recall, accuracy, and F1-score, were not comprehensively assessed.

This limitation was driven by practical constraints. Establishing complete ground truth for all 531 papers would require extensive expert manual curation, which was not feasible within the project timeline. Consequently, we prioritized rigorous precision evaluation over broader metric coverage. As a result, we cannot make definitive claims regarding recall or overall classification accuracy, although preliminary insights into false negatives are discussed based on retrieval overlap patterns.

## Entity-Level Annotation Limitations

Manual curation primarily targeted paper-level classification (i.e., whether a paper constitutes non-model organism genetics research). While gene and species annotations were reviewed, entity-level validation was not performed with equivalent rigor. Some ambiguity therefore remains in the ground truth for entity annotations, and reported entity-level precision values should be interpreted as indicative rather than definitive.

## Data Limitations

### Temporal Sampling Bias

The corpus was sampled from a narrow three-day window (December 1–3, 2024), introducing potential temporal bias. Publication patterns may vary seasonally, and related studies may cluster temporally. While a longer sampling window would provide more representative coverage, the selected window enabled computationally feasible method development. Importantly, all methods were evaluated on the identical corpus, preserving the validity of comparative analysis.

### Sample Size

The 531-paper corpus was sufficient for initial method comparison but limits statistical power, coverage of rare research subtypes, and taxonomic diversity. Larger-scale evaluations would be necessary to assess performance robustness, particularly for uncommon species and niche research areas.

## Methodological Limitations

### Ground Truth Ambiguity

Classifying “non-model organism genetics research” involves subjective judgment, particularly for studies at the boundary between genetics and related domains (e.g., ecology or physiology). To ensure internal consistency, all evaluations were conducted by a single domain expert. However, formal inter-rater reliability assessment was not performed, which limits confidence in edge-case classifications.

### Classification Framework

In the absence of established taxonomies for non-model organism genetics research, we developed an ad hoc six-category classification framework. While applied consistently across all methods, this framework has not been externally validated, and boundary cases may be inconsistently categorized.

### Database Coverage Constraints

Custom Biomni relies on NCBI Gene and Taxonomy databases for validation. However, gene annotation for non-model organisms is often incomplete, creating a structural limitation. Strict database-based validation may therefore exclude legitimate genetic studies lacking registered gene entries, contributing to reduced recall. This paradox highlights how incomplete annotation of non-model organisms—one of the motivations for this study—also constrains database-driven approaches.

## Performance and Practical Limitations

Custom Biomni required higher computational cost and processing time than baseline method. While acceptable for targeted, high-value curation tasks, these costs may limit applicability to large-scale or real-time monitoring. Batch-based processing further introduces engineering complexity, although structured output mechanisms mitigated data loss risks.

Results are also model-specific, reflecting performance of GPT-4.1-mini at the time of evaluation. Performance, cost, and error characteristics may change with future model updates or alternative LLMs.

## Generalizability

This study is specific to non-model organism genetics literature. Generalization to other biological domains, model organism research, or non-biological fields remains untested. Moreover, the evaluation represents a snapshot of AI capabilities in 2025; rapid advances in LLM technology may alter both performance and limitations over time.

Custom Biomni’s performance is also sensitive to prompt design. Prompt optimization was not systematic, and small prompt variations may lead to different outcomes, limiting reproducibility.

## Comparison Constraints

PubTator represents a free, pre-computed annotation baseline with no customization or per-query cost, whereas Biomni agents required computational cost and leverage modern LLMs. Despite these structural differences, PubTator remains the most practical large-scale automated baseline and therefore an appropriate comparator.

“Default Biomni” was defined as Biomni without custom database integration. Alternative default configurations or prompt designs may yield different results, although both Biomni variants shared similar base settings to enable fair comparison.

## Summary

These limitations reflect the exploratory nature of this study and highlight key challenges in automated curation for non-model organism genetics, including incomplete databases, subjective classification boundaries, and precision–recall trade-offs. While these constraints limit generalization and recall assessment, they also delineate clear directions for future methodological refinement and large-scale validation.



---

## Supplementary Note : Extended Limitations and Context

This supplementary note provides methodological details and extended context for the limitations briefly described in the main text. It is intended to support transparency and reproducibility without duplicating the main discussion.

---

## S1. Evaluation Scope

### Precision-Centered Design

Evaluation focused exclusively on precision, reflecting the primary requirement of literature curation workflows. Comprehensive recall estimation was infeasible due to the lack of complete ground truth for the full 531-paper corpus. Preliminary insights into false negatives were derived from retrieval overlap patterns but are not quantitatively reported.

### Entity-Level Annotation Uncertainty

Manual curation prioritized paper-level classification. Gene and species annotations were reviewed but not exhaustively curated, particularly for non-model organisms with inconsistent nomenclature. Reported entity-level precision should therefore be interpreted as indicative.

---

## S2. Data and Sampling Constraints

### Temporal Window

The corpus was sampled from a three-day publication window (December 1–3, 2024), which may introduce temporal bias and topic clustering. The window was chosen for computational feasibility, and all methods were evaluated on the identical corpus, preserving valid relative comparison.

### Corpus Size

The 531-paper corpus is sufficient to detect large performance differences but limits statistical power and taxonomic coverage. Larger, temporally diverse corpora are needed for robust evaluation.

---

## S3. Methodological Considerations

### Ground Truth Subjectivity

Classification of non-model organism genetics research involves subjective boundary cases (e.g., genetic markers vs. genetics-focused studies). All annotations were performed by a single expert curator, and no formal inter-rater reliability analysis was conducted.

### Classification Framework

A six-category, ad hoc classification framework was developed in the absence of standardized taxonomies. While consistently applied, it has not been externally validated and may be ambiguous for multi-category papers.

### Database Coverage Paradox

Custom Biomni relies on NCBI Gene and Taxonomy validation, which is incomplete for non-model organisms. This improves precision but likely reduces recall by excluding legitimate studies lacking database support.

---

## S4. Computational and Generalization Limits

### Cost and Reliability

Custom Biomni incurs higher computational cost and requires batch-based processing, increasing engineering complexity. These constraints may limit applicability to large-scale or real-time monitoring.

### Model and Prompt Dependency

Results are specific to GPT-4.1-mini and to the chosen prompt design. Model updates or prompt variations may alter performance, and transferability to other domains remains untested.

---

### Supplementary Summary

These limitations reflect structural challenges in non-model organism literature and early-stage AI agent development. While they constrain absolute performance claims, they do not affect the validity of comparative conclusions, which are based on consistent evaluation across identical corpora.

---
