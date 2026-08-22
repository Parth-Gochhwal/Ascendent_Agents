import { useState, useEffect } from 'react';
import { GitCommit, Sparkles } from 'lucide-react';
import type { TimelineMilestone } from '../types/research';
import { api } from '../services/api';
import { EmptyState } from '../components/common/EmptyState';

interface TimelinePageProps {
  sessionId: string;
}

export function TimelinePage({ sessionId }: TimelinePageProps) {
  const [milestones, setMilestones] = useState<TimelineMilestone[]>([]);

  useEffect(() => {
    api.getTimeline(sessionId)
      .then((d: { milestones: TimelineMilestone[] }) => setMilestones(d.milestones || []))
      .catch(() => {});
  }, [sessionId]);

  return (
    <div className="workspace-content animate-fade-in">
      {/* Header */}
      <div style={{ marginBottom: 'var(--space-5)' }}>
        <div className="card-section-label">LONGITUDINAL RESEARCH TIMELINE</div>
        <h1 style={{ fontFamily: 'var(--font-serif)', fontSize: '1.75rem' }}>
          Evolution of Paradigms & Methodological Shifts
        </h1>
        <p style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>
          Historical progression of scientific discoveries, architectures, and breakthrough transitions over time
        </p>
      </div>

      {/* Timeline Stream */}
      {milestones.length > 0 ? (
        <div style={{ position: 'relative', paddingLeft: 24, borderLeft: '2px solid var(--border-primary)', display: 'flex', flexDirection: 'column', gap: 'var(--space-4)', margin: '20px 0' }}>
          {milestones.map((m, i) => (
            <div key={i} style={{ position: 'relative' }}>
              {/* Dot */}
              <div
                style={{
                  position: 'absolute',
                  left: -31,
                  top: 14,
                  width: 12,
                  height: 12,
                  borderRadius: '50%',
                  background: m.breakthrough_indicator ? 'var(--accent-amber)' : 'var(--accent-steel)',
                  border: '2px solid var(--bg-space)',
                  boxShadow: m.breakthrough_indicator ? '0 0 10px var(--accent-amber)' : 'none',
                }}
              />

              {/* Milestone Card */}
              <div className="editorial-card" style={{ borderLeft: m.breakthrough_indicator ? '3px solid var(--accent-amber)' : '1px solid var(--border-primary)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    <span className="nexus-badge badge-blue" style={{ fontSize: 12, fontWeight: 700 }}>
                      {m.year}
                    </span>
                    <span className="nexus-badge badge-indigo">
                      {m.paradigm}
                    </span>
                  </div>
                  {m.breakthrough_indicator && (
                    <span className="nexus-badge badge-copper" style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                      <Sparkles size={11} />
                      <span>BREAKTHROUGH MILESTONE</span>
                    </span>
                  )}
                </div>

                <h3 style={{ fontFamily: 'var(--font-serif)', fontSize: '1.2rem', color: 'var(--text-primary)', margin: '4px 0 8px' }}>
                  {m.title}
                </h3>

                <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                  {m.description}
                </p>

                {m.key_methods && m.key_methods.length > 0 && (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 10 }}>
                    {m.key_methods.map((km: string, j: number) => (
                      <span key={j} className="telemetry-chip" style={{ fontSize: 10 }}>
                        {km}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState
          icon={<GitCommit size={24} />}
          title="Constructing Longitudinal Research Timeline"
          description="Chronological timeline orders paradigm shifts and breakthrough milestones extracted across publications."
        />
      )}
    </div>
  );
}
