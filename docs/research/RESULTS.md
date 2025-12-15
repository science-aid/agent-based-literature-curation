# Results

## Overview

We compared three approaches for constructing a high-precision corpus of genetic research articles on non-model organisms using a pre-filtered set of 531 articles. All methods were applied to the same input corpus to ensure a direct and fair comparison. Evaluation focused on **precision**, reflecting the primary requirement of literature curation workflows, where minimizing false positives is critical due to the substantial downstream costs of manual review.

---

## Performance Comparison

### Overall Precision and Retrieval Characteristics

Table 1 summarizes the performance of the three approaches. **Custom Biomni achieved the highest precision (90.91%)**, outperforming Default Biomni (80.00%) and PubTator (60.00%).

| Metric                       | Default Biomni | Custom Biomni | PubTator |
| ---------------------------- | -------------- | ------------- | -------- |
| Input corpus size            | 531            | 531           | 531      |
| Papers retrieved             | 75             | 44            | 55       |
| **Precision**                | 80.00%         | **90.91%**    | 60.00%   |
| Gene annotation precision    | 59.72%         | **71.11%**    | 38.97%   |
| Species annotation precision | 63.98%         | **83.33%**    | 65.55%   |

A clear **retrieval volume–precision trade-off** was observed. Default Biomni retrieved the largest number of papers but at lower precision, whereas Custom Biomni retrieved fewer papers while maintaining substantially higher precision. PubTator showed intermediate retrieval volume but the lowest precision overall.

---

### Entity Annotation Performance

Custom Biomni consistently outperformed the other methods in both gene and species annotation precision. In particular, **gene annotation precision for PubTator was markedly low (38.97%)**, substantially lagging behind both Biomni variants. This gap was less pronounced for species annotations, where PubTator performed comparably to Default Biomni.

These results support our hypothesis that **gene annotation for non-model organisms remains a major limitation of existing automated annotation systems**, whereas species recognition is relatively robust.

---

## Error Analysis

### False Positives

Analysis of false positives revealed distinct error modes across methods:

* **PubTator** frequently admitted papers with generic or incidental gene mentions, contamination from model organism–centric studies, or non-genetic research falsely flagged by gene annotations.
* **Default Biomni** errors were primarily due to overgeneralization and insufficient contextual discrimination between primary research focus and background mentions.
* **Custom Biomni** produced the fewest false positives, mostly limited to edge cases involving complex multi-organism studies or borderline definitions of genetics research.

The reduction in false positives for Custom Biomni can be attributed to its integration of external validation using NCBI Gene and Taxonomy resources.

---

## Computational Efficiency

### Cost and Time Considerations

Both Biomni approaches required modest computational resources. Custom Biomni incurred slightly higher cost and processing time than Default Biomni, reflecting its additional validation steps.

| Method         | Total time | Total cost | Cost per true positive |
| -------------- | ---------- | ---------- | ---------------------- |
| Custom Biomni  | 6.09 h     | $6.76      | $0.169                 |
| Default Biomni | 5.28 h     | $6.01      | $0.100                 |
| PubTator       | <5 min     | $0         | $0*                    |

* PubTator requires substantial downstream manual filtering due to lower precision.

Although Custom Biomni is more expensive per retrieved paper, its higher precision substantially reduces downstream curation effort, suggesting better overall cost-effectiveness for large-scale literature curation.

---

## Scalability

Both Biomni methods demonstrated stable performance across the evaluated corpus. Extrapolation to larger datasets (e.g., 10,000 articles) suggests feasible runtimes (approximately 4–5 days) and moderate costs, supporting practical scalability for large literature collections.

---

## Summary of Key Findings

1. **Custom Biomni achieved the highest precision (90.91%)**, substantially reducing false positives.
2. PubTator exhibited **particularly weak gene annotation performance** for non-model organisms.
3. Higher precision corresponded to lower retrieval volume, highlighting an inherent trade-off.
4. Improved annotation precision translated into meaningful reductions in downstream curation cost.
5. AI agent–based approaches with database-aware validation offer a promising direction for high-precision literature curation in understudied biological domains.

