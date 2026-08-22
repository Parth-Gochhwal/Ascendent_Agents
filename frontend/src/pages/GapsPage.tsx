import { useState, useEffect } from 'react';
import { Search, Compass, AlertOctagon, Lightbulb } from 'lucide-react';
import type { ResearchGap, MissingExperiment, DeadEnd, ResearchSession } from '../types/research';
import { api } from '../services/api';
import { ConfidenceBadge } from '../components/common/Badge';
import { WhyButton } from '../components/common/WhyButton';
import { EmptyState } from '../components/common/EmptyState';

interface GapsPageProps {
  sessionId: string;
  session: ResearchSession | null;
  onWhy: (type: string, id: string) => void;
}

export function GapsPage({ sessionId, session, onWhy }: GapsPageProps) {
  const [gaps, setGaps] = useState<ResearchGap[]>([]);
  const [missingExperiments, setMissingExperiments] = useState<MissingExperiment[]>([]);
  const [deadEnds, setDeadEnds] = useState<DeadEnd[]>([]);
  const [activeSubTab, setActiveSubTab] = useState<'gaps' | 'deadends' | 'experiments'>('gaps');

  useEffect(() => {
    api.getGaps(sessionId)
      .then((d: { gaps: ResearchGap[]; missing_experiments: MissingExperiment[] }) => {
        setGaps(d.gaps || []);
        setMissingExperiments(d.missing_experiments || []);
      })
      .catch(() => {});

    api.getDeadEnds(sessionId)
      .then((d: { dead_ends: DeadEnd[]; count: number }) => setDeadEnds(d.dead_ends || []))
      .catch(() => {});
  }, [sessionId, session?.status]);

  return (
    <div className="workspace-content animate-fade-in">
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--space-5)' }}>
        <div>
          <div className="card-section-label">UNTESTED & NEGATIVE KNOWLEDGE LANDSCAPE</div>
          <h1 style={{ fontFamily: 'var(--font-serif)', fontSize: '1.75rem' }}>
            Research Gaps & Dead-End Atlas
          </h1>
          <p style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>
            Systematically identified white spaces, missing empirical experiments, and documented failure conditions
          </p>
        </div>

        {/* Tab Controls */}
        <div className="toolbar-group">
          <button
            className={`action-btn-secondary ${activeSubTab === 'gaps' ? 'action-btn-primary' : ''}`}
            onClick={() => setActiveSubTab('gaps')}
          >
            <Search size={13} />
            <span>Research Gaps ({gaps.length})</span>
          </button>
          <button
            className={`action-btn-secondary ${activeSubTab === 'deadends' ? 'action-btn-primary' : ''}`}
            onClick={() => setActiveSubTab('deadends')}
          >
            <AlertOctagon size={13} />
            <span>Dead-End Atlas ({deadEnds.length})</span>
          </button>
          <button
            className={`action-btn-secondary ${activeSubTab === 'experiments' ? 'action-btn-primary' : ''}`}
            onClick={() => setActiveSubTab('experiments')}
          >
            <Compass size={13} />
            <span>Missing Experiments ({missingExperiments.length})</span>
          </button>
        </div>
      </div>

      {/* ── SubTab 1: Research Gaps ── */}
      {activeSubTab === 'gaps' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          {gaps.length > 0 ? (
            gaps.map((g, i) => (
              <div key={g.id || i} className="editorial-card highlight-indigo">
                <div className="card-editorial-header">
                  <div>
                    <div className="card-section-label">GAP #{i + 1} · {g.gap_type.toUpperCase()}</div>
                    <h3 className="card-editorial-title">{g.title}</h3>
                  </div>

                  <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    {g.importance && (
                      <span className="nexus-badge badge-copper">
                        IMPORTANCE: {g.importance.toUpperCase()}
                      </span>
                    )}
                    {g.feasibility && (
                      <span className="nexus-badge badge-high">
                        FEASIBILITY: {g.feasibility.toUpperCase()}
                      </span>
                    )}
                    <ConfidenceBadge confidence={g.confidence} />
                    <WhyButton onClick={() => onWhy('gap', g.id)} />
                  </div>
                </div>

                <p style={{ fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.6, marginBottom: 12 }}>
                  {g.description}
                </p>

                {g.potential_direction && (
                  <div style={{ background: 'var(--bg-tertiary)', borderLeft: '3px solid var(--accent-steel)', padding: '10px 14px', borderRadius: 'var(--radius-sm)', marginBottom: 8 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--accent-steel)', textTransform: 'uppercase', marginBottom: 2 }}>
                      <Lightbulb size={12} />
                      <span>PROPOSED INVESTIGATION DIRECTION</span>
                    </div>
                    <p style={{ fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.5 }}>
                      {g.potential_direction}
                    </p>
                  </div>
                )}

                {g.why_it_matters && (
                  <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                    <strong style={{ color: 'var(--text-primary)' }}>Impact & Significance:</strong> {g.why_it_matters}
                  </div>
                )}
              </div>
            ))
          ) : (
            <EmptyState
              icon={<Search size={24} />}
              title="No Research Gaps Identified"
              description="Gap detection models extract underexplored intersections and missing methodological conditions."
            />
          )}
        </div>
      )}

      {/* ── SubTab 2: Dead-End Atlas (Negative Knowledge) ── */}
      {activeSubTab === 'deadends' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          <div className="editorial-card highlight-crimson" style={{ marginBottom: 4 }}>
            <div className="card-section-label">ATLAS OF NEGATIVE KNOWLEDGE & CONDITIONAL LIMITATIONS</div>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5, marginTop: 4 }}>
              Documents failed paradigms, non-generalizing architectures, and broken research paths so future experiments do not duplicate known dead ends.
            </p>
          </div>

          {deadEnds.length > 0 ? (
            <div className="dead-end-atlas-grid">
              {deadEnds.map((d, i) => (
                <div key={d.id || i} className="dead-end-card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                    <span className="nexus-badge badge-low">{d.status.replace(/_/g, ' ').toUpperCase()}</span>
                    <WhyButton label="Context" onClick={() => onWhy('dead_end', d.id)} />
                  </div>

                  <h3 style={{ fontFamily: 'var(--font-serif)', fontSize: '1.15rem', color: 'var(--text-primary)', marginBottom: 8 }}>
                    {d.approach}
                  </h3>

                  <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: 12 }}>
                    {d.description}
                  </p>

                  {d.failure_conditions && d.failure_conditions.length > 0 && (
                    <div style={{ background: 'var(--bg-tertiary)', padding: 8, borderRadius: 'var(--radius-sm)', marginBottom: 8 }}>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--accent-crimson)', textTransform: 'uppercase', marginBottom: 4 }}>
                        FAILURE CONDITIONS
                      </div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                        {d.failure_conditions.map((fc: string, j: number) => (
                          <span key={j} className="telemetry-chip" style={{ fontSize: 10, color: 'var(--accent-crimson)' }}>
                            ✗ {fc}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {d.alternative_directions && d.alternative_directions.length > 0 && (
                    <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>
                      <strong style={{ color: 'var(--accent-teal)' }}>Viable Alternatives:</strong> {d.alternative_directions.join(' · ')}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              icon={<AlertOctagon size={24} />}
              title="No Dead Ends Mapped"
              description="Dead-End extraction catalogues failed architectures and bounded methodological constraints."
            />
          )}
        </div>
      )}

      {/* ── SubTab 3: Missing Experiments ── */}
      {activeSubTab === 'experiments' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 'var(--space-3)' }}>
          {missingExperiments.map((m, i) => (
            <div key={m.id || i} className="editorial-card highlight-copper">
              <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
                <span className="nexus-badge badge-indigo">{m.method}</span>
                <span className="nexus-badge badge-blue">{m.dataset}</span>
              </div>
              <p style={{ fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.5 }}>
                {m.explanation}
              </p>
            </div>
          ))}
          {missingExperiments.length === 0 && (
            <EmptyState
              icon={<Compass size={24} />}
              title="No Missing Experiment Intersections"
              description="Missing experiment analysis identifies untested combinations in the Method × Dataset matrix."
            />
          )}
        </div>
      )}
    </div>
  );
}
