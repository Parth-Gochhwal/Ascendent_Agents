import { X, ShieldAlert, BookOpen, GitCommit, AlertTriangle } from 'lucide-react';
import type { WhyExplanation } from '../../types/research';
import { ConfidenceBadge } from './Badge';

interface WhyInspectorProps {
  isOpen: boolean;
  onClose: () => void;
  targetType: string;
  targetId: string;
  data: WhyExplanation | null;
  loading: boolean;
}

export function WhyInspector({
  isOpen,
  onClose,
  targetType,
  data,
  loading,
}: WhyInspectorProps) {
  if (!isOpen) return null;

  return (
    <div className="why-drawer-backdrop" onClick={onClose}>
      <div className="why-drawer-content" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="why-drawer-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div
              style={{
                width: 26,
                height: 26,
                borderRadius: 'var(--radius-xs)',
                background: 'rgba(217, 119, 54, 0.15)',
                color: 'var(--accent-copper)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <GitCommit size={14} />
            </div>
            <div>
              <div
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: 10,
                  color: 'var(--text-tertiary)',
                  letterSpacing: '0.1em',
                  textTransform: 'uppercase',
                }}
              >
                PROVENANCE CHAIN INSPECTOR
              </div>
              <div style={{ fontFamily: 'var(--font-serif)', fontSize: 15, fontWeight: 500 }}>
                {targetType.replace(/_/g, ' ').toUpperCase()} EXPLAINABILITY
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              padding: 6,
              borderRadius: 'var(--radius-xs)',
              background: 'var(--bg-tertiary)',
              color: 'var(--text-secondary)',
            }}
          >
            <X size={16} />
          </button>
        </div>

        {/* Body */}
        <div className="why-drawer-body">
          {loading ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '60px 0', gap: 12 }}>
              <div
                style={{
                  width: 28,
                  height: 28,
                  border: '2px solid var(--border-secondary)',
                  borderTopColor: 'var(--accent-copper)',
                  borderRadius: '50%',
                  animation: 'pulseSubtle 1s infinite linear',
                }}
              />
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-tertiary)' }}>
                RESOLVING EVIDENCE PROVENANCE GRAPH...
              </div>
            </div>
          ) : data ? (
            <>
              {/* Target Statement */}
              <div className="why-assertion-box">
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)', textTransform: 'uppercase', marginBottom: 4 }}>
                  TARGET SCIENTIFIC ASSERTION
                </div>
                <div style={{ fontFamily: 'var(--font-serif)', fontSize: 14, color: 'var(--text-primary)', lineHeight: 1.45, marginBottom: 8 }}>
                  "{data.target_statement}"
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <ConfidenceBadge confidence={data.confidence} />
                </div>
              </div>

              {/* Evidence Chain */}
              {data.evidence_chain && data.evidence_chain.length > 0 && (
                <div>
                  <div
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: 10,
                      letterSpacing: '0.08em',
                      textTransform: 'uppercase',
                      color: 'var(--accent-steel)',
                      marginBottom: 8,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                    }}
                  >
                    <BookOpen size={12} />
                    <span>Verifiable Evidence Chain ({data.evidence_chain.length} records)</span>
                  </div>
                  {data.evidence_chain.map((item, i) => (
                    <div key={i} className="why-chain-item">
                      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>
                        {item.claim}
                      </div>
                      <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 6 }}>
                        <strong style={{ color: 'var(--text-tertiary)', fontSize: 10, textTransform: 'uppercase' }}>Evidence: </strong>
                        {item.evidence}
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 11, color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>
                        <span>Source: {item.source_paper_title}</span>
                        {item.doi_or_url && (
                          <span style={{ color: 'var(--accent-steel)' }}>DOI:{item.doi_or_url}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Reasoning Factors */}
              {data.reasoning_factors && data.reasoning_factors.length > 0 && (
                <div>
                  <div
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: 10,
                      letterSpacing: '0.08em',
                      textTransform: 'uppercase',
                      color: 'var(--accent-indigo)',
                      marginBottom: 8,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                    }}
                  >
                    <GitCommit size={12} />
                    <span>Reasoning Decomposition</span>
                  </div>
                  <div style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-sm)', padding: 12 }}>
                    {data.reasoning_factors.map((factor, i) => (
                      <div key={i} style={{ fontSize: 12, color: 'var(--text-secondary)', padding: '4px 0', display: 'flex', gap: 8 }}>
                        <span style={{ color: 'var(--accent-indigo)', fontFamily: 'var(--font-mono)' }}>▸</span>
                        <span>{factor}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Uncertainty Analysis */}
              {data.uncertainty_analysis && (
                <div className="why-uncertainty-box">
                  <div
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: 10,
                      letterSpacing: '0.08em',
                      textTransform: 'uppercase',
                      color: 'var(--accent-amber)',
                      marginBottom: 4,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                    }}
                  >
                    <AlertTriangle size={12} />
                    <span>Scientific Uncertainty & Methodological Bounds</span>
                  </div>
                  <p style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                    {data.uncertainty_analysis}
                  </p>
                </div>
              )}

              {/* Conflicting Evidence */}
              {data.conflicting_evidence && data.conflicting_evidence.length > 0 && (
                <div style={{ background: 'rgba(244, 63, 94, 0.06)', border: '1px solid rgba(244, 63, 94, 0.25)', borderRadius: 'var(--radius-sm)', padding: 12 }}>
                  <div
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: 10,
                      letterSpacing: '0.08em',
                      textTransform: 'uppercase',
                      color: 'var(--accent-crimson)',
                      marginBottom: 6,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                    }}
                  >
                    <ShieldAlert size={12} />
                    <span>Contrasting / Non-Convergent Evidence</span>
                  </div>
                  {data.conflicting_evidence.map((c, i) => (
                    <div key={i} style={{ fontSize: 12, color: 'var(--text-secondary)', padding: '3px 0' }}>
                      • {c}
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : (
            <div style={{ textAlign: 'center', color: 'var(--text-tertiary)', padding: '40px 20px', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
              NO EXPLAINABILITY RECORD REGISTERED FOR THIS TARGET IDENTIFIER
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
