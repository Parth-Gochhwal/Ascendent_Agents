import { useState, useEffect } from 'react';
import { Layers, GitBranch, Search } from 'lucide-react';
import type { Claim, Evidence, ClaimPropagation, ResearchSession } from '../types/research';
import { api } from '../services/api';
import { ConfidenceBadge } from '../components/common/Badge';
import { WhyButton } from '../components/common/WhyButton';
import { EmptyState } from '../components/common/EmptyState';

interface EvidencePageProps {
  sessionId: string;
  session: ResearchSession | null;
  onWhy: (type: string, id: string) => void;
}

export function EvidencePage({ sessionId, session, onWhy }: EvidencePageProps) {
  const [claims, setClaims] = useState<Claim[]>([]);
  const [, setEvidenceItems] = useState<Evidence[]>([]);
  const [propagations, setPropagations] = useState<ClaimPropagation[]>([]);
  const [activeTab, setActiveTab] = useState<'matrix' | 'claimline'>('matrix');
  const [filterText, setFilterText] = useState('');
  const [confidenceFilter, setConfidenceFilter] = useState('all');

  useEffect(() => {
    api.getClaims(sessionId)
      .then((d: { claims: Claim[]; evidence: Evidence[] }) => {
        setClaims(d.claims || []);
        setEvidenceItems(d.evidence || []);
      })
      .catch(() => {});

    api.getClaimPropagations(sessionId)
      .then((d: { propagations: ClaimPropagation[] }) => setPropagations(d.propagations || []))
      .catch(() => {});
  }, [sessionId, session?.status]);

  const filteredClaims = claims.filter((c) => {
    const matchesText =
      c.statement?.toLowerCase().includes(filterText.toLowerCase()) ||
      c.metric?.toLowerCase().includes(filterText.toLowerCase()) ||
      c.conditions?.some((cond: string) => cond.toLowerCase().includes(filterText.toLowerCase()));
    const matchesConfidence =
      confidenceFilter === 'all' || c.confidence?.toLowerCase() === confidenceFilter;
    return matchesText && matchesConfidence;
  });

  return (
    <div className="workspace-content animate-fade-in">
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--space-5)' }}>
        <div>
          <div className="card-section-label">EMPIRICAL GROUNDING MATRIX</div>
          <h1 style={{ fontFamily: 'var(--font-serif)', fontSize: '1.75rem' }}>
            Evidence Matrix & ClaimLine
          </h1>
          <p style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>
            Verifiable paper claims linked directly to quantitative metrics, experimental conditions, and propagation chains
          </p>
        </div>

        {/* Tab switcher */}
        <div className="toolbar-group">
          <button
            className={`action-btn-secondary ${activeTab === 'matrix' ? 'action-btn-primary' : ''}`}
            onClick={() => setActiveTab('matrix')}
          >
            <Layers size={13} />
            <span>Evidence Matrix</span>
          </button>
          <button
            className={`action-btn-secondary ${activeTab === 'claimline' ? 'action-btn-primary' : ''}`}
            onClick={() => setActiveTab('claimline')}
          >
            <GitBranch size={13} />
            <span>ClaimLine ({propagations.length})</span>
          </button>
        </div>
      </div>

      {activeTab === 'matrix' ? (
        <>
          {/* Filter Bar */}
          <div style={{ display: 'flex', gap: 10, marginBottom: 'var(--space-4)', flexWrap: 'wrap' }}>
            <div style={{ position: 'relative', flex: 1, minWidth: 260 }}>
              <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-tertiary)' }} />
              <input
                style={{ width: '100%', paddingLeft: 32, paddingRight: 12, height: 34, fontSize: 13 }}
                placeholder="Search claims, metrics, conditions..."
                value={filterText}
                onChange={(e) => setFilterText(e.target.value)}
              />
            </div>
            <select
              style={{ height: 34, padding: '0 12px', fontSize: 12, fontFamily: 'var(--font-mono)' }}
              value={confidenceFilter}
              onChange={(e) => setConfidenceFilter(e.target.value)}
            >
              <option value="all">ALL CONFIDENCE LEVELS</option>
              <option value="high">HIGH CONFIDENCE ONLY</option>
              <option value="medium">MEDIUM CONFIDENCE ONLY</option>
              <option value="low">LOW CONFIDENCE ONLY</option>
            </select>
          </div>

          {/* Evidence Matrix Table */}
          {filteredClaims.length > 0 ? (
            <div className="scholarly-table-container">
              <table className="scholarly-table">
                <thead>
                  <tr>
                    <th style={{ width: '38%' }}>Atomic Claim Statement</th>
                    <th style={{ width: '12%' }}>Source Paper</th>
                    <th style={{ width: '14%' }}>Empirical Metric</th>
                    <th style={{ width: '22%' }}>Experimental Conditions</th>
                    <th style={{ width: '8%' }}>Confidence</th>
                    <th style={{ width: '6%', textAlign: 'right' }}>Provenance</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredClaims.map((c, i) => (
                    <tr key={c.id || i}>
                      <td>
                        <div style={{ color: 'var(--text-primary)', fontWeight: 500, lineHeight: 1.45 }}>
                          {c.statement}
                        </div>
                      </td>
                      <td>
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--accent-steel)' }}>
                          {c.paper_id.slice(0, 10)}
                        </span>
                      </td>
                      <td>
                        {c.metric ? (
                          <div>
                            <span className="nexus-badge badge-blue">{c.metric}</span>
                            {c.evidence_value && (
                              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-primary)', marginTop: 2 }}>
                                {c.evidence_value}
                              </div>
                            )}
                          </div>
                        ) : (
                          <span style={{ color: 'var(--text-dim)', fontFamily: 'var(--font-mono)', fontSize: 11 }}>—</span>
                        )}
                      </td>
                      <td>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                          {c.conditions && c.conditions.length > 0 ? (
                            c.conditions.map((cond: string, j: number) => (
                              <span key={j} className="telemetry-chip" style={{ fontSize: 10 }}>{cond}</span>
                            ))
                          ) : (
                            <span style={{ color: 'var(--text-dim)', fontSize: 11 }}>Unconditioned</span>
                          )}
                        </div>
                      </td>
                      <td>
                        <ConfidenceBadge confidence={c.confidence} />
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <WhyButton onClick={() => onWhy('paper', c.paper_id)} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <EmptyState
              icon={<Layers size={24} />}
              title="No Claims Found"
              description="No empirical claims match your current filter criteria."
            />
          )}
        </>
      ) : (
        /* ClaimLine Tab: Propagation Across Literature */
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div className="editorial-card highlight-indigo" style={{ marginBottom: 8 }}>
            <div className="card-section-label">CLAIMLINE — PROPAGATION & DRIFT DYNAMICS</div>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5, marginTop: 4 }}>
              Visualizes how scientific assertions evolve, generalize, specialize, or lose experimental caveats as they get cited across subsequent papers.
            </p>
          </div>

          {propagations.length > 0 ? (
            propagations.map((p, i) => (
              <div key={p.id || i} className="editorial-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span className="nexus-badge badge-indigo">
                      {p.relationship_type.replace(/_/g, ' ').toUpperCase()}
                    </span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-tertiary)' }}>
                      Paper {p.source_paper_id.slice(0, 8)} → Paper {p.derived_paper_id.slice(0, 8)}
                    </span>
                  </div>
                  <WhyButton onClick={() => onWhy('claim_propagation', p.id)} />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 8 }}>
                  <div style={{ background: 'var(--bg-tertiary)', padding: 10, borderRadius: 'var(--radius-sm)', borderLeft: '2px solid var(--accent-steel)' }}>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)' }}>ORIGINATING SOURCE CONDITIONS</div>
                    <div style={{ fontSize: 12, color: 'var(--text-primary)', marginTop: 4 }}>
                      {p.source_conditions?.join(', ') || 'Standard experimental conditions'}
                    </div>
                  </div>
                  <div style={{ background: 'var(--bg-tertiary)', padding: 10, borderRadius: 'var(--radius-sm)', borderLeft: '2px solid var(--accent-indigo)' }}>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)' }}>DERIVED CITING CONDITIONS</div>
                    <div style={{ fontSize: 12, color: 'var(--text-primary)', marginTop: 4 }}>
                      {p.derived_conditions?.join(', ') || 'Generalized context'}
                    </div>
                  </div>
                </div>

                {p.explanation && (
                  <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 10, lineHeight: 1.5 }}>
                    <strong>Propagation Scope Shift:</strong> {p.explanation}
                  </p>
                )}
              </div>
            ))
          ) : (
            <EmptyState
              icon={<GitBranch size={24} />}
              title="No ClaimLine Propagations Detected"
              description="ClaimLine tracking identifies citations that weaken or extend claims across multiple publications."
            />
          )}
        </div>
      )}
    </div>
  );
}
