/**
 * Complete TypeScript Type Definitions for NEXUS Research Intelligence
 * Directly aligned with backend Pydantic models in backend/app/models/research.py
 */

export type SessionStatus =
  | 'idle'
  | 'planning'
  | 'discovering'
  | 'ranking'
  | 'analyzing'
  | 'extracting_evidence'
  | 'building_graph'
  | 'analyzing_contradictions'
  | 'synthesizing_consensus'
  | 'detecting_gaps'
  | 'analyzing_dead_ends'
  | 'checking_reproducibility'
  | 'analyzing_novelty'
  | 'designing_experiment'
  | 'red_team'
  | 'auditing'
  | 'synthesizing'
  | 'report_ready'
  | 'completed_with_warnings'
  | 'error'
  | 'paused';

export type EvidenceConfidence = 'high' | 'medium' | 'low' | 'uncertain' | 'insufficient';

export type ContradictionType =
  | 'agreement'
  | 'apparent_contradiction'
  | 'contextual_disagreement'
  | 'methodological_conflict'
  | 'metric_disagreement'
  | 'scope_disagreement'
  | 'direct_contradiction'
  | 'method_variation'
  | 'insufficient_information'
  | 'unresolved';

export type ConsensusStatus =
  | 'supported'
  | 'likely_supported'
  | 'consensus'
  | 'mixed'
  | 'contested'
  | 'uncertain'
  | 'unresolved'
  | 'insufficient_evidence';

export type Availability =
  | 'available'
  | 'partial'
  | 'not_found'
  | 'unavailable'
  | 'unclear'
  | 'unknown';

export type DeadEndStatus =
  | 'failed'
  | 'limited'
  | 'non_generalizing'
  | 'superseded'
  | 'unresolved'
  | 'promising_but_undertested'
  | 'conditional_failure'
  | 'weak_under_specific_conditions'
  | 'repeatedly_underperforming'
  | 'reproducibility_failure'
  | 'insufficient_evidence';

export type NoveltyLevel =
  | 'novel'
  | 'potentially_novel'
  | 'incremental'
  | 'overlapping'
  | 'already_explored'
  | 'insufficient_evidence';

export type RedTeamSeverity = 'critical' | 'high' | 'medium' | 'low' | 'info';

export type RedTeamFindingType =
  | 'unsupported_claim'
  | 'citation_misuse'
  | 'cherry_picking'
  | 'hidden_assumption'
  | 'dataset_bias'
  | 'publication_bias'
  | 'survivorship_bias'
  | 'duplicated_evidence'
  | 'citation_echo'
  | 'contextual_mismatch'
  | 'overgeneralization'
  | 'weak_baseline'
  | 'evaluation_leakage'
  | 'contradictory_evidence_ignored'
  | 'insufficient_sample'
  | 'reproducibility_weakness'
  | 'false_novelty'
  | 'speculative_as_fact';

export type ClaimPropagationType =
  | 'preserved'
  | 'weakened'
  | 'strengthened'
  | 'generalized'
  | 'specialized'
  | 'context_shifted'
  | 'contradicted'
  | 'unsupported_extension';

export type PaperContentStatus =
  | 'METADATA_ONLY'
  | 'ABSTRACT_ONLY'
  | 'FULL_TEXT'
  | 'FULL_TEXT_PARTIAL'
  | 'FULL_TEXT_FAILED';

export interface Author {
  name: string;
  affiliation?: string;
  orcid?: string;
}

export interface Paper {
  id: string;
  title: string;
  authors: Author[];
  year?: number;
  venue?: string;
  doi?: string;
  url?: string;
  abstract?: string;
  citation_count?: number;
  source_provider?: string;
  source_ids?: Record<string, string>;
  full_text_available?: boolean;
  content_status?: PaperContentStatus;
  pdf_url?: string;
  open_access?: boolean;
  oa_status?: string;
  sections?: Record<string, string>;
  page_count?: number;
  text_length?: number;
  extraction_status?: string;
  retrieval_failure_reason?: string;
  relevance_score?: number;
  evidence_quality?: number;
  research_score?: number;
  score_components?: Record<string, number>;
  is_demo?: boolean;
  retrieved_at?: string;
  metadata_quality?: number;
  created_at?: string;
}

export interface EvidenceStrength {
  directness: number;
  source_quality: number;
  methodological_rigor: number;
  reproducibility: number;
  external_validity: number;
  cross_study_consistency: number;
  scope_alignment: number;
  overall_assessment: EvidenceConfidence;
  rationale?: string;
  composite_score?: number;
}

export interface Claim {
  id: string;
  paper_id: string;
  statement: string;
  conditions: string[];
  metric?: string;
  evidence_value?: string;
  comparison_value?: string;
  confidence: EvidenceConfidence;
  strength?: EvidenceStrength;
  composite_score?: number;
  source_section?: string;
  source_page?: number;
  status?: string;
}

export interface Evidence {
  id: string;
  claim_id: string;
  paper_id: string;
  evidence_type: string;
  description: string;
  quantitative_value?: string;
  metric?: string;
  dataset?: string;
  conditions: string[];
  confidence: EvidenceConfidence;
  strength?: EvidenceStrength;
  source_location?: string;
}

export interface ClaimPropagation {
  id: string;
  source_claim_id: string;
  derived_claim_id: string;
  source_paper_id: string;
  derived_paper_id: string;
  relationship_type: ClaimPropagationType;
  source_conditions: string[];
  derived_conditions: string[];
  evidence_strength: EvidenceConfidence;
  scope_change: string;
  confidence: EvidenceConfidence;
  explanation: string;
}

export interface CitationEchoCluster {
  id: string;
  claim_statement: string;
  originating_paper_id: string;
  originating_paper_title: string;
  echo_paper_ids: string[];
  total_support_count: number;
  independent_support_count: number;
  citation_dependency_depth: number;
  echo_chain: string[];
  independence_weight: number;
  explanation: string;
}

export interface MethodPipeline {
  id: string;
  paper_id: string;
  dataset?: string;
  preprocessing: string[];
  feature_engineering: string[];
  model_architecture?: string;
  model_details?: string;
  training_procedure?: string;
  loss_function?: string;
  optimizer?: string;
  baselines: string[];
  metrics: string[];
  evaluation_protocol?: string;
}

export interface PaperAnalysis {
  id: string;
  paper_id: string;
  research_problem?: string;
  research_question?: string;
  hypothesis?: string;
  main_findings: string[];
  secondary_findings: string[];
  limitations: string[];
  assumptions: string[];
  future_work: string[];
  code_availability: Availability;
  dataset_availability: Availability;
  reproducibility_indicators: Record<string, any>;
  methods: MethodPipeline[];
  claims: Claim[];
  evidence: Evidence[];
}

export interface CitationEdge {
  source_paper_id: string;
  target_paper_id: string;
  relation: string;
  context?: string;
  is_inferred: boolean;
}

export interface Contradiction {
  id: string;
  claim_a_id: string;
  claim_b_id: string;
  paper_a_id: string;
  paper_b_id: string;
  paper_a_summary: string;
  paper_b_summary: string;
  claim_a_text: string;
  claim_b_text: string;
  shared_conditions: string[];
  different_conditions: string[];
  difference_dimensions: string[];
  classification: ContradictionType;
  explanation: string;
  confidence: EvidenceConfidence;
  severity: string;
  resolution_status: string;
  can_coexist?: boolean;
  coexistence_conditions?: string;
}

export interface ConsensusFinding {
  id: string;
  statement: string;
  status: ConsensusStatus;
  supporting_paper_ids: string[];
  supporting_evidence: string[];
  dissenting_paper_ids: string[];
  confidence: EvidenceConfidence;
  explanation: string;
  independence_weight: number;
  independent_support_count: number;
  evidence_quality_weighted: boolean;
}

export interface DeadEnd {
  id: string;
  approach: string;
  description: string;
  supporting_papers: string[];
  failure_evidence: string[];
  failure_conditions: string[];
  task?: string;
  dataset?: string;
  metric?: string;
  failure_reason?: string;
  attempt_count?: number;
  success_conditions_if_any?: string[];
  confidence: EvidenceConfidence;
  status: DeadEndStatus;
  alternative_directions: string[];
}

export interface ReproducibilityBlocker {
  category: string;
  severity: string;
  affected_component: string;
  evidence: string;
  recommended_remediation: string;
}

export interface ReproducibilityProfile {
  id: string;
  paper_id: string;
  dataset_available: Availability;
  data_preprocessing_documented: Availability;
  code_available: Availability;
  model_specification_documented: Availability;
  hyperparameters_documented: Availability;
  training_procedure_documented: Availability;
  random_seeds_reported: Availability;
  evaluation_metrics_defined: Availability;
  baselines_reproducible: Availability;
  statistical_reporting: Availability;
  hardware_environment_documented: Availability;
  external_validation: Availability;
  experimental_protocol_documented: Availability;
  completeness_score: number;
  missing_components: string[];
  blockers: ReproducibilityBlocker[];
  risk_factors: string[];
  replication_risks: string[];
  explanation: string;
}

export interface ResearchGap {
  id: string;
  title: string;
  description: string;
  gap_type: string;
  gap_dimension?: string;
  evidence: string[];
  supporting_paper_ids: string[];
  missing_dimension?: string;
  affected_literature?: string[];
  confidence: EvidenceConfidence;
  importance: string;
  novelty_potential: string;
  feasibility: string;
  potential_direction?: string;
  why_it_matters?: string;
}

export interface MissingExperiment {
  id: string;
  method: string;
  dataset: string;
  condition?: string;
  existing_coverage: string[];
  explanation: string;
}

export interface NoveltyAssessment {
  id: string;
  proposed_idea: string;
  closest_papers: string[];
  semantic_similarity_scores: Record<string, number>;
  methodological_overlap: string[];
  dataset_overlap: string[];
  evaluation_overlap: string[];
  explored_dimensions: string[];
  potentially_unexplored: string[];
  assessment: string;
  novelty_level: NoveltyLevel;
  explanation: string;
  warnings: string[];
  supporting_literature: string[];
}

export interface ExperimentProposal {
  id: string;
  gap_id?: string;
  dead_end_ids: string[];
  hypothesis: string;
  research_question?: string;
  research_objective: string;
  independent_variables: string[];
  dependent_variables: string[];
  control_variables: string[];
  datasets: string[];
  train_test_split?: string;
  experimental_variables: string[];
  baseline_models: string[];
  proposed_method: string;
  evaluation_metrics: string[];
  ablation_studies: string[];
  statistical_tests: string[];
  sample_size_guidance?: string;
  cross_validation_strategy?: string;
  expected_outcomes: string[];
  failure_criteria: string[];
  success_criteria: string[];
  reproducibility_requirements: string[];
  expected_risks: string[];
  alternative_interpretations: string[];
  addresses_gap?: string;
  motivated_by_evidence: string[];
  avoids_dead_ends: string[];
}

export interface RedTeamFinding {
  id: string;
  severity: RedTeamSeverity;
  finding_type: RedTeamFindingType;
  description: string;
  evidence_refs: string[];
  affected_claims: string[];
  recommended_correction: string;
}

export interface RedTeamResult {
  id: string;
  conclusion_challenged: string;
  challenges: string[];
  findings: RedTeamFinding[];
  weak_evidence: string[];
  potential_biases: string[];
  missing_perspectives: string[];
  overgeneralizations: string[];
  final_confidence: EvidenceConfidence;
  adjudication: string;
}

export interface IntegrityFinding {
  check_name: string;
  passed: boolean;
  details: string;
  affected_ids: string[];
}

export interface AuditResult {
  id?: string;
  total_claims: number;
  claims_with_evidence_links: number;
  unsupported_claims: number;
  identifiable_source_metadata: number;
  citations_total: number;
  contradictions_represented?: boolean;
  bibliographic_metadata_complete: boolean;
  uncertainty_levels_present?: boolean;
  integrity_findings?: IntegrityFinding[];
  issues?: string[];
  warnings?: string[];
  overall_integrity: string;
  verdict?: string;
}

export interface AgentEvent {
  id: string;
  session_id: string;
  agent_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  message: string;
  detail?: string;
  progress?: number;
  started_at?: string;
  completed_at?: string;
  duration_ms?: number;
  error?: string;
  token_usage?: number;
  retry_count?: number;
}

export interface ResearchPlan {
  id: string;
  normalized_question: string;
  research_objective: string;
  subquestions: string[];
  concepts: string[];
  entities: string[];
  methods_of_interest: string[];
  datasets_of_interest: string[];
  metrics_of_interest: string[];
  search_queries: string[];
  synonyms: Record<string, string[]>;
  related_terms: string[];
  required_evidence_types: string[];
  search_strategy: string;
  expected_dimensions: string[];
}

export interface ResearchSession {
  id: string;
  title: string;
  question: string;
  status: SessionStatus;
  created_at: string;
  updated_at: string;
  plan?: ResearchPlan;
  papers: Record<string, Paper>;
  analyses: Record<string, PaperAnalysis>;
  claims: Claim[];
  evidence: Evidence[];
  methods: MethodPipeline[];
  citations: CitationEdge[];
  claim_propagations: ClaimPropagation[];
  citation_echoes: CitationEchoCluster[];
  contradictions: Contradiction[];
  consensus: ConsensusFinding[];
  dead_ends: DeadEnd[];
  reproducibility_profiles: Record<string, ReproducibilityProfile>;
  gaps: ResearchGap[];
  missing_experiments: MissingExperiment[];
  novelty?: NoveltyAssessment;
  experiment?: ExperimentProposal;
  red_team?: RedTeamResult;
  audit?: AuditResult;
  agent_events: AgentEvent[];
  stats: Record<string, number>;
  stage_results: Record<string, string>;
  quality_state: string;
  quality_warnings: string[];
  is_demo: boolean;
  iteration_count?: number;
}

export interface WhyEvidenceChainItem {
  claim: string;
  evidence: string;
  source_paper_id: string;
  source_paper_title: string;
  source_location?: string;
  doi_or_url?: string;
  confidence: EvidenceConfidence;
}

export interface WhyExplanation {
  id: string;
  target_type: string;
  target_id: string;
  target_statement: string;
  confidence: EvidenceConfidence;
  evidence_chain: WhyEvidenceChainItem[];
  reasoning_factors: string[];
  uncertainty_analysis: string;
  conflicting_evidence: string[];
  counter_hypotheses: string[];
}

export interface TimelineMilestone {
  year: number | string;
  paradigm: string;
  title: string;
  description: string;
  paper_ids: string[];
  key_methods: string[];
  breakthrough_indicator: boolean;
}

export interface GraphNode {
  id: string;
  node_type: 'PAPER' | 'CLAIM' | 'EVIDENCE' | 'METHOD' | 'DATASET' | 'GAP' | 'DEAD_END' | 'EXPERIMENT';
  label: string;
  metadata: Record<string, any>;
}

export interface GraphEdge {
  source_id: string;
  target_id: string;
  edge_type: string;
  weight: number;
  metadata: Record<string, any>;
}

export interface ResearchGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
  clusters: Record<string, string[]>;
}

export type PageId =
  | 'home'
  | 'overview'
  | 'literature'
  | 'evidence'
  | 'methods'
  | 'contradictions'
  | 'consensus'
  | 'gaps'
  | 'novelty'
  | 'experiment'
  | 'redteam'
  | 'integrity'
  | 'graph'
  | 'timeline'
  | 'dossier';
