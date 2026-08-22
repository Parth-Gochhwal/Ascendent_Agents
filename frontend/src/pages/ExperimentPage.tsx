import { useState, useEffect } from 'react';
import { FlaskConical, Download, AlertOctagon, Sliders, Database, Cpu, BarChart2 } from 'lucide-react';
import type { ExperimentProposal, ResearchSession } from '../types/research';
import { api } from '../services/api';
import { EmptyState } from '../components/common/EmptyState';

interface ExperimentPageProps {
  sessionId: string;
  session: ResearchSession | null;
}

export function ExperimentPage({ sessionId, session }: ExperimentPageProps) {
  const [experiment, setExperiment] = useState<ExperimentProposal | null>(null);

  useEffect(() => {
    api.getExperiment(sessionId)
      .then((d: { experiment: ExperimentProposal | null }) => setExperiment(d.experiment))
      .catch(() => {});
  }, [sessionId, session?.status]);

  const exportProtocolMarkdown = () => {
    if (!experiment) return;
    const md = `# NEXUS Scientific Experiment Protocol\n\n## 1. Primary Hypothesis\n${experiment.hypothesis}\n\n## 2. Research Objective\n${experiment.research_objective}\n\n## 3. Benchmark Datasets\n${experiment.datasets?.map((d: string) => `- ${d}`).join('\n')}\n\n## 4. Baseline Models\n${experiment.baseline_models?.map((b: string) => `- ${b}`).join('\n')}\n\n## 5. Proposed Method\n${experiment.proposed_method}\n\n## 6. Evaluation Metrics\n${experiment.evaluation_metrics?.map((m: string) => `- ${m}`).join('\n')}\n\n## 7. Ablation Studies\n${experiment.ablation_studies?.map((a: string) => `- ${a}`).join('\n')}\n\n## 8. Statistical Falsification Criteria\n${experiment.failure_criteria?.map((f: string) => `- ${f}`).join('\n')}\n`;
    const blob = new Blob([md], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `NEXUS_Experiment_Protocol_${sessionId.slice(0, 6)}.md`;
    a.click();
  };

  if (!experiment) {
    return (
      <div className="workspace-content animate-fade-in">
        <EmptyState
          icon={<FlaskConical size={24} />}
          title="Synthesizing Experiment Protocol"
          description="Autonomous experiment designer synthesizes hypotheses, baseline models, statistical falsification criteria, and ablation studies from literature gaps."
        />
      </div>
    );
  }

  return (
    <div className="workspace-content animate-fade-in">
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--space-5)' }}>
        <div>
          <div className="card-section-label">AUTONOMOUS EXPERIMENTAL PROTOCOL DESIGNER</div>
          <h1 style={{ fontFamily: 'var(--font-serif)', fontSize: '1.75rem' }}>
            Laboratory Experiment Protocol
          </h1>
          <p style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>
            Rigorous pre-registration protocol designed directly from literature gaps and validated baselines
          </p>
        </div>

        <button className="action-btn-primary" onClick={exportProtocolMarkdown}>
          <Download size={13} />
          <span>Export Protocol (.md)</span>
        </button>
      </div>

      {/* Primary Hypothesis Card */}
      <div className="editorial-card highlight-steel" style={{ marginBottom: 'var(--space-4)' }}>
        <div className="card-section-label">PRIMARY TESTABLE HYPOTHESIS</div>
        <h2 style={{ fontFamily: 'var(--font-serif)', fontSize: '1.35rem', color: 'var(--text-primary)', margin: '6px 0 10px', lineHeight: 1.4 }}>
          "{experiment.hypothesis}"
        </h2>
        <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
          <strong>Objective:</strong> {experiment.research_objective}
        </div>
      </div>

      {/* 2-Column Experimental Specification Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 'var(--space-4)', marginBottom: 'var(--space-4)' }}>
        {/* Datasets */}
        <div className="editorial-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
            <Database size={14} color="var(--accent-steel)" />
            <span className="card-section-label" style={{ margin: 0 }}>BENCHMARK DATASETS</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {experiment.datasets?.map((d: string, i: number) => (
              <div key={i} style={{ fontSize: 13, color: 'var(--text-primary)', display: 'flex', gap: 8 }}>
                <span style={{ color: 'var(--accent-steel)' }}>•</span>
                <span>{d}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Baseline Comparison Models */}
        <div className="editorial-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
            <Cpu size={14} color="var(--accent-indigo)" />
            <span className="card-section-label" style={{ margin: 0 }}>BASELINE MODELS</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {experiment.baseline_models?.map((b: string, i: number) => (
              <div key={i} style={{ fontSize: 13, color: 'var(--text-primary)', display: 'flex', gap: 8 }}>
                <span style={{ color: 'var(--accent-indigo)' }}>•</span>
                <span>{b}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Evaluation Metrics */}
        <div className="editorial-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
            <BarChart2 size={14} color="var(--accent-teal)" />
            <span className="card-section-label" style={{ margin: 0 }}>EVALUATION METRICS</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {experiment.evaluation_metrics?.map((m: string, i: number) => (
              <div key={i} style={{ fontSize: 13, color: 'var(--text-primary)', display: 'flex', gap: 8 }}>
                <span style={{ color: 'var(--accent-teal)' }}>•</span>
                <span>{m}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Ablation Studies */}
        <div className="editorial-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
            <Sliders size={14} color="var(--accent-amber)" />
            <span className="card-section-label" style={{ margin: 0 }}>PLANNED ABLATION STUDIES</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {experiment.ablation_studies?.map((a: string, i: number) => (
              <div key={i} style={{ fontSize: 13, color: 'var(--text-primary)', display: 'flex', gap: 8 }}>
                <span style={{ color: 'var(--accent-amber)' }}>•</span>
                <span>{a}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Proposed Architecture & Protocol */}
      {experiment.proposed_method && (
        <div className="editorial-card highlight-indigo" style={{ marginBottom: 'var(--space-4)' }}>
          <div className="card-section-label">PROPOSED METHOD & ARCHITECTURE EXECUTION PROTOCOL</div>
          <p style={{ fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.65, marginTop: 8 }}>
            {experiment.proposed_method}
          </p>
        </div>
      )}

      {/* Statistical Falsification Criteria */}
      {experiment.failure_criteria && experiment.failure_criteria.length > 0 && (
        <div className="editorial-card highlight-crimson">
          <div className="card-section-label">FALSIFICATION & FAILURE CRITERIA</div>
          <p style={{ fontSize: 12, color: 'var(--text-tertiary)', marginBottom: 8 }}>
            Conditions under which the hypothesis must be formally rejected:
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {experiment.failure_criteria.map((fc: string, i: number) => (
              <div key={i} style={{ fontSize: 13, color: 'var(--text-primary)', display: 'flex', gap: 8 }}>
                <AlertOctagon size={14} color="var(--accent-crimson)" style={{ flexShrink: 0, marginTop: 2 }} />
                <span>{fc}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
