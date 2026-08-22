import { Activity, Compass, Cpu, Database, Search, ShieldCheck } from 'lucide-react';
import type { AgentEvent } from '../../types/research';

interface LoadingRadarProps {
  question: string;
  events: AgentEvent[];
}

export function LoadingRadar({ question, events }: LoadingRadarProps) {
  const latestEvent = events[events.length - 1];

  const stages = [
    { name: 'Research Planning', icon: <Compass size={14} />, key: 'planning' },
    { name: 'Literature Discovery', icon: <Search size={14} />, key: 'discovering' },
    { name: 'Evidence Extraction', icon: <Database size={14} />, key: 'analyzing' },
    { name: 'Contradictions & Tension', icon: <Activity size={14} />, key: 'contradictions' },
    { name: 'Experiment Design', icon: <Cpu size={14} />, key: 'experiment' },
    { name: 'Integrity & Red Team', icon: <ShieldCheck size={14} />, key: 'audit' },
  ];

  return (
    <div style={{ padding: '60px var(--space-6)', maxWidth: 720, margin: '0 auto', textAlign: 'center' }}>
      {/* Animated Scientific Radar Visual */}
      <div style={{ position: 'relative', width: 140, height: 140, margin: '0 auto var(--space-6)' }}>
        <div
          style={{
            position: 'absolute',
            inset: 0,
            borderRadius: '50%',
            border: '1px dashed var(--border-secondary)',
            animation: 'pulseSubtle 3s infinite ease-in-out',
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 18,
            borderRadius: '50%',
            border: '1px solid rgba(56, 189, 248, 0.25)',
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 38,
            borderRadius: '50%',
            border: '1px solid rgba(20, 184, 166, 0.35)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'var(--bg-secondary)',
          }}
        >
          <Activity size={24} color="var(--accent-steel)" className="animate-pulse-subtle" />
        </div>
      </div>

      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, letterSpacing: '0.15em', textTransform: 'uppercase', color: 'var(--accent-steel)', marginBottom: 8 }}>
        AUTONOMOUS SCIENTIFIC INVESTIGATION ACTIVE
      </div>
      <h2 style={{ fontFamily: 'var(--font-serif)', fontSize: '1.45rem', marginBottom: 'var(--space-4)', color: 'var(--text-primary)' }}>
        "{question}"
      </h2>

      {latestEvent && (
        <div
          style={{
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border-primary)',
            borderRadius: 'var(--radius-md)',
            padding: 'var(--space-3) var(--space-4)',
            marginBottom: 'var(--space-6)',
            display: 'inline-flex',
            alignItems: 'center',
            gap: 10,
          }}
        >
          <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--accent-sage)', boxShadow: '0 0 8px var(--accent-sage)' }} />
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--accent-steel)' }}>
            [{latestEvent.agent_name}]
          </span>
          <span style={{ fontSize: 13, color: 'var(--text-primary)' }}>
            {latestEvent.message || 'Executing analytical stage...'}
          </span>
        </div>
      )}

      {/* Pipeline Stage Indicators */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 8, textAlign: 'left' }}>
        {stages.map((st, i) => {
          const isDone = events.some(e => e.agent_name?.toLowerCase().includes(st.key) && e.status === 'completed');
          const isRunning = latestEvent?.agent_name?.toLowerCase().includes(st.key);

          return (
            <div
              key={i}
              style={{
                background: isRunning ? 'var(--bg-elevated)' : 'var(--bg-secondary)',
                border: `1px solid ${isRunning ? 'var(--accent-steel)' : isDone ? 'var(--border-secondary)' : 'var(--border-primary)'}`,
                borderRadius: 'var(--radius-sm)',
                padding: '8px 12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12 }}>
                <span style={{ color: isRunning ? 'var(--accent-steel)' : isDone ? 'var(--accent-teal)' : 'var(--text-tertiary)' }}>
                  {st.icon}
                </span>
                <span style={{ color: isRunning ? 'var(--text-primary)' : isDone ? 'var(--text-secondary)' : 'var(--text-tertiary)', fontWeight: isRunning ? 600 : 400 }}>
                  {st.name}
                </span>
              </div>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: isDone ? 'var(--accent-teal)' : isRunning ? 'var(--accent-steel)' : 'var(--text-dim)' }}>
                {isDone ? '✓' : isRunning ? '●' : '○'}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
