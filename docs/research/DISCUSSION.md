# Discussion

## Overview

This study demonstrates that AI agent–based approaches, particularly when combined with database-aware reasoning, can substantially outperform existing automated literature annotation systems in constructing high-precision corpora of genetic research articles on non-model organisms. Custom Biomni achieved 90.91% precision, representing a 30.91 percentage point improvement over PubTator (60.00%) and a 10.91 percentage point improvement over Default Biomni (80.00%).

Beyond performance differences, our analysis reveals how agentic tool use, prompt design, and database coverage collectively shape the observed precision–recall trade-offs.

## Comparative Performance Analysis

### Why Custom Biomni Outperforms Other Methods

Three primary factors account for Custom Biomni’s superior precision.

#### 1. Enhanced Entity Linking via Database Integration

Custom Biomni integrates external biomedical databases through an MCP server, enabling real-time access to NCBI Gene and Taxonomy resources. This allows:

* **Gene validation** against official records and synonyms
* **Species verification** using authoritative taxonomy identifiers
* **Species–gene consistency checks** to confirm biological plausibility

**Impact**:
By autonomously querying MCP-connected databases during inference, Custom Biomni performs context-aware entity grounding rather than static post-processing. This agentic tool use enables disambiguation of gene and species mentions based on biological plausibility—for example, distinguishing biomarker proteins from genes or rejecting invalid gene–species associations. As a result, false positives arising from superficial or ambiguous co-mentions are substantially reduced.

**Contrast with PubTator**:
PubTator relies on pre-computed NER annotations and rule-based filtering, without the ability to dynamically verify whether a gene mention represents the focus of genetic investigation or merely incidental background information.

**Contrast with Default Biomni**:
Default Biomni can access some external databases, including NCBI Gene and Taxonomy, but such access is intermittent and not reliably integrated into the inference process, limiting consistent context-aware validation.

#### 2. Structured Output Generation

Custom Biomni employs structured output tools that incrementally persist validated annotations to external files. This provides:

* **Reliability**, preserving outputs even when agent execution is interrupted
* **Consistency**, through enforced output schemas
* **Auditability**, enabling traceability of agent decisions

By contrast, Default Biomni produced heterogeneous outputs requiring manual extraction from logs. Of 531 processed papers, only 387 yielded readily parseable outputs, increasing post-processing effort and reducing practical usability.

#### 3. Contextual Understanding via LLM Reasoning

Both Biomni variants leverage LLM-based reasoning to interpret document-level context, enabling:

* Identification of primary research intent
* Discrimination between genetic research and incidental gene mentions
* Iterative resolution of ambiguous cases

This capability explains why both Biomni variants eliminated entire classes of false positives that were frequent in PubTator outputs.

## False Positive Analysis

### Custom Biomni

Despite high precision, Custom Biomni produced four false positives, revealing two dominant error modes:

1. **Gene vs. gene product ambiguity**, where proteins, biomarkers, or peptide hormones were incorrectly treated as genetic research targets
2. **Model organism contamination**, particularly in multi-organism studies where human genes were expressed or discussed in non-model systems

These cases highlight semantic boundaries that remain challenging even for expert curators.

### Default Biomni

Default Biomni produced 15 false positives, reflecting broader and more systematic issues:

* Inclusion of papers with no substantive genetic content
* Insufficient filtering of model organisms
* Acceptance of tangential enzyme or gene mentions

These errors stem largely from overly inclusive classification criteria rather than misidentification of specific entities.

### PubTator

PubTator produced 22 false positives, dominated by two patterns:

1. **Human gene misclassification**, where papers primarily focused on human genetics but mentioned non-model organisms
2. **False gene annotations**, including biomarkers, metabolites, and non-genetic entities labeled as genes

These errors reflect fundamental limitations of entity-level annotation without document-level reasoning.

## False Negative Analysis

### Conservative Classification in Custom Biomni

Custom Biomni retrieved fewer papers overall (44) than Default Biomni (75), indicating reduced recall. This difference arises from two interacting factors.

First, the precision-oriented design introduces an inherent trade-off. More importantly, prompt design amplified this effect. The instruction to *always verify species–gene consistency using NCBI databases* imposed an overly strict constraint for non-model organisms, whose genes are often absent from curated databases. Consequently, legitimate genetic studies lacking registered NCBI Gene entries were systematically excluded.

Second, Custom Biomni applied a stricter interpretation of what constitutes “genetic research,” excluding borderline studies that Default Biomni retained. Some of these cases likely represent genuine classification ambiguities rather than clear errors.

### Implications

These findings indicate that Custom Biomni’s false negatives are driven not only by model limitations but also by design choices—particularly prompt constraints that do not fully account for incomplete database coverage in non-model organism research.

## Mechanistic Insights

### Why Database Integration Improves Precision

Database integration improves precision through synonym resolution, species–gene consistency checks, and increased confidence in established genetic entities. However, these benefits depend on database completeness—an assumption that does not hold uniformly for non-model organisms.

### Why LLM Reasoning Outperforms Traditional NER Pipelines

**PubTator’s Fundamental Constraint**:
PubTator employs dedicated machine learning–based NER models trained on curated biomedical corpora. These datasets could be biased toward human and other model organism genes, with limited representation of non-model organism genetics. As a result, performance degrades in non-model contexts, and annotations are often driven by string-level matches rather than research relevance.

More fundamentally, PubTator’s pipeline lacks document-level reasoning and cannot assess whether a recognized gene mention constitutes the focus of genetic investigation or merely incidental context. This limitation explains the high frequency of false positives observed in this study.

In contrast, LLM-based agents integrate entity recognition with contextual interpretation, enabling intent recognition and research-type classification that are critical for high-precision curation.

## Precision–Recall Trade-off and Design Implications

A clear trade-off emerges:

* **Custom Biomni**: Highest precision, lower recall due to strict validation requirements
* **Default Biomni**: Moderate precision with higher recall
* **PubTator**: Lowest precision, with recall dependent on annotation coverage

Optimal method selection therefore depends on use case, ranging from high-precision curation to exploratory literature discovery.

## Broader Implications

This study demonstrates that AI agent–based literature curation can approach manual-level precision while retaining scalability. At the same time, it highlights challenges specific to non-model organism research, particularly incomplete database coverage and ambiguous research boundaries.

Importantly, the observed limitations point to clear improvement pathways: relaxed validation prompts, expanded non-model organism gene databases, and more capable reasoning models. Together, these advances could plausibly push precision beyond 95% while improving recall.

## Conclusion

AI agent–based literature curation with database integration substantially outperforms existing automated systems for identifying genetic research on non-model organisms. While Custom Biomni achieves high precision, its limitations underscore the importance of prompt design and database coverage in shaping performance. Overall, this work establishes both the feasibility of agent-based curation and a concrete roadmap toward more comprehensive, high-precision literature organization across the tree of life.

---

# Supplementary Information

## Supplementary Note 1: Detailed False Positive Analysis

### S1.1 Custom Biomni False Positives (4 cases)

Despite achieving high precision, Custom Biomni produced four false positives, revealing specific edge-case error modes.

#### Case S1.1.1: PMID 39620069 — HIV–Human Evolutionary Study

**Description**: Evolutionary analysis of the HIV *gp120* gene in human populations.
**Error Type**: Model organism contamination.
**Explanation**: Although the agent correctly identified a gene-level study, it failed to exclude the paper due to primary involvement of a model organism (human). The presence of a non-model organism (HIV) led to misclassification.

#### Case S1.1.2: PMID 39624363 — Canine CRP Biomarker Review

**Description**: Review of C-reactive protein (CRP) as a disease biomarker in dogs.
**Error Type**: Gene vs. biomarker ambiguity.
**Explanation**: CRP is encoded by a gene, but the paper focused on protein-level clinical measurements rather than genetic investigation.

#### Case S1.1.3: PMID 39620500 — Cyanobacteria-Based Medical Applications

**Description**: Engineering cyanobacteria to express human genes for medical use.
**Error Type**: Species–gene misattribution.
**Explanation**: Human genes were incorrectly attributed to cyanobacteria, illustrating the difficulty of multi-organism genetic engineering contexts.

#### Case S1.1.4: PMID 39625374 — Canine Endocrinology

**Description**: Study of parathyroid hormone (PTH) in canine endocrine disorders.
**Error Type**: Gene vs. gene product ambiguity.
**Explanation**: The focus was physiological rather than genetic, despite the presence of gene-encoded peptides.

---

### S1.2 Common Error Patterns in Custom Biomni

Across these cases, two dominant error modes were observed:

1. **Confusion between genes and gene products** (biomarkers, hormones, peptides)
2. **Incomplete filtering of model organism involvement in multi-species studies**

These errors highlight semantic boundaries that remain challenging even for expert human curators.

---

## Supplementary Note 2: Default Biomni False Positive Breakdown (15 cases)

Default Biomni’s false positives exhibited more systematic classification issues.

### S2.1 No Genetic Content (6 cases)

Papers incorrectly classified as genetic research despite lacking gene-focused investigation, including methodological, ecological, or nutritional studies.

### S2.2 Model Organism Contamination (3 cases)

Studies primarily focused on recognized model organisms (e.g., *E. coli*, tobacco, humans) that were insufficiently filtered.

### S2.3 Ambiguous or Tangential Gene Mentions (2 cases)

Papers mentioning enzymes or genes incidentally within biochemical or cultivation contexts, without genetic analysis.

### S2.4 Other Cases (4 cases)

Remaining errors spanned multiple categories and reflected inconsistent application of classification criteria.

---

## Supplementary Note 3: PubTator False Positive Analysis (22 cases)

### S3.1 Human Gene Misclassification (10 cases)

Human genetics papers incorrectly retained due to incidental mentions of non-model organisms.

### S3.2 False Gene Annotations (10 cases)

Entities annotated as genes despite representing biomarkers, metabolites, or non-genetic concepts.

### S3.3 Irrelevant Papers (2 cases)

Papers lacking substantive biological research content but spuriously annotated.

---

## Supplementary Note 4: Comparative Error Statistics

| Error Type                   | PubTator | Default Biomni | Custom Biomni |
| ---------------------------- | -------- | -------------- | ------------- |
| No genetic content           | 2/22     | 6/15           | 0/4           |
| Model organism contamination | 10/22    | 3/15           | 2/4           |
| False gene annotations       | 10/22    | 0/15           | 0/4           |
| Gene vs. biomarker/peptide   | included | 2/15           | 2/4           |
| Species–gene misattribution  | 0/22     | 2/15           | 1/4           |

---

## Supplementary Note 5: False Negative Analysis

### S5.1 Papers Missed by Custom Biomni (26 cases)

#### S5.1.1 Missing NCBI Gene Entries

Many legitimate non-model organism genetic studies lacked registered NCBI Gene IDs, preventing database-based validation.

**Representative examples** include studies on insecticide resistance genes, bacterial functional genomics, and algal DNA repair genes.

#### S5.1.2 Classification Boundary Ambiguity

Several missed papers occupied gray zones between genetics, taxonomy, ecology, or physiology, where expert judgment may vary.

---

### S5.2 Papers Missed by Default Biomni (6 cases)

Papers retrieved exclusively by Custom Biomni included studies on plants, fungi, and some domesticated animals, suggesting that Default Biomni may have applied overly conservative filtering in specific contexts.

---

## Supplementary Note 6: Prompt Design Considerations

### S6.1 Over-Constraint in Custom Biomni

The instruction to *always verify species–gene consistency using NCBI databases* disproportionately penalized non-model organism research, where gene annotation coverage is incomplete by definition.

### S6.2 Prompt Simplification Hypothesis

Reducing prompt complexity may improve agent consistency by lowering cognitive load and allowing flexible reasoning when database evidence is unavailable.

---

## Supplementary Note 7: Implications for Future System Design

These supplementary analyses underscore that remaining errors arise primarily from semantic ambiguity, database incompleteness, and prompt design choices rather than fundamental model incapability. Addressing these factors represents a clear pathway toward further performance gains.

---