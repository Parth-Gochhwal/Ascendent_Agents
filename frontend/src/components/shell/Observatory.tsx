import { useState } from 'react';
import { X, Play, CheckCircle2, AlertCircle, Clock, Trash2, Filter } from 'lucide-react';
import type { AgentEvent } from '../../types/research';

interface ObservatoryProps {
  isOpen: boolean;
  onClose: () => void;
  events: AgentEvent[];
  onClearEvents?: () => void;
  status?: string;
}

export function Observatory({
  isOpen,
  onClose,
  events,
  onClearEvents,
  status = 'idle',
}: ObservatoryProps) {
  const [filterAgent, setFilterAgent] = useState<string>('all');
  const isRunning = status !== 'report_ready' && status !== 'idle' && status !== 'error';

  const agentNames = Array.from(new Set(events.map((e) => e.agent_name).filter(Boolean)));
  const filtered = events.filter(
    (e) => filterAgent === 'all' || e.agent_name === filterAgent
  );

  return (
    <aside className={`shell-observatory ${!isOpen ? 'collapsed' : ''}`}>
      {/* Header */}
      <div className="observatory-header">
        <div className="observatory-header-title">
          <div className={`observatory-live-indicator ${isRunning ? '' : 'idle'}`} />
          <span>OBSERVATORY CONSOLE</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          {onClearEvents && events.length > 0 && (
            <button
              onClick={onClearEvents}
              style={{ color: 'var(--text-tertiary)', padding: 4 }}
              title="Clear event trace"
            >
              <Trash2 size={13} />
            </button>
          )}
          <button onClick={onClose} style={{ color: 'var(--text-secondary)', padding: 4 }}>
            <X size={15} />
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      {agentNames.length > 0 && (
        <div
          style={{
            padding: '6px 12px',
            borderBottom: '1px solid var(--border-primary)',
            background: 'var(--bg-secondary)',
            display: 'flex',
            alignItems: 'center',
            gap: 6,
          }}
        >
          <Filter size={11} style={{ color: 'var(--text-tertiary)' }} />
          <select
            value={filterAgent}
            onChange={(e) => setFilterAgent(e.target.value)}
            style={{
              background: 'transparent',
              border: 'none',
              fontSize: 11,
              fontFamily: 'var(--font-mono)',
              color: 'var(--text-secondary)',
              width: '100%',
            }}
          >
            <option value="all">ALL AGENT SUBSYSTEMS ({events.length})</option>
            {agentNames.map((name) => (
              <option key={name} value={name}>
                {name.toUpperCase()}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Events Log Stream */}
      <div className="observatory-body">
        {filtered.map((ev, i) => {
          const isCompleted = ev.status === 'completed';
          const isFailed = ev.status === 'failed';
          const isEvRunning = ev.status === 'running';

          return (
            <div
              key={ev.id || i}
              className={`observatory-event-card ${isEvRunning ? 'running' : ''}`}
            >
              <div className="observatory-event-header">
                <span className="observatory-agent-name">{ev.agent_name}</span>
                <span
                  style={{
                    color: isCompleted
                      ? 'var(--accent-teal)'
                      : isFailed
                      ? 'var(--accent-crimson)'
                      : isEvRunning
                      ? 'var(--accent-steel)'
                      : 'var(--text-tertiary)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 3,
                  }}
                >
                  {isCompleted ? (
                    <CheckCircle2 size={11} />
                  ) : isFailed ? (
                    <AlertCircle size={11} />
                  ) : isEvRunning ? (
                    <Play size={11} className="animate-pulse-subtle" />
                  ) : null}
                  <span>{ev.status.toUpperCase()}</span>
                </span>
              </div>

              <div className="observatory-event-msg">{ev.message}</div>

              {ev.detail && (
                <div className="observatory-event-detail">{ev.detail}</div>
              )}

              {/* Telemetry info */}
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  fontFamily: 'var(--font-mono)',
                  fontSize: 10,
                  color: 'var(--text-dim)',
                  marginTop: 4,
                }}
              >
                {ev.duration_ms != null && (
                  <span style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
                    <Clock size={9} />
                    {(ev.duration_ms / 1000).toFixed(2)}s
                  </span>
                )}
                {ev.token_usage != null && (
                  <span>{ev.token_usage.toLocaleString()} tokens</span>
                )}
              </div>
            </div>
          );
        })}

        {filtered.length === 0 && (
          <div
            style={{
              padding: '40px 20px',
              textAlign: 'center',
              color: 'var(--text-tertiary)',
              fontFamily: 'var(--font-mono)',
              fontSize: 11,
            }}
          >
            NO AGENT EVENTS RECORDED
          </div>
        )}
      </div>
    </aside>
  );
}
