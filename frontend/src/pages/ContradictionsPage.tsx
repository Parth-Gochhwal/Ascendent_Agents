import { useState, useEffect } from 'react';
import { Split, Sliders } from 'lucide-react';
import type { Contradiction, ResearchSession } from '../types/research';
import { api } from '../services/api';
import { ContradictionBadge, ConfidenceBadge } from '../components/common/Badge';
import { WhyButton } from '../components/common/WhyButton';
import { EmptyState } from '../components/common/EmptyState';

interface ContradictionsPageProps {
  sessionId: string;
  session: ResearchSession | null;
  onWhy: (type: string, id: string) => void;
}

export function ContradictionsPage({ sessionId, session, onWhy }: ContradictionsPageProps) {
  const [contradictions, setContradictions] = useState<Contradiction[]>([]);

  useEffect(() => {
    api.getContradictions(sessionId)
      .then((d: { contradictions: Contradiction[] }) => setContradictions(d.contradictions || []))
      .catch(() => {});
  }, [sessionId, session?.status]);

  return (
    <div className="workspace-content animate-fade-in">
      {/* Header */}
      <div style={{ marginBottom: 'var(--space-5)' }}>
        <div className="card-section-label">SCIENTIFIC DISCREPANCY RESOLUTION</div>
        <h1 style={{ fontFamily: 'var(--font-serif)', fontSize: '1.75rem' }}>
          Contradiction & Tension Engine
        </h1>
        <p style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>
          Disagreements rigorously classified into Direct Conflicts, Contextual Boundary Disagreements, or Methodological Variations
        </p>
      </div>

      {/* Tension Cards List */}
      {contradictions.length > 0 ? (
        contradictions.map((c) => (
          <div key={c.id} className="tension-diagram-card highlight-copper">
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-3)' }}>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <ContradictionBadge type={c.classification} />
                <ConfidenceBadge confidence={c.confidence} />
                <span className="telemetry-chip">
                  <span className="chip-label">SEVERITY:</span>
                  <span className="chip-value" style={{ textTransform: 'uppercase' }}>{c.severity || 'MEDIUM'}</span>
                </span>
              </div>

              <WhyButton label="Explain Discrepancy (Why?)" onClick={() => onWhy('contradiction', c.id)} />
            </div>

            {/* Central Tension Visualizer (Study A ──[TENSION]── Study B) */}
            <div className="tension-sides-container">
              {/* Study A */}
              <div className="tension-side-box side-a">
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--accent-steel)', textTransform: 'uppercase', marginBottom: 4 }}>
                  STUDY A FINDING
                </div>
                <div style={{ fontFamily: 'var(--font-serif)', fontSize: 14, color: 'var(--text-primary)', lineHeight: 1.45, marginBottom: 8 }}>
                  "{c.claim_a_text}"
                </div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-tertiary)' }}>
                  Ref: {c.paper_a_summary || c.paper_a_id}
                </div>
              </div>

              {/* Tension Center Axis */}
              <div className="tension-center-axis">
                <div style={{ width: 1, height: 20, background: 'var(--border-secondary)' }} />
                <span className="tension-center-badge">VS TENSION</span>
                <div style={{ width: 1, height: 20, background: 'var(--border-secondary)' }} />
              </div>

              {/* Study B */}
              <div className="tension-side-box side-b">
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--accent-copper)', textTransform: 'uppercase', marginBottom: 4 }}>
                  STUDY B FINDING
                </div>
                <div style={{ fontFamily: 'var(--font-serif)', fontSize: 14, color: 'var(--text-primary)', lineHeight: 1.45, marginBottom: 8 }}>
                  "{c.claim_b_text}"
                </div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-tertiary)' }}>
                  Ref: {c.paper_b_summary || c.paper_b_id}
                </div>
              </div>
            </div>

            {/* Differing Experimental Variables */}
            {c.different_conditions && c.different_conditions.length > 0 && (
              <div className="tension-diff-parameters">
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)', textTransform: 'uppercase', marginBottom: 6 }}>
                  <Sliders size={12} color="var(--accent-amber)" />
                  <span>Differing Experimental Boundary Conditions</span>
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {c.different_conditions.map((diff: string, idx: number) => (
                    <span key={idx} className="telemetry-chip" style={{ color: 'var(--accent-amber)' }}>
                      ⚠ {diff}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Discrepancy Synthesis & Coexistence Verdict */}
            <div style={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-sm)', padding: 'var(--space-3) var(--space-4)', marginTop: 'var(--space-3)' }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--accent-steel)', textTransform: 'uppercase', marginBottom: 4 }}>
                SCIENTIFIC SYNTHESIS & RESOLUTION
              </div>
              <p style={{ fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.6 }}>
                {c.explanation}
              </p>
              {c.coexistence_conditions && (
                <div style={{ fontSize: 12, color: 'var(--accent-teal)', marginTop: 6, borderTop: '1px solid var(--border-subtle)', paddingTop: 6 }}>
                  <strong>Coexistence Criteria:</strong> {c.coexistence_conditions}
                </div>
              )}
            </div>
          </div>
        ))
      ) : (
        <EmptyState
          icon={<Split size={24} />}
          title="No Scientific Contradictions Flagged"
          description="Contradiction extraction analyzes cross-paper claims under shared versus differing experimental protocols."
        />
      )}
    </div>
  );
}
