"""Versioned prompt templates for all NEXUS agents.

Each prompt is designed for structured JSON output,
is token-conscious, and includes clear instructions.
"""

SYSTEM_PROMPT = """You are NEXUS, an AI Research Scientist. You analyze academic literature with scientific rigor.
Rules:
- NEVER fabricate papers, authors, DOIs, or results
- Always distinguish fact from inference
- Mark uncertain information explicitly
- Use precise, scientific language
- If information is unavailable, say so clearly"""


PLANNER_V1 = """Analyze this research question and create a structured research plan.

RESEARCH QUESTION: {question}

Create a comprehensive research plan with:
1. A normalized, precise version of the question
2. Clear research objective
3. 5-8 specific subquestions that decompose the main question
4. Key concepts and entities mentioned
5. Methods of interest (algorithms, architectures, techniques)
6. Datasets of interest
7. Metrics of interest
8. 8-12 diverse search queries for academic databases (vary terminology, focus)
9. Synonyms for key terms
10. Related terminology
11. Required evidence types (empirical, theoretical, etc.)
12. Search strategy description
13. Expected research dimensions (what axes of comparison matter)

Be specific and thorough. The search queries should cover different aspects of the question."""


PAPER_EXTRACTION_V1 = """Analyze this academic paper and extract structured information.

TITLE: {title}
AUTHORS: {authors}
YEAR: {year}
VENUE: {venue}
ABSTRACT: {abstract}
{full_text_section}

Extract:
1. research_problem: What problem does this paper address?
2. research_question: What specific question does it investigate?
3. hypothesis: What hypothesis is tested (if any)?
4. main_findings: List of primary results/conclusions (3-5 items)
5. secondary_findings: Supporting or minor findings
6. limitations: Acknowledged limitations
7. assumptions: Key assumptions made
8. future_work: Suggested future research directions
9. code_availability: "available", "not_found", or "unclear"
10. dataset_availability: "available", "not_found", or "unclear"

Base your analysis ONLY on the provided text. Do NOT invent information.
If something is not mentioned, use null or empty list."""


CLAIM_EXTRACTION_V1 = """Extract atomic research claims from this paper.

TITLE: {title}
ABSTRACT: {abstract}
FINDINGS: {findings}

Extract specific, testable claims. For each claim provide:
1. statement: The claim in clear language (e.g., "Model X outperforms Model Y on metric Z")
2. conditions: List of conditions under which the claim holds (dataset, setting, etc.)
3. metric: The evaluation metric if applicable
4. evidence_value: Quantitative result if available (e.g., "RMSE: 0.081")
5. comparison_value: Comparison value if available (e.g., "baseline RMSE: 0.103")
6. confidence: "high", "medium", "low", or "uncertain"
7. source_section: Which part of the paper this comes from

Extract 3-8 claims per paper. Focus on the most significant, verifiable claims.
Do NOT fabricate quantitative values. If not explicitly stated, omit them."""


METHOD_EXTRACTION_V1 = """Extract the methodology pipeline from this paper.

TITLE: {title}
ABSTRACT: {abstract}
{methods_section}

Extract:
1. dataset: Primary dataset(s) used
2. preprocessing: Data preprocessing steps
3. feature_engineering: Feature engineering techniques
4. model_architecture: Name/type of model architecture
5. model_details: Architecture details (layers, dimensions, etc.)
6. training_procedure: How the model was trained
7. loss_function: Loss function used
8. optimizer: Optimizer used
9. baselines: Models compared against
10. metrics: Evaluation metrics
11. evaluation_protocol: How evaluation was conducted (cross-validation, train/test split, etc.)

Only include information explicitly stated in the paper."""


CONTRADICTION_ANALYSIS_V1 = """Analyze whether these two claims represent a genuine scientific contradiction.

CLAIM A:
Paper: {paper_a_title} ({paper_a_year})
Statement: {claim_a}
Conditions: {conditions_a}
Metric: {metric_a}
Evidence: {evidence_a}

CLAIM B:
Paper: {paper_b_title} ({paper_b_year})
Statement: {claim_b}
Conditions: {conditions_b}
Metric: {metric_b}
Evidence: {evidence_b}

Compare these claims considering:
1. Are they evaluating the same task?
2. Do they use the same datasets?
3. Do they use the same metrics?
4. Are the experimental conditions comparable?
5. Are the model configurations comparable?
6. Could different results be explained by methodological differences?

Classify the relationship as one of:
- "agreement": Claims support each other
- "apparent_contradiction": Seems contradictory at first glance
- "contextual_disagreement": Different results explained by different conditions
- "methodological_conflict": Different results due to different methodologies
- "direct_contradiction": Same conditions, opposite results
- "unresolved": Cannot determine from available information

Provide:
1. classification: One of the above categories
2. shared_conditions: Conditions both papers share
3. different_conditions: Conditions that differ
4. explanation: Why this classification (2-4 sentences)
5. confidence: "high", "medium", "low", or "uncertain" """


CONSENSUS_ANALYSIS_V1 = """Analyze the following claims from multiple papers and determine the consensus status.

RESEARCH QUESTION: {question}

CLAIMS AND EVIDENCE:
{claims_summary}

For each major finding or theme, determine:
1. statement: The finding being assessed
2. status: "consensus" (most papers agree), "uncertain" (limited evidence), "contested" (mixed findings), or "unresolved" (insufficient evidence)
3. supporting_papers: Which papers support this finding
4. dissenting_papers: Which papers disagree
5. confidence: "high", "medium", "low", or "uncertain"
6. explanation: Brief reasoning

Identify 4-8 key findings. Use scientific language. Do not overstate certainty."""


GAP_DETECTION_V1 = """Identify research gaps based on the analyzed literature.

RESEARCH QUESTION: {question}

PAPERS ANALYZED:
{papers_summary}

CLAIMS AND EVIDENCE:
{claims_summary}

CONTRADICTIONS:
{contradictions_summary}

METHODS USED:
{methods_summary}

DATASETS USED:
{datasets_summary}

Identify research gaps by looking for:
1. Repeated limitations across papers
2. Unanswered subquestions
3. Missing experimental conditions
4. Missing baseline comparisons
5. Underexplored method combinations
6. Lack of cross-domain evaluation
7. Reproducibility weaknesses
8. Inconsistent metrics across papers
9. Missing ablation studies

For each gap provide:
1. title: Short descriptive title
2. description: What the gap is
3. gap_type: "underexplored", "conflicting", "missing", or "methodological"
4. evidence: What evidence points to this gap
5. supporting_paper_ids: Papers that inform this gap observation
6. confidence: How confident this is a genuine gap
7. potential_direction: A possible research direction to address it
8. why_it_matters: Why this gap is significant

IMPORTANT: Say "based on retrieved literature" — do NOT claim absolute absence from all scientific literature.
Generate 3-6 gaps."""


NOVELTY_ANALYSIS_V1 = """Assess the novelty of a proposed research idea against existing literature.

PROPOSED IDEA: {idea}

EXISTING PAPERS:
{papers_summary}

EXISTING METHODS:
{methods_summary}

Analyze:
1. Which existing papers are most similar to this idea?
2. What methodological overlap exists?
3. What dimensions have already been explored?
4. What dimensions appear potentially unexplored?
5. How does this idea differ from the closest existing work?

Provide:
1. closest_papers: List of most similar paper IDs
2. methodological_overlap: List of methods already used in similar contexts
3. explored_dimensions: What has been done
4. potentially_unexplored: What appears new
5. assessment: "potentially_promising", "substantial_overlap", "unclear", or "likely_well_explored"
6. explanation: Detailed reasoning
7. warnings: Any caveats about this assessment

IMPORTANT: Scientific novelty cannot be proven from a finite corpus.
Use "potential novelty based on retrieved literature." Never claim "100% novel." """


EXPERIMENT_DESIGN_V1 = """Design a concrete experiment to investigate a research gap.

RESEARCH GAP: {gap}

EXISTING LITERATURE CONTEXT:
{context}

AVAILABLE METHODS: {methods}
AVAILABLE DATASETS: {datasets}
AVAILABLE METRICS: {metrics}

Design an experiment with:
1. hypothesis: Clear, testable hypothesis
2. research_objective: What the experiment aims to determine
3. datasets: Specific datasets to use
4. train_test_split: Data splitting strategy
5. experimental_variables: Independent and dependent variables
6. baseline_models: Models to compare against (from literature)
7. proposed_method: The proposed approach
8. evaluation_metrics: Metrics to use
9. ablation_studies: Components to ablate
10. statistical_tests: Statistical tests to validate results
11. expected_outcomes: What results would support/refute the hypothesis
12. failure_criteria: What would indicate the approach doesn't work
13. reproducibility_requirements: What's needed for reproducibility

This should read like a genuine research protocol."""


RED_TEAM_V1 = """You are a critical scientific reviewer. Challenge the following research conclusions.

RESEARCH CONCLUSIONS:
{conclusions}

SUPPORTING EVIDENCE:
{evidence}

Identify:
1. challenges: Specific challenges to the conclusions
2. weak_evidence: Evidence that is weak or insufficient
3. potential_biases: Possible biases in the analysis
4. missing_perspectives: Important perspectives not considered
5. overgeneralizations: Claims that overstate the evidence
6. final_confidence: "high", "medium", "low", or "uncertain" after review
7. adjudication: Final balanced assessment (3-5 sentences)

Be rigorous but fair. Flag genuine concerns, not pedantic issues.
The goal is to strengthen the research, not dismiss it."""


INTEGRITY_AUDIT_V1 = """Audit the research integrity of this analysis.

CLAIMS: {claims_count} total
CLAIMS WITH EVIDENCE: {evidence_count}
CITATIONS: {citations_data}
CONTRADICTIONS: {contradictions_data}
BIBLIOGRAPHY: {bibliography_data}

Check:
1. Are important claims cited?
2. Does each finding map to evidence?
3. Are citations consistent (title/author/DOI match)?
4. Are contradictions properly represented?
5. Are unsupported conclusions clearly marked?
6. Are recommendations grounded in evidence?
7. Are uncertainty levels present?
8. Are bibliographic fields complete?

Provide:
1. issues: List of specific issues found
2. warnings: List of warnings (non-critical)
3. overall_integrity: "passed", "warnings", or "failed" """

MISSING_EXPERIMENTS_V1 = """Analyze the identified gaps and contradictions to infer missing experimental combinations.

GAPS:
{gaps}

CONTRADICTIONS:
{contradictions}

Suggest missing experimental combinations (method, dataset, condition) that could address these gaps or resolve contradictions.
For each missing experiment provide:
1. method: The proposed method or model architecture
2. dataset: The target dataset
3. condition: Specific experimental condition
4. existing_coverage: Paper IDs that explore adjacent areas
5. explanation: Why this combination is needed

Generate 2-4 missing experiments."""
