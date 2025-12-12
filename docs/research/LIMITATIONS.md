# Limitations

## Current Scope

This study focused specifically on evaluating **precision** in identifying non-model organism genetics papers. While this metric is most critical for literature curation workflows, several important dimensions remain unexplored.

### Incomplete Evaluation Metrics

**Precision-Only Assessment**: We evaluated only precision, not recall, accuracy, or F1-score. This limitation arose from practical constraints:

- **Ground Truth Challenge**: Establishing comprehensive ground truth for 531 papers requires extensive expert manual curation
- **Time Constraints**: Manual evaluation of all 531 papers was not feasible within the project timeline
- **Focused Priorities**: Given that precision is the primary concern in curation workflows, we prioritized rigorous precision evaluation over comprehensive metric coverage

**Impact**: We cannot make definitive claims about how many relevant papers were missed (recall) or overall classification accuracy across the entire corpus. See [DISCUSSION.md](DISCUSSION.md) for preliminary false negative analysis based on retrieval overlap patterns.

### Entity-Level Annotation Quality

**Annotation Curation Limitations**: While manual curation focused on determining whether papers represented "non-model organism genetics research," entity-level validation (gene names, gene IDs, species names, species taxonomy IDs) was secondary:

- Entity annotations were verified but not with the same rigor as paper-level classifications
- Some ambiguity remains in entity-level ground truth
- Entity precision results should be interpreted as indicative rather than definitive

**Reported Entity Precision**: Gene and species annotation precision values (see [RESULTS.md](RESULTS.md)) represent best-effort evaluation but may contain annotation inconsistencies.

## Data Limitations

### Temporal Sampling Bias

**Three-Day Window**: Our corpus was sampled from December 1-3, 2024—a narrow 3-day window that introduces potential bias:

**Concerns**:
1. **Seasonal Bias**: Publication patterns may vary by time of year (conference cycles, journal issue schedules)
2. **Topic Clustering**: Related papers from the same research groups or projects may cluster temporally
3. **Statistical Validity**: A 3-day sample may not represent the broader population of biomedical literature

**Ideal Approach**: A 1-month sampling window (e.g., January 1-31, 2025) with random selection would provide more representative coverage and reduce temporal bias.

**Justification**: The 3-day window was selected for computational feasibility during initial method development. While not ideal, the consistency of applying all three methods to the identical corpus enables valid comparative evaluation.

### Limited Sample Size

**531-Paper Corpus**: While sufficient for initial method comparison, this corpus size limits:

- Statistical power for detecting smaller performance differences
- Coverage of rare genetics research subtypes
- Taxonomic diversity representation

**Broader Coverage Needed**: Larger corpora (e.g., 5,000-10,000 papers) would provide more robust evaluation, particularly for tail distributions of uncommon species and research types.

## Methodological Limitations

### Ground Truth Establishment Challenges

**Manual Curation Variability**: Determining "non-model organism genetics research" involves subjective judgment at classification boundaries:

- Papers investigating genetic markers for species identification
- Studies mentioning genes but focusing on ecological or physiological processes
- Research at the intersection of genetics and other domains

**Consistency Efforts**: To maximize consistency, a single expert curator (domain expert in genetics and bioinformatics) performed all evaluations. However, some inter-rater reliability uncertainty remains for edge cases.

**No Inter-Rater Reliability Assessment**: Due to resource constraints, we did not conduct formal inter-rater reliability studies with multiple independent curators. This represents a limitation in ground truth validation.

### Genetics Research Classification Framework

**Ad Hoc Six-Category System**: In the absence of standardized classification systems for non-model organism genetics research, we developed a six-category framework through iterative consultation (see [METHODS.md](METHODS.md)).

**Limitations**:
- Not validated against existing taxonomies
- Boundary cases may be classified inconsistently
- Some papers span multiple categories, complicating classification

**Mitigation**: The framework was applied consistently across all methods, ensuring fair comparison even if absolute classification validity has uncertainty.

### Database Coverage Constraints

**NCBI Gene Incompleteness for Non-Model Organisms**: Custom Biomni's advantage relies on NCBI Gene and Taxonomy database queries. However:

- Many non-model organism genes lack NCBI Gene entries
- Gene nomenclature is less standardized for non-model species
- This creates a paradox where our enhancement specifically disadvantages the target population (non-model organisms)

**Impact on Recall**: As discussed in [DISCUSSION.md](DISCUSSION.md), Custom Biomni's strict database validation requirement likely reduced recall by excluding papers discussing genes without database entries—even when the genetic research was legitimate.

**Irony**: The very problem motivating this research (incomplete annotation of non-model organisms) limits the effectiveness of database-validation approaches.

## Performance Limitations

### Computational Costs

**Scalability Considerations**:
- Custom Biomni: $6.76 for 531 papers (~$127 for 10,000 papers)
- Processing time: 6.09 hours for 531 papers (~5 days for 10,000 papers)

While acceptable for targeted curation projects, these costs may limit applicability to:
- Routine large-scale literature monitoring (e.g., daily PubMed updates)
- Resource-constrained research settings
- Real-time applications

**Cost-Benefit Context**: Whether these costs are justified depends on use case. For high-value curation (systematic reviews, curated databases), costs are reasonable. For exploratory screening, cheaper methods may be preferred despite lower precision.

### Processing Reliability

**Batch Processing Challenges**: Both Biomni variants required subprocess-based batch processing to avoid memory accumulation (see [METHODS.md](METHODS.md)).

**Implications**:
- More complex deployment architecture
- Potential for batch-level failures requiring restart
- Engineering overhead for production systems

**Mitigation**: Structured output tools in Custom Biomni ensured data persistence across batch boundaries, reducing risk of data loss.

### Model Version Dependency

**GPT-4.1-mini Specificity**: Results are specific to GPT-4.1-mini as of late 2024.

**Concerns**:
- Model updates may change performance unpredictably
- Reproducibility requires version pinning
- Cost structures may change

**Generalization Uncertainty**: Performance with other LLMs (Claude, Gemini, open-source models) remains unknown.

## Generalizability

### Domain Specificity

**Non-Model Organism Genetics Focus**: This study evaluated methods specifically for non-model organism genetics literature. Generalization to other domains remains uncertain:

**Unknown Transferability**:
- Model organism genetics (where database coverage is comprehensive)
- Other biological subfields (ecology, evolution, structural biology)
- Biomedical literature outside genetics (clinical studies, drug development)
- Non-biological scientific domains

**Hypothesis**: Custom Biomni's advantage derives partly from enhanced entity linking via NCBI databases. Domains with comparable structured knowledge bases (UniProt for proteins, ChEMBL for compounds, etc.) may benefit similarly, but validation is needed.

### Temporal Validity

**Snapshot Evaluation**: This study represents a snapshot of AI agent capabilities in late 2024.

**LLM Performance Evolution**: Rapid advances in LLM technology mean:
- Error modes identified here may be resolved in next-generation models
- New error modes may emerge
- Cost-performance trade-offs will shift

**Benchmark Stability**: Periodic re-evaluation will be necessary to track performance evolution and maintain benchmark relevance.

### Prompt Sensitivity

**Custom Prompt Design**: Custom Biomni performance depends on specific prompt engineering choices.

**Concerns**:
- Small prompt variations may yield different performance
- Prompt optimization was informal, not systematic
- Optimal prompts may differ for other corpora or domains

**Need for Systematic Prompt Engineering**: Future work should explore prompt variants through rigorous A/B testing on held-out validation sets.

## Comparison Limitations

### PubTator Baseline Constraints

**Free, Pre-Computed Annotations**: PubTator represents a specific type of baseline:
- Zero computational cost to users
- Annotations computed once, queried many times
- No opportunity for customization or refinement

**Unfair Comparison Dimensions**:
- Biomni agents incur per-paper costs; PubTator amortizes costs across all users
- Biomni agents use 2024 LLMs; PubTator uses older NER models
- Biomni agents are customizable; PubTator is fixed

**Justification**: Despite these differences, PubTator represents the **current state-of-the-art for available, scalable automated annotation**, making it the appropriate baseline for practical comparison.

### Default Biomni Definition

**"Default" Configuration**: We defined "Default Biomni" as the standard Biomni framework without custom database integration.

**Limitations**:
- Biomni offers many configuration options; our "default" may not match others' choices
- Prompt design for Default Biomni was not independently optimized
- Performance might improve with different default settings

**Mitigation**: Both Biomni variants used similar base configurations and prompts, differing primarily in MCP server integration, enabling fair attribution of performance differences to the custom enhancements.

## Future Work

### Comprehensive Evaluation Metrics

**Planned Extensions**:

1. **Recall and F1-Score Evaluation**:
   - Establish complete ground truth for subset of corpus (e.g., 200-500 randomly sampled papers)
   - Calculate recall, accuracy, and F1-scores for all three methods
   - Quantify precision-recall trade-offs with PR curves

2. **Larger Corpus Evaluation**:
   - Expand to 5,000-10,000 papers from extended timeframe (e.g., 1-month window)
   - Use stratified random sampling to ensure representative coverage
   - Evaluate performance across different research subtypes and taxonomic groups

3. **Cross-Domain Validation**:
   - Test methods on model organism genetics literature
   - Evaluate on other biological subfields
   - Assess transferability to non-biological domains

### Methodological Improvements

**1. Sampling Strategy**:
- **Recommended Approach**: Sample papers from 1-month period (e.g., January 2025) using stratified random selection
- **Rationale**: Reduces temporal bias and improves population representativeness
- **Implementation**: Stratify by journal, research area, or publication date to ensure diverse coverage

**2. Inter-Rater Reliability**:
- **Multiple Expert Curators**: Recruit 2-3 independent domain experts
- **Calculate Agreement Metrics**: Cohen's kappa, Fleiss' kappa, or similar
- **Adjudication Process**: Resolve disagreements through discussion or third-party arbitration
- **Document Ambiguity**: Identify and characterize papers with low inter-rater agreement

**3. Prompt Optimization**:
- **Systematic A/B Testing**: Evaluate multiple prompt variants on held-out validation set
- **Specific Revisions**:
  - Relax strict gene ID validation requirement for non-model organisms
  - Simplify overall prompt complexity
  - Add explicit biomarker vs. gene research distinction
- **Optimization Metrics**: Balance precision, recall, and cost across prompt variants

**4. Model Selection**:
- **Frontier Models**: Evaluate GPT-5-pro, Claude Opus, Gemini Pro, and other state-of-the-art models
- **Cost-Performance Frontier**: Map out precision vs. cost trade-offs across models
- **Open-Source Alternatives**: Test Llama 3, Mistral, and other open models for cost-sensitive applications
- **Domain-Specific Fine-Tuning**: Explore fine-tuned models specialized for biomedical literature

### Benchmark Development

**Standardized Evaluation Framework**:

1. **Create Public Benchmark**:
   - Release annotated corpus with ground truth classifications
   - Include challenging edge cases and ambiguous examples
   - Establish standardized evaluation protocols (precision, recall, F1, entity-level metrics)
   - Enable reproducible comparison of future methods

2. **Longitudinal Tracking**:
   - Re-evaluate methods as new LLM generations emerge
   - Track performance improvements and cost evolution over time
   - Document error mode changes across model generations
   - Maintain version-controlled benchmark results

3. **Expansion to Related Tasks**:
   - Extend to other organism types (model organisms, specific taxonomic groups)
   - Cover additional genetics subtypes (population genetics, evolutionary genetics, etc.)
   - Develop multi-domain benchmark suite spanning biological subfields
   - Enable cross-domain transfer learning research

### Practical Applications

**Scaling to Production**:

**Requirements for Production Deployment**:
- Precision >95% (to minimize manual review burden)
- Recall >80% (to ensure comprehensive coverage)
- Cost <$0.05 per paper (for economic feasibility at scale)
- Processing time <10 seconds per paper (for near-real-time applications)

**Potential Applications** (once performance thresholds are met):
- Integration with PubMed update streams for real-time curation
- Species- and gene-level literature monitoring for research communities
- Automated feeding of curated databases (e.g., model organism databases, gene ontology)
- Personalized literature recommendation for researchers

**Current Status**: At 90.91% precision with unclear recall and $0.0127 per paper, Custom Biomni is approaching but has not yet met production-ready thresholds.

### Impact and Vision

**Transformative Potential**: Continued development of AI agent-based curation could enable:

1. **Comprehensive Non-Model Organism Literature Mapping**: Automated identification of genetic research across the full taxonomic tree of life
2. **Gene-Level Literature Organization**: Precise, species-specific literature curation for every characterized gene
3. **Real-Time Knowledge Synthesis**: Dynamic integration of new findings into structured biological knowledge bases
4. **Democratized Access**: Enabling small research groups and non-model organism communities to maintain curated literature resources

**Performance Trajectory**: Clear progression from PubTator (60%) → Default Biomni (80%) → Custom Biomni (90.91%) suggests continued improvement is feasible.

**Timeline Estimate**: With focused effort on prompt optimization, model upgrades, and expanded databases, production-ready performance (>95% precision, >80% recall) may be achievable within 1-2 years.

---

**Acknowledgment of Constraints**: This study represents an initial investigation into AI agent-based literature curation for non-model organisms. The limitations described here are characteristic of exploratory research and provide clear directions for subsequent work. We have prioritized transparency about methodological constraints to facilitate accurate interpretation of results and guide future studies.

**Methodological Rigor**: Despite these limitations, our study design ensures valid comparative evaluation: all three methods were applied to an identical corpus using consistent evaluation criteria. The observed performance differences are therefore attributable to methodological variations rather than corpus or evaluation artifacts.
