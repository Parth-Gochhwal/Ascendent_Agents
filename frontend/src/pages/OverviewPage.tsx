import { ArrowRight } from 'lucide-react';
import type { PageId, ResearchSession } from '../types/research';
import { ConfidenceBadge } from '../components/common/Badge';
import { WhyButton } from '../components/common/WhyButton';

interface OverviewPageProps {
  session: ResearchSession | null;
  onNavigate: (page: PageId) => void;
  onWhy: (type: string, id: string) => void;
}

export function OverviewPage({ session, onNavigate, onWhy }: OverviewPageProps) {
  if (!session) {
    return <div style={{ padding: 40, textAlign: 'center' }}>Loading investigation...</div>;
  }

  const stats = session.stats || {};
  const plan = session.plan;

  return (
    <div className="workspace-content animate-fade-in">
      {/* ── Editorial Question Hero ── */}
      <div className="overview-question-hero">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-2)' }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--accent-steel)' }}>
            INVESTIGATED RESEARCH QUESTION
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="action-btn-secondary" onClick={() => onNavigate('dossier')}>
              <span>View Dossier</span>
              <ArrowRight size={12} />
            </button>
            <button className="action-btn-primary" onClick={() => onNavigate('experiment')}>
              <span>Experiment Plan</span>
              <ArrowRight size={12} />
            </button>
          </div>
        </div>

        <h1 className="overview-question-headline">
          {session.question}
        </h1>

        {plan?.research_objective && (
          <p style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
            <strong style={{ color: 'var(--text-primary)' }}>Research Objective:</strong> {plan.research_objective}
          </p>
        )}
      </div>

      {/* ── Scientific Signal Telemetry Strip ── */}
      <div className="overview-metrics-strip">
        <div className="overview-metric-cell" onClick={() => onNavigate('literature')}>
          <div className="overview-metric-val" style={{ color: 'var(--accent-steel)' }}>
            {stats.papers_discovered || 0}
          </div>
          <div className="overview-metric-name">Papers Discovered</div>
        </div>

        <div className="overview-metric-cell" onClick={() => onNavigate('evidence')}>
          <div className="overview-metric-val" style={{ color: 'var(--accent-teal)' }}>
            {stats.claims_extracted || 0}
          </div>
          <div className="overview-metric-name">Claims Extracted</div>
        </div>

        <div className="overview-metric-cell" onClick={() => onNavigate('contradictions')}>
          <div className="overview-metric-val" style={{ color: 'var(--accent-copper)' }}>
            {stats.contradictions_found || 0}
          </div>
          <div className="overview-metric-name">Contradictions Found</div>
        </div>

        <div className="overview-metric-cell" onClick={() => onNavigate('consensus')}>
          <div className="overview-metric-val" style={{ color: 'var(--accent-sage)' }}>
            {stats.consensus_findings || 0}
          </div>
          <div className="overview-metric-name">Consensus Findings</div>
        </div>

        <div className="overview-metric-cell" onClick={() => onNavigate('gaps')}>
          <div className="overview-metric-val" style={{ color: 'var(--accent-crimson)' }}>
            {stats.research_gaps || 0}
          </div>
          <div className="overview-metric-name">Research Gaps</div>
        </div>

        <div className="overview-metric-cell" onClick={() => onNavigate('methods')}>
          <div className="overview-metric-val" style={{ color: 'var(--accent-indigo)' }}>
            {stats.methods_extracted || 0}
          </div>
          <div className="overview-metric-name">Methods Mapped</div>
        </div>
      </div>

      {/* ── Structured Question Decomposition ── */}
      {plan?.subquestions && plan.subquestions.length > 0 && (
        <div className="editorial-card highlight-indigo" style={{ marginBottom: 'var(--space-5)' }}>
          <div className="card-editorial-header">
            <div>
              <div className="card-section-label">INVESTIGATIVE BREAKDOWN</div>
              <h3 className="card-editorial-title">Structured Question Decomposition</h3>
            </div>
            <span className="nexus-badge badge-indigo">{plan.subquestions.length} Subquestions</span>
          </div>

          <div className="decomposition-tree-grid">
            {plan.subquestions.map((sq: string, i: number) => (
              <div key={i} className="decomposition-node">
                <span className="decomposition-node-num">0{i + 1}.</span>
                <span className="decomposition-node-text">{sq}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Key Editorial Finding Blocks ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: 'var(--space-4)', marginBottom: 'var(--space-5)' }}>
        {/* Supported / Consensus */}
        <div className="editorial-card highlight-teal">
          <div className="card-editorial-header">
            <div>
              <div className="card-section-label">EMPIRICAL SUPPORT</div>
              <h3 className="card-editorial-title" style={{ fontSize: '1.05rem' }}>What The Literature Supports</h3>
            </div>
            <button className="action-btn-secondary" style={{ padding: '3px 8px' }} onClick={() => onNavigate('consensus')}>
              Explore →
            </button>
          </div>
          {session.consensus && session.consensus.length > 0 ? (
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              {session.consensus[0].statement}
            </p>
          ) : (
            <p style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>No consensus synthesized yet.</p>
          )}
        </div>

        {/* Contested / Conflict */}
        <div className="editorial-card highlight-copper">
          <div className="card-editorial-header">
            <div>
              <div className="card-section-label">SCIENTIFIC TENSION</div>
              <h3 className="card-editorial-title" style={{ fontSize: '1.05rem' }}>Where Studies Disagree</h3>
            </div>
            <button className="action-btn-secondary" style={{ padding: '3px 8px' }} onClick={() => onNavigate('contradictions')}>
              Explore →
            </button>
          </div>
          {session.contradictions && session.contradictions.length > 0 ? (
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              {session.contradictions[0].explanation || session.contradictions[0].claim_a_text}
            </p>
          ) : (
            <p style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>No conflicting findings recorded.</p>
          )}
        </div>
      </div>

      {/* ── Red-Team Adjudication Summary ── */}
      {session.red_team && (
        <div className="editorial-card highlight-crimson" style={{ marginBottom: 'var(--space-5)' }}>
          <div className="card-editorial-header">
            <div>
              <div className="card-section-label">ADVERSARIAL RED-TEAM ADJUDICATION</div>
              <h3 className="card-editorial-title">Critical Vulnerability & Bias Review</h3>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <ConfidenceBadge confidence={session.red_team.final_confidence} />
              <WhyButton onClick={() => onWhy('red_team', 'red_team')} />
            </div>
          </div>
          <p style={{ fontSize: 14, color: 'var(--text-primary)', lineHeight: 1.6 }}>
            {session.red_team.adjudication}
          </p>
        </div>
      )}

      {/* ── Target Entities & Search Queries ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }}>
        {plan?.search_queries && (
          <div className="editorial-card">
            <div className="card-section-label">SEARCH STRATEGY QUERIES</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginTop: 8 }}>
              {plan.search_queries.map((q: string, i: number) => (
                <div key={i} style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-secondary)' }}>
                  • {q}
                </div>
              ))}
            </div>
          </div>
        )}

        {plan?.concepts && (
          <div className="editorial-card">
            <div className="card-section-label">EXTRACTED CORE ENTITIES & TARGETS</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 8 }}>
              {plan.concepts.map((c: string, i: number) => (
                <span key={i} className="nexus-badge badge-blue">{c}</span>
              ))}
              {plan.methods_of_interest?.map((m: string, i: number) => (
                <span key={`m-${i}`} className="nexus-badge badge-indigo">{m}</span>
              ))}
              {plan.datasets_of_interest?.map((d: string, i: number) => (
                <span key={`d-${i}`} className="nexus-badge badge-neutral">{d}</span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
