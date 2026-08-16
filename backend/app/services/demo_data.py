"""Demo data for NEXUS — synthetic research corpus for battery RUL prediction.

This provides a realistic research corpus designed to demonstrate:
- Agreement between papers
- Contextual disagreement
- Direct contradiction
- Research gaps
- Method comparison
- Citation relationships

ALL DATA IS SYNTHETIC / DEMO. Clearly labeled as demo.
"""
from backend.app.models.research import (
    Paper, Author, PaperAnalysis, Claim, Evidence, MethodPipeline,
    CitationEdge, Contradiction, ConsensusFinding, ResearchGap,
    MissingExperiment, ExperimentProposal, NoveltyAssessment,
    RedTeamResult, AuditResult, ResearchPlan, SearchResult,
    EvidenceConfidence, ContradictionType, ConsensusStatus,
    Availability, CitationRelation, AgentStatus
)


def get_demo_plan() -> ResearchPlan:
    return ResearchPlan(
        id="plan-demo-001",
        normalized_question="Are graph neural networks genuinely better than transformer-based models for battery remaining useful life (RUL) prediction under cross-domain conditions?",
        research_objective="Evaluate the comparative effectiveness of GNN-based and Transformer-based architectures for battery RUL prediction, with specific focus on cross-domain generalization.",
        subquestions=[
            "What methods currently dominate battery RUL prediction?",
            "How are graph neural networks applied to battery RUL estimation?",
            "How are transformer architectures applied to battery RUL estimation?",
            "What datasets are commonly used for battery RUL benchmarking?",
            "How is cross-domain or cross-chemistry transfer evaluated?",
            "What evaluation metrics are standard in this field?",
            "Are reported improvements statistically significant?",
            "What limitations are repeatedly reported across studies?",
            "Where do findings across papers disagree?"
        ],
        concepts=["battery degradation", "remaining useful life", "graph neural networks", "transformers", "domain adaptation", "transfer learning", "electrochemical impedance"],
        entities=["lithium-ion battery", "GNN", "GAT", "GCN", "Transformer", "LSTM", "GRU"],
        methods_of_interest=["Graph Attention Network", "Graph Convolutional Network", "Transformer", "LSTM", "GRU", "CNN-LSTM", "Transfer Learning", "Domain Adaptation"],
        datasets_of_interest=["NASA Battery Dataset", "CALCE Battery Dataset", "Oxford Battery Degradation", "MIT-Stanford Battery Dataset"],
        metrics_of_interest=["RMSE", "MAE", "MAPE", "R-squared", "Relative Error"],
        search_queries=[
            "graph neural network battery remaining useful life prediction",
            "transformer battery RUL estimation",
            "GNN vs LSTM battery degradation prediction",
            "cross-domain battery life prediction transfer learning",
            "battery capacity estimation deep learning comparison",
            "graph attention network electrochemical degradation",
            "attention mechanism battery prognostics",
            "domain adaptation battery state of health"
        ],
        synonyms={
            "RUL": ["remaining useful life", "end of life", "battery lifetime"],
            "GNN": ["graph neural network", "graph network", "graph-based model"],
            "domain shift": ["cross-domain", "transfer learning", "domain adaptation", "distribution shift"]
        },
        related_terms=["state of health", "capacity estimation", "cycle life", "degradation modeling", "prognostics and health management"],
        required_evidence_types=["empirical", "comparative", "ablation"],
        search_strategy="Multi-stage search: (1) broad GNN + battery RUL, (2) transformer + battery RUL, (3) cross-domain battery prediction, (4) method comparison studies, (5) limitation/challenge papers",
        expected_dimensions=["model architecture", "dataset", "prediction horizon", "cross-domain evaluation", "training data size", "battery chemistry"]
    )


def get_demo_papers() -> dict[str, Paper]:
    papers = {}

    p1 = Paper(
        id="demo-p001",
        title="Graph Attention Networks for Battery Remaining Useful Life Prediction",
        authors=[Author(name="Wei Zhang"), Author(name="Jian Li"), Author(name="Xiaoming Chen")],
        year=2024,
        venue="IEEE Transactions on Industrial Informatics",
        doi="10.1109/TII.2024.DEMO001",
        abstract="This paper proposes a Graph Attention Network (GAT) architecture for lithium-ion battery remaining useful life prediction. By representing battery degradation cycles as graph-structured data with attention-based aggregation, our model captures complex temporal and inter-cycle dependencies. Evaluated on the NASA battery dataset with NMC chemistry, the proposed GAT model achieves RMSE of 0.081 compared to LSTM baseline of 0.103 and GRU baseline of 0.095 for short-horizon predictions (30 cycles). Ablation studies demonstrate the importance of the attention mechanism and graph structure.",
        citation_count=45,
        source_provider="demo",
        is_demo=True, relevance_score=0.95, evidence_quality=0.9, research_score=0.92,
    )
    papers[p1.id] = p1

    p2 = Paper(
        id="demo-p002",
        title="Transformer-Based Sequential Modeling for Battery Degradation Forecasting",
        authors=[Author(name="Sarah Johnson"), Author(name="Michael Park")],
        year=2024,
        venue="Applied Energy",
        doi="10.1016/j.apenergy.2024.DEMO002",
        abstract="We present a Transformer architecture with custom positional encoding designed for battery degradation time-series forecasting. Unlike recurrent models, our approach captures long-range dependencies in capacity fade trajectories. On the CALCE dataset with LFP chemistry, the Transformer achieves MAE of 1.23% compared to LSTM (1.87%) and CNN-LSTM (1.56%) for long-horizon predictions (100+ cycles). However, the model requires substantially more training data and computational resources.",
        citation_count=38,
        source_provider="demo",
        is_demo=True, relevance_score=0.93, evidence_quality=0.88, research_score=0.90,
    )
    papers[p2.id] = p2

    p3 = Paper(
        id="demo-p003",
        title="LSTM Networks Outperform Graph Models for Battery RUL Under Limited Training Data",
        authors=[Author(name="Yuki Tanaka"), Author(name="Akira Sato")],
        year=2023,
        venue="Journal of Power Sources",
        doi="10.1016/j.jpowsour.2023.DEMO003",
        abstract="This study challenges the emerging trend of graph-based models for battery RUL prediction. Through extensive experiments on the CALCE dataset with various data regimes, we demonstrate that standard LSTM networks outperform both GCN and GAT architectures when training data is limited (fewer than 50 full charge-discharge cycles). The GNN models show higher variance and require careful hyperparameter tuning. We argue that the additional architectural complexity of graph models is not justified for single-cell scenarios with limited data.",
        citation_count=29,
        source_provider="demo",
        is_demo=True, relevance_score=0.91, evidence_quality=0.85, research_score=0.87,
    )
    papers[p3.id] = p3

    p4 = Paper(
        id="demo-p004",
        title="Cross-Chemistry Transfer Learning for Battery Health Estimation Using Domain Adaptation",
        authors=[Author(name="Maria Garcia"), Author(name="Thomas Müller"), Author(name="Liang Wu")],
        year=2025,
        venue="Nature Energy",
        doi="10.1038/s41560-2025-DEMO004",
        abstract="We investigate cross-chemistry transfer learning for battery state of health estimation. Our domain-adversarial approach enables models trained on NMC batteries to generalize to LFP chemistry with minimal fine-tuning. Using the combined NASA and CALCE datasets, we evaluate LSTM, Transformer, and GCN architectures under domain shift. Results show that all models degrade significantly under cross-chemistry conditions (15-40% increase in RMSE), but domain adaptation reduces this gap by 60%. Notably, the Transformer with domain adaptation achieves the best cross-domain performance. No model achieves satisfactory performance without any form of adaptation.",
        citation_count=12,
        source_provider="demo",
        is_demo=True, relevance_score=0.97, evidence_quality=0.92, research_score=0.95,
    )
    papers[p4.id] = p4

    p5 = Paper(
        id="demo-p005",
        title="A Comprehensive Benchmark of Deep Learning Methods for Battery Remaining Useful Life",
        authors=[Author(name="David Brown"), Author(name="Elena Petrov"), Author(name="Raj Patel")],
        year=2024,
        venue="Energy and AI",
        doi="10.1016/j.egyai.2024.DEMO005",
        abstract="This paper presents a systematic benchmarking study of deep learning approaches for battery RUL prediction. We evaluate 8 architectures (MLP, CNN, LSTM, GRU, CNN-LSTM, Transformer, GCN, GAT) across 4 datasets (NASA, CALCE, Oxford, MIT-Stanford) using consistent preprocessing and evaluation protocols. Key findings: (1) No single architecture dominates across all conditions; (2) Temporal models (LSTM, GRU) provide the most consistent baseline performance; (3) GNN models show promise but results vary significantly with graph construction method; (4) Transformer models excel with large training sets but underperform with limited data; (5) Reproducibility remains a major challenge — only 3 of 15 surveyed papers provide complete code.",
        citation_count=67,
        source_provider="demo",
        is_demo=True, relevance_score=0.96, evidence_quality=0.94, research_score=0.96,
    )
    papers[p5.id] = p5

    p6 = Paper(
        id="demo-p006",
        title="Graph Convolutional Networks with Uncertainty Estimation for Battery Degradation",
        authors=[Author(name="Chen Liu"), Author(name="Fei Wang")],
        year=2024,
        venue="Reliability Engineering & System Safety",
        doi="10.1016/j.ress.2024.DEMO006",
        abstract="We integrate Monte Carlo dropout-based uncertainty estimation into graph convolutional networks for battery degradation prediction. The model provides both point estimates and prediction intervals, enabling more informed decision-making for battery management systems. On the NASA dataset, our GCN with uncertainty achieves comparable RMSE (0.089) to GAT (0.084) while providing calibrated uncertainty bounds. The model correctly identifies high-uncertainty predictions near end-of-life transitions.",
        citation_count=18,
        source_provider="demo",
        is_demo=True, relevance_score=0.88, evidence_quality=0.86, research_score=0.85,
    )
    papers[p6.id] = p6

    p7 = Paper(
        id="demo-p007",
        title="Attention-Based Temporal Graph Networks for Multi-Cell Battery Pack RUL Prediction",
        authors=[Author(name="Hyun Kim"), Author(name="Jun Park"), Author(name="Soo Lee")],
        year=2025,
        venue="IEEE Transactions on Power Electronics",
        doi="10.1109/TPEL.2025.DEMO007",
        abstract="We extend graph-based approaches to multi-cell battery pack scenarios where inter-cell dependencies are naturally represented as graph structures. Our temporal graph attention network captures both within-cell degradation patterns and between-cell interactions. On a proprietary multi-cell dataset and the MIT-Stanford dataset, the TGAT achieves 12% lower RMSE than single-cell models and 8% lower than LSTM baselines. This work demonstrates that the graph structure advantage becomes most pronounced in multi-cell scenarios rather than single-cell predictions.",
        citation_count=8,
        source_provider="demo",
        is_demo=True, relevance_score=0.85, evidence_quality=0.80, research_score=0.82,
    )
    papers[p7.id] = p7

    p8 = Paper(
        id="demo-p008",
        title="Hybrid CNN-Transformer Architecture for Early Battery Life Prediction",
        authors=[Author(name="Anna Schmidt"), Author(name="Peter Olsen")],
        year=2025,
        venue="Journal of Energy Storage",
        doi="10.1016/j.est.2025.DEMO008",
        abstract="We propose a hybrid CNN-Transformer model that uses convolutional feature extraction followed by Transformer-based sequence modeling for early battery life prediction. Our approach predicts battery lifetime from the first 100 cycles with MAPE of 8.3% on the MIT-Stanford dataset, outperforming pure LSTM (MAPE 12.1%) and pure Transformer (MAPE 9.7%) models. The CNN front-end provides important inductive bias for local feature extraction that pure attention models lack. We provide open-source code and preprocessed datasets for reproducibility.",
        citation_count=5,
        source_provider="demo",
        is_demo=True, relevance_score=0.84, evidence_quality=0.82, research_score=0.81,
    )
    papers[p8.id] = p8

    return papers


def get_demo_analyses() -> dict[str, PaperAnalysis]:
    analyses = {}

    analyses["demo-p001"] = PaperAnalysis(
        paper_id="demo-p001",
        research_problem="Battery RUL prediction using standard sequential models fails to capture complex inter-cycle dependencies",
        research_question="Can graph attention networks improve battery RUL prediction by modeling degradation as graph-structured data?",
        hypothesis="GAT architecture with cycle-level graph construction captures degradation patterns better than sequential models",
        main_findings=[
            "GAT achieves RMSE of 0.081 vs LSTM baseline of 0.103 on NASA dataset",
            "Graph structure enables modeling of inter-cycle dependencies",
            "Attention mechanism identifies critical degradation transitions"
        ],
        secondary_findings=["Model trains in under 10 minutes on single GPU", "Graph construction method significantly affects performance"],
        limitations=["Only evaluated on NASA dataset (NMC chemistry)", "Short prediction horizon only (30 cycles)", "Single-cell scenario only"],
        assumptions=["Degradation patterns are representable as graph structures", "Adjacent cycles have meaningful relationships"],
        future_work=["Multi-chemistry evaluation", "Long-horizon prediction", "Multi-cell battery packs"],
        code_availability=Availability.NOT_FOUND,
        dataset_availability=Availability.AVAILABLE,
        methods=[
            MethodPipeline(
                paper_id="demo-p001",
                dataset="NASA Battery Dataset",
                preprocessing=["Capacity extraction per cycle", "Min-max normalization"],
                feature_engineering=["Cycle-to-cycle graph construction", "Voltage curve features"],
                model_architecture="Graph Attention Network",
                model_details="3-layer GAT with 64-dim hidden, 4 attention heads",
                training_procedure="Supervised, 200 epochs, early stopping",
                loss_function="MSE",
                optimizer="Adam",
                baselines=["LSTM", "GRU", "MLP"],
                metrics=["RMSE", "MAE", "R-squared"],
                evaluation_protocol="80/20 train/test split, 5-fold cross-validation"
            )
        ],
        claims=[
            Claim(id="claim-001", paper_id="demo-p001",
                  statement="GAT outperforms LSTM for battery RUL prediction",
                  conditions=["NASA dataset", "NMC chemistry", "short horizon (30 cycles)"],
                  metric="RMSE", evidence_value="0.081", comparison_value="0.103 (LSTM)",
                  confidence=EvidenceConfidence.HIGH, source_section="Results"),
            Claim(id="claim-002", paper_id="demo-p001",
                  statement="Graph structure captures inter-cycle degradation dependencies",
                  conditions=["NASA dataset"],
                  confidence=EvidenceConfidence.MEDIUM, source_section="Discussion"),
            Claim(id="claim-003", paper_id="demo-p001",
                  statement="Attention mechanism identifies critical degradation transitions",
                  conditions=["NASA dataset", "NMC chemistry"],
                  confidence=EvidenceConfidence.MEDIUM, source_section="Analysis"),
        ],
        evidence=[
            Evidence(id="ev-001", claim_id="claim-001", paper_id="demo-p001",
                     evidence_type="empirical", description="GAT RMSE 0.081 vs LSTM RMSE 0.103 on NASA dataset",
                     quantitative_value="0.081", metric="RMSE", dataset="NASA Battery Dataset",
                     conditions=["NMC chemistry", "30-cycle horizon"], confidence=EvidenceConfidence.HIGH),
        ],
    )

    analyses["demo-p002"] = PaperAnalysis(
        paper_id="demo-p002",
        research_problem="Recurrent models have limited ability to capture long-range dependencies in battery degradation",
        research_question="Can Transformer architectures capture long-range capacity fade patterns for RUL prediction?",
        hypothesis="Self-attention mechanism in Transformers can model long-range degradation dependencies better than LSTM",
        main_findings=[
            "Transformer achieves MAE of 1.23% vs LSTM 1.87% on CALCE dataset for long-horizon prediction",
            "Custom positional encoding improves performance for degradation time-series",
            "Transformer excels with sufficient training data (100+ cycles)"
        ],
        secondary_findings=["Requires 3x more training data than LSTM for convergence"],
        limitations=["High computational cost", "Requires large training datasets", "Only evaluated on LFP chemistry"],
        future_work=["Efficient attention mechanisms", "Few-shot learning", "Multi-chemistry evaluation"],
        code_availability=Availability.AVAILABLE,
        dataset_availability=Availability.AVAILABLE,
        methods=[
            MethodPipeline(
                paper_id="demo-p002",
                dataset="CALCE Battery Dataset",
                preprocessing=["Capacity extraction", "Z-score normalization", "Sliding window"],
                feature_engineering=["Custom positional encoding", "Voltage-capacity curves"],
                model_architecture="Transformer",
                model_details="6-layer Transformer, 128-dim, 8 heads",
                training_procedure="Supervised, 500 epochs, cosine annealing",
                loss_function="Huber Loss",
                optimizer="AdamW",
                baselines=["LSTM", "CNN-LSTM", "GRU"],
                metrics=["MAE", "MAPE", "R-squared"],
                evaluation_protocol="Rolling window evaluation, 70/15/15 split"
            )
        ],
        claims=[
            Claim(id="claim-004", paper_id="demo-p002",
                  statement="Transformer outperforms LSTM for long-horizon battery RUL prediction",
                  conditions=["CALCE dataset", "LFP chemistry", "long horizon (100+ cycles)"],
                  metric="MAE", evidence_value="1.23%", comparison_value="1.87% (LSTM)",
                  confidence=EvidenceConfidence.HIGH, source_section="Results"),
            Claim(id="claim-005", paper_id="demo-p002",
                  statement="Transformer requires substantially more training data than LSTM",
                  conditions=["CALCE dataset"],
                  confidence=EvidenceConfidence.HIGH, source_section="Discussion"),
        ],
        evidence=[
            Evidence(id="ev-002", claim_id="claim-004", paper_id="demo-p002",
                     evidence_type="empirical", description="Transformer MAE 1.23% vs LSTM MAE 1.87% on CALCE",
                     quantitative_value="1.23%", metric="MAE", dataset="CALCE Battery Dataset",
                     conditions=["LFP chemistry", "100+ cycle horizon"], confidence=EvidenceConfidence.HIGH),
        ],
    )

    analyses["demo-p003"] = PaperAnalysis(
        paper_id="demo-p003",
        research_problem="Graph-based models may be over-hyped for battery RUL — performance advantage unclear under limited data",
        research_question="Do graph neural networks actually outperform LSTM under realistic data constraints?",
        hypothesis="LSTM outperforms GNN models when training data is limited",
        main_findings=[
            "LSTM outperforms GCN and GAT with fewer than 50 training cycles",
            "GNN models show higher variance with limited data",
            "Graph model complexity is not justified for single-cell scenarios with limited data"
        ],
        limitations=["Only evaluated on CALCE dataset", "Single chemistry (LFP)", "Does not evaluate multi-cell scenarios"],
        future_work=["Evaluation with more data", "Multi-cell scenarios", "Cross-chemistry evaluation"],
        code_availability=Availability.AVAILABLE,
        dataset_availability=Availability.AVAILABLE,
        methods=[
            MethodPipeline(
                paper_id="demo-p003",
                dataset="CALCE Battery Dataset",
                preprocessing=["Capacity extraction", "Min-max normalization"],
                model_architecture="LSTM",
                baselines=["GCN", "GAT", "GRU"],
                metrics=["RMSE", "MAE"],
                evaluation_protocol="Multiple data regimes (10, 25, 50, 100 cycles)"
            )
        ],
        claims=[
            Claim(id="claim-006", paper_id="demo-p003",
                  statement="LSTM outperforms GNN models with limited training data",
                  conditions=["CALCE dataset", "LFP chemistry", "fewer than 50 cycles", "single cell"],
                  metric="RMSE", confidence=EvidenceConfidence.HIGH, source_section="Results"),
            Claim(id="claim-007", paper_id="demo-p003",
                  statement="GNN architectural complexity is not justified for single-cell battery RUL",
                  conditions=["limited data regime", "single cell"],
                  confidence=EvidenceConfidence.MEDIUM, source_section="Discussion"),
        ],
        evidence=[
            Evidence(id="ev-003", claim_id="claim-006", paper_id="demo-p003",
                     evidence_type="empirical", description="LSTM achieves 15-25% lower RMSE than GAT/GCN with <50 training cycles",
                     dataset="CALCE Battery Dataset", conditions=["LFP chemistry", "limited data"],
                     confidence=EvidenceConfidence.HIGH),
        ],
    )

    analyses["demo-p004"] = PaperAnalysis(
        paper_id="demo-p004",
        research_problem="Cross-chemistry generalization is a critical unsolved challenge for battery health models",
        research_question="How do different architectures perform under cross-chemistry domain shift?",
        hypothesis="Domain adaptation can significantly reduce cross-chemistry performance degradation",
        main_findings=[
            "All models degrade 15-40% under cross-chemistry conditions",
            "Domain adaptation reduces cross-domain gap by 60%",
            "Transformer with domain adaptation achieves best cross-domain performance",
            "No model achieves satisfactory performance without adaptation"
        ],
        limitations=["Only NMC→LFP transfer evaluated", "Requires target domain unlabeled data", "Computational overhead of adversarial training"],
        future_work=["Multi-chemistry transfer", "Zero-shot transfer", "Uncertainty quantification under domain shift"],
        code_availability=Availability.AVAILABLE,
        dataset_availability=Availability.AVAILABLE,
        methods=[
            MethodPipeline(
                paper_id="demo-p004",
                dataset="NASA + CALCE (combined)",
                preprocessing=["Capacity extraction", "Feature alignment", "Domain label annotation"],
                feature_engineering=["Domain-invariant features", "Chemistry-agnostic representations"],
                model_architecture="Domain-Adversarial Neural Network",
                baselines=["LSTM", "Transformer", "GCN", "LSTM+DA", "GCN+DA"],
                metrics=["RMSE", "MAE", "Domain transfer ratio"],
                evaluation_protocol="Train on NMC (NASA), test on LFP (CALCE)"
            )
        ],
        claims=[
            Claim(id="claim-008", paper_id="demo-p004",
                  statement="All models degrade significantly under cross-chemistry conditions",
                  conditions=["NMC to LFP transfer", "NASA to CALCE"],
                  metric="RMSE", evidence_value="15-40% increase",
                  confidence=EvidenceConfidence.HIGH, source_section="Results"),
            Claim(id="claim-009", paper_id="demo-p004",
                  statement="Transformer with domain adaptation achieves best cross-domain performance",
                  conditions=["NMC to LFP transfer", "with domain adaptation"],
                  confidence=EvidenceConfidence.HIGH, source_section="Results"),
            Claim(id="claim-010", paper_id="demo-p004",
                  statement="Domain adaptation reduces cross-chemistry performance gap by 60%",
                  conditions=["NMC to LFP transfer"],
                  confidence=EvidenceConfidence.HIGH, source_section="Results"),
        ],
        evidence=[
            Evidence(id="ev-004", claim_id="claim-008", paper_id="demo-p004",
                     evidence_type="empirical", description="15-40% RMSE increase across all models under cross-chemistry conditions",
                     dataset="NASA + CALCE", conditions=["NMC→LFP transfer"],
                     confidence=EvidenceConfidence.HIGH),
        ],
    )

    analyses["demo-p005"] = PaperAnalysis(
        paper_id="demo-p005",
        research_problem="Lack of systematic comparison across architectures, datasets, and conditions",
        research_question="Which deep learning architecture is most effective for battery RUL across diverse conditions?",
        main_findings=[
            "No single architecture dominates across all conditions",
            "LSTM and GRU provide most consistent baseline performance",
            "GNN results vary significantly with graph construction method",
            "Transformer excels with large training sets but underperforms with limited data",
            "Reproducibility is a major challenge — only 3/15 surveyed papers provide code"
        ],
        limitations=["Benchmark limited to 4 public datasets", "Graph construction not systematically explored"],
        code_availability=Availability.AVAILABLE,
        dataset_availability=Availability.AVAILABLE,
        methods=[
            MethodPipeline(
                paper_id="demo-p005",
                dataset="NASA, CALCE, Oxford, MIT-Stanford",
                model_architecture="Benchmark (8 architectures)",
                baselines=["MLP", "CNN", "LSTM", "GRU", "CNN-LSTM", "Transformer", "GCN", "GAT"],
                metrics=["RMSE", "MAE", "MAPE", "R-squared"],
                evaluation_protocol="Consistent preprocessing, 5-fold CV, statistical significance tests"
            )
        ],
        claims=[
            Claim(id="claim-011", paper_id="demo-p005",
                  statement="No single architecture dominates battery RUL prediction across all conditions",
                  conditions=["4 datasets", "consistent evaluation"],
                  confidence=EvidenceConfidence.HIGH, source_section="Conclusion"),
            Claim(id="claim-012", paper_id="demo-p005",
                  statement="LSTM and GRU provide the most consistent baseline performance",
                  conditions=["across 4 datasets"],
                  confidence=EvidenceConfidence.HIGH, source_section="Results"),
            Claim(id="claim-013", paper_id="demo-p005",
                  statement="Reproducibility is a major challenge in battery RUL research",
                  conditions=["survey of 15 papers"],
                  confidence=EvidenceConfidence.HIGH, source_section="Discussion"),
        ],
        evidence=[
            Evidence(id="ev-005", claim_id="claim-011", paper_id="demo-p005",
                     evidence_type="empirical", description="Systematic benchmark across 8 architectures and 4 datasets shows no universal winner",
                     dataset="NASA, CALCE, Oxford, MIT-Stanford",
                     confidence=EvidenceConfidence.HIGH),
        ],
    )

    # Abbreviated analyses for remaining papers
    analyses["demo-p006"] = PaperAnalysis(
        paper_id="demo-p006",
        research_problem="Lack of uncertainty quantification in battery RUL predictions",
        main_findings=["GCN with MC dropout provides calibrated uncertainty", "Comparable accuracy to GAT with uncertainty bounds"],
        limitations=["Only NASA dataset", "Computational overhead of MC sampling"],
        code_availability=Availability.NOT_FOUND,
        claims=[
            Claim(id="claim-014", paper_id="demo-p006",
                  statement="GCN with uncertainty estimation achieves comparable performance to GAT",
                  conditions=["NASA dataset", "NMC chemistry"],
                  metric="RMSE", evidence_value="0.089", comparison_value="0.084 (GAT)",
                  confidence=EvidenceConfidence.HIGH),
        ],
        evidence=[
            Evidence(id="ev-006", claim_id="claim-014", paper_id="demo-p006",
                     evidence_type="empirical", description="GCN RMSE 0.089 vs GAT RMSE 0.084 on NASA dataset",
                     quantitative_value="0.089", metric="RMSE", dataset="NASA Battery Dataset",
                     confidence=EvidenceConfidence.HIGH),
        ],
    )

    analyses["demo-p007"] = PaperAnalysis(
        paper_id="demo-p007",
        research_problem="Single-cell models miss inter-cell dependencies in battery packs",
        main_findings=["TGAT achieves 12% lower RMSE than single-cell models", "Graph advantage most pronounced in multi-cell scenarios"],
        limitations=["Proprietary multi-cell dataset", "Limited single-cell comparison"],
        claims=[
            Claim(id="claim-015", paper_id="demo-p007",
                  statement="Graph structure advantage is most pronounced in multi-cell battery pack scenarios",
                  conditions=["Multi-cell battery pack", "MIT-Stanford dataset"],
                  confidence=EvidenceConfidence.MEDIUM),
        ],
    )

    analyses["demo-p008"] = PaperAnalysis(
        paper_id="demo-p008",
        research_problem="Pure attention models lack inductive bias for local feature extraction from battery data",
        main_findings=["CNN-Transformer hybrid outperforms pure LSTM and Transformer", "CNN front-end provides important inductive bias"],
        code_availability=Availability.AVAILABLE,
        dataset_availability=Availability.AVAILABLE,
        claims=[
            Claim(id="claim-016", paper_id="demo-p008",
                  statement="CNN-Transformer hybrid outperforms pure Transformer and LSTM for early battery life prediction",
                  conditions=["MIT-Stanford dataset", "first 100 cycles"],
                  metric="MAPE", evidence_value="8.3%", comparison_value="12.1% (LSTM), 9.7% (Transformer)",
                  confidence=EvidenceConfidence.HIGH),
        ],
        evidence=[
            Evidence(id="ev-007", claim_id="claim-016", paper_id="demo-p008",
                     evidence_type="empirical", description="CNN-Transformer MAPE 8.3% vs LSTM 12.1% on MIT-Stanford",
                     quantitative_value="8.3%", metric="MAPE", dataset="MIT-Stanford",
                     confidence=EvidenceConfidence.HIGH),
        ],
    )

    return analyses


def get_demo_contradictions() -> list[Contradiction]:
    return [
        Contradiction(
            id="contra-001",
            claim_a_id="claim-001", claim_b_id="claim-006",
            paper_a_id="demo-p001", paper_b_id="demo-p003",
            paper_a_summary="Zhang et al. 2024 — GAT outperforms LSTM on NASA dataset",
            paper_b_summary="Tanaka & Sato 2023 — LSTM outperforms GNN with limited data on CALCE",
            claim_a_text="GAT outperforms LSTM for battery RUL prediction (RMSE 0.081 vs 0.103)",
            claim_b_text="LSTM outperforms GNN models with limited training data",
            shared_conditions=["Battery RUL prediction", "Deep learning comparison"],
            different_conditions=[
                "Dataset: NASA (Paper A) vs CALCE (Paper B)",
                "Chemistry: NMC vs LFP",
                "Prediction horizon: short (30 cycles) vs variable",
                "Training data: sufficient vs limited (<50 cycles)",
            ],
            classification=ContradictionType.CONTEXTUAL_DISAGREEMENT,
            explanation="These papers evaluate different datasets (NASA vs CALCE), different battery chemistries (NMC vs LFP), and critically different data availability regimes. Paper A uses sufficient training data while Paper B specifically evaluates limited-data scenarios. The apparent contradiction is likely explained by these contextual differences rather than being a direct methodological conflict.",
            confidence=EvidenceConfidence.HIGH,
        ),
        Contradiction(
            id="contra-002",
            claim_a_id="claim-001", claim_b_id="claim-011",
            paper_a_id="demo-p001", paper_b_id="demo-p005",
            paper_a_summary="Zhang et al. 2024 — GAT outperforms LSTM",
            paper_b_summary="Brown et al. 2024 — No single architecture dominates across all conditions",
            claim_a_text="GAT outperforms LSTM for battery RUL prediction",
            claim_b_text="No single architecture dominates battery RUL prediction across all conditions",
            shared_conditions=["Battery RUL prediction", "GAT and LSTM included"],
            different_conditions=[
                "Scope: single dataset (Paper A) vs 4 datasets (Paper B)",
                "Evaluation breadth: single condition vs systematic benchmark",
            ],
            classification=ContradictionType.APPARENT_CONTRADICTION,
            explanation="Paper A's claim is specific to NASA/NMC/short-horizon conditions, while Paper B's comprehensive benchmark shows architecture superiority is condition-dependent. The specific claim is not wrong, but generalizing it would be inappropriate based on the broader evidence.",
            confidence=EvidenceConfidence.HIGH,
        ),
        Contradiction(
            id="contra-003",
            claim_a_id="claim-004", claim_b_id="claim-012",
            paper_a_id="demo-p002", paper_b_id="demo-p005",
            paper_a_summary="Johnson & Park 2024 — Transformer outperforms LSTM for long-horizon prediction",
            paper_b_summary="Brown et al. 2024 — LSTM/GRU provide most consistent baseline",
            claim_a_text="Transformer outperforms LSTM for long-horizon battery RUL prediction",
            claim_b_text="LSTM and GRU provide the most consistent baseline performance",
            shared_conditions=["Battery RUL prediction", "LSTM and Transformer compared"],
            different_conditions=[
                "Focus: long-horizon only (Paper A) vs all conditions (Paper B)",
                "Metric emphasis: peak performance vs consistency"
            ],
            classification=ContradictionType.CONTEXTUAL_DISAGREEMENT,
            explanation="Paper A focuses specifically on long-horizon prediction where Transformers excel, while Paper B evaluates consistency across diverse conditions. Both findings can coexist: Transformers may peak higher for long horizons while LSTM provides more robust all-around performance.",
            confidence=EvidenceConfidence.HIGH,
        ),
        Contradiction(
            id="contra-004",
            claim_a_id="claim-007", claim_b_id="claim-015",
            paper_a_id="demo-p003", paper_b_id="demo-p007",
            paper_a_summary="Tanaka & Sato 2023 — GNN complexity not justified for single-cell",
            paper_b_summary="Kim et al. 2025 — Graph advantage pronounced in multi-cell scenarios",
            claim_a_text="GNN architectural complexity is not justified for single-cell battery RUL",
            claim_b_text="Graph structure advantage is most pronounced in multi-cell battery pack scenarios",
            shared_conditions=["GNN evaluation for battery RUL"],
            different_conditions=["Single-cell (Paper A) vs multi-cell (Paper B)"],
            classification=ContradictionType.AGREEMENT,
            explanation="These claims actually complement each other. Paper A argues GNNs don't help for single-cell scenarios, and Paper B demonstrates GNNs shine in multi-cell scenarios where inter-cell relationships provide natural graph structure. Together they suggest GNN value is context-dependent.",
            confidence=EvidenceConfidence.HIGH,
        ),
    ]


def get_demo_consensus() -> list[ConsensusFinding]:
    return [
        ConsensusFinding(
            id="cons-001",
            statement="Temporal information (cycle sequences) is important for battery RUL prediction",
            status=ConsensusStatus.CONSENSUS,
            supporting_paper_ids=["demo-p001", "demo-p002", "demo-p003", "demo-p005"],
            supporting_evidence=["All evaluated models incorporate temporal/sequential information"],
            confidence=EvidenceConfidence.HIGH,
            explanation="All reviewed papers use sequential or temporal models, confirming that degradation patterns are inherently temporal."
        ),
        ConsensusFinding(
            id="cons-002",
            statement="No single architecture universally dominates battery RUL prediction",
            status=ConsensusStatus.CONSENSUS,
            supporting_paper_ids=["demo-p003", "demo-p004", "demo-p005"],
            supporting_evidence=["Benchmark study across 4 datasets", "Different winners under different conditions"],
            confidence=EvidenceConfidence.HIGH,
            explanation="Multiple papers, especially the comprehensive benchmark (Brown et al. 2024), confirm that architecture superiority is condition-dependent."
        ),
        ConsensusFinding(
            id="cons-003",
            statement="GNN consistently outperforms LSTM for battery RUL prediction",
            status=ConsensusStatus.CONTESTED,
            supporting_paper_ids=["demo-p001", "demo-p006", "demo-p007"],
            dissenting_paper_ids=["demo-p003", "demo-p005"],
            confidence=EvidenceConfidence.MEDIUM,
            explanation="GNN shows advantages in specific conditions (sufficient data, multi-cell) but not universally. LSTM outperforms under limited data."
        ),
        ConsensusFinding(
            id="cons-004",
            statement="Cross-domain/cross-chemistry generalization remains a major challenge",
            status=ConsensusStatus.CONSENSUS,
            supporting_paper_ids=["demo-p004", "demo-p005"],
            confidence=EvidenceConfidence.HIGH,
            explanation="Garcia et al. 2025 shows 15-40% performance degradation under cross-chemistry conditions across all architectures."
        ),
        ConsensusFinding(
            id="cons-005",
            statement="Transformer models are the best architecture for battery RUL prediction",
            status=ConsensusStatus.CONTESTED,
            supporting_paper_ids=["demo-p002", "demo-p004"],
            dissenting_paper_ids=["demo-p003", "demo-p005"],
            confidence=EvidenceConfidence.MEDIUM,
            explanation="Transformers excel with large data and long horizons but require more data and compute. Not universally superior."
        ),
        ConsensusFinding(
            id="cons-006",
            statement="Reproducibility is a significant challenge in battery RUL research",
            status=ConsensusStatus.CONSENSUS,
            supporting_paper_ids=["demo-p005"],
            supporting_evidence=["Only 3/15 surveyed papers provide complete code"],
            confidence=EvidenceConfidence.HIGH,
            explanation="The benchmark study found that only 20% of surveyed papers provide sufficient artifacts for reproduction."
        ),
    ]


def get_demo_gaps() -> list[ResearchGap]:
    return [
        ResearchGap(
            id="gap-001",
            title="Cross-Chemistry Generalization of Graph Neural Networks",
            description="While GNNs show promise for battery RUL, almost all evaluations use single-chemistry datasets. Only one retrieved paper (Garcia et al. 2025) evaluates GNNs under cross-chemistry conditions, and it found significant degradation.",
            gap_type="underexplored",
            evidence=[
                "demo-p001 evaluates GAT only on NASA (NMC)",
                "demo-p006 evaluates GCN only on NASA (NMC)",
                "demo-p007 uses proprietary dataset",
                "demo-p004 evaluates GCN cross-domain but finds significant degradation",
                "No retrieved paper specifically designs GNNs for cross-chemistry robustness"
            ],
            supporting_paper_ids=["demo-p001", "demo-p004", "demo-p006"],
            confidence=EvidenceConfidence.HIGH,
            potential_direction="Design graph neural networks with chemistry-agnostic representations and evaluate on multiple chemistry transfers (NMC→LFP, LFP→NCA, etc.)",
            why_it_matters="If GNNs cannot generalize across chemistries, their practical utility for real-world battery management is limited."
        ),
        ResearchGap(
            id="gap-002",
            title="Uncertainty Quantification Under Domain Shift",
            description="Only one retrieved paper (Liu & Wang 2024) addresses uncertainty estimation for battery GNN models, and none evaluate uncertainty calibration under domain shift conditions.",
            gap_type="missing",
            evidence=[
                "demo-p006 introduces uncertainty for GCN but only on NASA dataset",
                "demo-p004 evaluates cross-domain but without uncertainty",
                "No retrieved paper combines uncertainty estimation with domain adaptation"
            ],
            supporting_paper_ids=["demo-p004", "demo-p006"],
            confidence=EvidenceConfidence.MEDIUM,
            potential_direction="Combine domain-adversarial training with uncertainty estimation to provide calibrated predictions under cross-chemistry conditions",
            why_it_matters="Battery management systems need reliable uncertainty bounds, especially when operating on new chemistries."
        ),
        ResearchGap(
            id="gap-003",
            title="Systematic Graph Construction Methodology for Battery Data",
            description="Multiple retrieved papers note that GNN performance varies significantly with graph construction method, yet no systematic study of graph construction strategies was found.",
            gap_type="methodological",
            evidence=[
                "demo-p005 notes GNN results vary with graph construction",
                "demo-p001 uses cycle-to-cycle graphs without comparing alternatives",
                "No retrieved paper systematically compares graph construction methods for battery data"
            ],
            supporting_paper_ids=["demo-p001", "demo-p005"],
            confidence=EvidenceConfidence.MEDIUM,
            potential_direction="Systematic comparison of graph construction methods (k-NN, threshold-based, temporal, physics-informed) for battery degradation data",
            why_it_matters="Graph construction may be the key factor determining GNN effectiveness — inconsistent methods make cross-paper comparison unreliable."
        ),
    ]


def get_demo_missing_experiments() -> list[MissingExperiment]:
    return [
        MissingExperiment(
            id="missing-001",
            method="Transformer",
            dataset="Oxford Battery Degradation",
            condition="standard evaluation",
            existing_coverage=["demo-p005"],
            explanation="No retrieved paper specifically evaluates Transformer architecture on the Oxford Battery Degradation dataset independently. The benchmark study includes it but individual focused evaluation appears missing."
        ),
        MissingExperiment(
            id="missing-002",
            method="GAT",
            dataset="MIT-Stanford Battery Dataset",
            condition="single-cell prediction",
            existing_coverage=["demo-p007"],
            explanation="GAT has been evaluated primarily on NASA dataset. MIT-Stanford evaluation found only in multi-cell TGAT context (Kim et al. 2025), not standard single-cell GAT."
        ),
        MissingExperiment(
            id="missing-003",
            method="GCN with uncertainty",
            dataset="CALCE Battery Dataset",
            condition="cross-chemistry transfer",
            existing_coverage=["demo-p004", "demo-p006"],
            explanation="GCN uncertainty (Liu & Wang 2024) evaluated only on NASA. Domain adaptation (Garcia et al. 2025) does not include uncertainty. Combination appears unexplored in retrieved literature."
        ),
    ]


def get_demo_experiment() -> ExperimentProposal:
    return ExperimentProposal(
        id="exp-demo-001",
        gap_id="gap-001",
        hypothesis="Graph neural networks with chemistry-agnostic graph construction and domain-adversarial training will achieve less than 10% RMSE degradation under cross-chemistry transfer, compared to 15-40% without adaptation.",
        research_objective="Evaluate whether GNN architectures can achieve robust cross-chemistry generalization for battery RUL prediction through domain-adaptive graph representations.",
        datasets=["NASA Battery Dataset (NMC)", "CALCE Battery Dataset (LFP)", "Oxford Battery Degradation (mixed)"],
        train_test_split="Train on source chemistry, validate on 10% target (unlabeled), test on held-out target chemistry. 3-fold cross-validation over chemistry pairs.",
        experimental_variables=["Battery chemistry (NMC, LFP, NCA)", "Graph construction method", "Domain adaptation strategy", "Training data availability"],
        baseline_models=["LSTM", "LSTM + Domain Adaptation", "GCN (no adaptation)", "GAT (no adaptation)", "Transformer + Domain Adaptation"],
        proposed_method="GAT with domain-adversarial training, chemistry-agnostic graph construction based on degradation pattern similarity rather than temporal adjacency",
        evaluation_metrics=["RMSE", "MAE", "MAPE", "Domain Transfer Ratio (target/source performance)", "Uncertainty calibration (PICP, MPIW)"],
        ablation_studies=[
            "Without graph structure (→ sequence model)",
            "Without attention mechanism (→ GCN)",
            "Without domain adaptation",
            "Without chemistry-agnostic features",
            "Different graph construction methods"
        ],
        statistical_tests=["Paired t-test for architecture comparisons", "Wilcoxon signed-rank test", "Bootstrap confidence intervals"],
        expected_outcomes=[
            "Domain-adaptive GAT reduces cross-chemistry RMSE gap to <10%",
            "Chemistry-agnostic graph construction outperforms temporal graphs under domain shift",
            "Uncertainty estimates remain calibrated under domain shift"
        ],
        failure_criteria=[
            "Cross-chemistry RMSE increase exceeds 20% even with adaptation",
            "LSTM + adaptation outperforms GAT + adaptation",
            "Graph structure provides no benefit over sequence models under domain shift"
        ],
        reproducibility_requirements=[
            "Open-source code on GitHub",
            "Preprocessed datasets with splits",
            "All hyperparameters documented",
            "Random seeds fixed and reported",
            "Training logs and model checkpoints",
            "Statistical significance tests with p-values"
        ]
    )


def get_demo_citations() -> list[CitationEdge]:
    return [
        CitationEdge(source_paper_id="demo-p003", target_paper_id="demo-p001", relation=CitationRelation.CHALLENGES, context="Challenges GAT superiority under limited data"),
        CitationEdge(source_paper_id="demo-p004", target_paper_id="demo-p001", relation=CitationRelation.EXTENDS, context="Extends GNN evaluation to cross-domain setting"),
        CitationEdge(source_paper_id="demo-p004", target_paper_id="demo-p002", relation=CitationRelation.COMPARES, context="Compares Transformer under domain shift"),
        CitationEdge(source_paper_id="demo-p005", target_paper_id="demo-p001", relation=CitationRelation.COMPARES, context="Includes GAT in benchmark"),
        CitationEdge(source_paper_id="demo-p005", target_paper_id="demo-p002", relation=CitationRelation.COMPARES, context="Includes Transformer in benchmark"),
        CitationEdge(source_paper_id="demo-p005", target_paper_id="demo-p003", relation=CitationRelation.CITES, context="References limited data findings"),
        CitationEdge(source_paper_id="demo-p006", target_paper_id="demo-p001", relation=CitationRelation.EXTENDS, context="Extends GNN approach with uncertainty"),
        CitationEdge(source_paper_id="demo-p007", target_paper_id="demo-p001", relation=CitationRelation.EXTENDS, context="Extends to multi-cell graph scenario"),
        CitationEdge(source_paper_id="demo-p007", target_paper_id="demo-p003", relation=CitationRelation.CHALLENGES, context="Shows graph advantage in multi-cell context"),
        CitationEdge(source_paper_id="demo-p008", target_paper_id="demo-p002", relation=CitationRelation.EXTENDS, context="Extends Transformer with CNN front-end"),
    ]


def get_demo_novelty() -> NoveltyAssessment:
    return NoveltyAssessment(
        id="novelty-demo-001",
        proposed_idea="GAT + domain adaptation + uncertainty estimation for battery RUL prediction under cross-chemistry conditions",
        closest_papers=["demo-p001", "demo-p004", "demo-p006"],
        semantic_similarity_scores={"demo-p004": 0.72, "demo-p006": 0.68, "demo-p001": 0.61},
        methodological_overlap=["GAT architecture", "domain adaptation", "battery RUL prediction"],
        explored_dimensions=["GAT for battery RUL (Paper 1)", "Domain adaptation for cross-chemistry (Paper 4)", "Uncertainty for battery GCN (Paper 6)"],
        potentially_unexplored=["Combined GAT + domain adaptation + uncertainty", "Chemistry-agnostic graph construction", "Calibrated uncertainty under domain shift"],
        assessment="potentially_promising",
        explanation="Individual components (GAT, domain adaptation, uncertainty estimation) have been explored separately in the retrieved literature, but their combination appears unexplored. Paper 4 evaluates domain adaptation with GCN but not GAT. Paper 6 adds uncertainty to GCN but not under domain shift. The three-way combination represents a potentially novel contribution based on the retrieved literature.",
        warnings=[
            "This assessment is based on 8 retrieved papers — the actual literature may contain relevant work not captured in this search",
            "The practical benefit of combining all three components is not guaranteed",
            "Implementation complexity is significantly higher than individual components"
        ]
    )


def get_demo_red_team() -> RedTeamResult:
    return RedTeamResult(
        id="rt-demo-001",
        conclusion_challenged="GNN-based architectures show promise for battery RUL prediction but performance is condition-dependent",
        challenges=[
            "The evidence for GNN superiority comes primarily from groups developing GNN methods — potential confirmation bias",
            "Most GNN evaluations use the same 1-2 datasets, limiting generalizability claims",
            "The benchmark study (Brown et al. 2024) suggests no architecture dominates, partially contradicting GNN-specific claims"
        ],
        weak_evidence=[
            "GNN advantage on NASA dataset shown by only 2 papers — limited independent replication",
            "Multi-cell GNN results (Kim et al. 2025) use partly proprietary data that cannot be verified"
        ],
        potential_biases=[
            "Publication bias — negative GNN results may be underreported",
            "Dataset overlap — multiple papers use NASA dataset, potentially inflating apparent consensus",
            "Methodology differences make cross-paper comparison difficult"
        ],
        missing_perspectives=[
            "No physics-informed or hybrid physics-ML approaches in the retrieved corpus",
            "No evaluation of computational cost vs. accuracy tradeoff",
            "No real-world deployment results"
        ],
        overgeneralizations=[
            "Claiming GAT 'outperforms LSTM' without specifying conditions overstates the evidence",
            "Reproducibility concerns weaken confidence in reported numerical improvements"
        ],
        final_confidence=EvidenceConfidence.MEDIUM,
        adjudication="The evidence suggests that GNN architectures have potential for battery RUL prediction, particularly in multi-cell and data-rich scenarios, but the claim of universal superiority is not supported by the retrieved literature. The most robust finding is that architecture choice should be condition-dependent. Cross-chemistry generalization remains an open challenge for all architectures, and reproducibility concerns limit confidence in specific numerical claims."
    )


def get_demo_audit() -> AuditResult:
    return AuditResult(
        id="audit-demo-001",
        total_claims=16,
        claims_with_evidence_links=14,
        unsupported_claims=2,
        identifiable_source_metadata=8,
        citations_total=8,
        contradictions_represented=True,
        bibliographic_metadata_complete=True,
        uncertainty_levels_present=True,
        issues=[
            "2 claims lack direct quantitative evidence (claims about attention mechanism and graph construction variability)",
        ],
        warnings=[
            "Demo mode: citations are synthetic and should not be used for real academic work",
            "Cross-chemistry evidence comes from a single paper — independent replication needed"
        ],
        overall_integrity="warnings"
    )
