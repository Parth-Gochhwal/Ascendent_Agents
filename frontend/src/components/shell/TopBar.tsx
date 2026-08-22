import { useState, useRef, useEffect } from 'react';
import { ChevronDown, Plus, Radio, Terminal } from 'lucide-react';
import type { ResearchSession } from '../../types/research';

interface TopBarProps {
  session: ResearchSession | null;
  sessionsList: Array<{ id: string; question: string; title: string; status: string; stats?: any; is_demo?: boolean }>;
  onSelectSession: (id: string) => void;
  onNewInquiry: () => void;
  onToggleDemoMode: () => void;
  onToggleObservatory: () => void;
  isObservatoryOpen: boolean;
  onNavigateHome: () => void;
}

export function TopBar({
  session,
  sessionsList,
  onSelectSession,
  onNewInquiry,
  onToggleDemoMode,
  onToggleObservatory,
  isObservatoryOpen,
  onNavigateHome,
}: TopBarProps) {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header className="shell-topbar">
      {/* Brand & Logo */}
      <div className="topbar-brand" onClick={onNavigateHome}>
        <div className="brand-glyph">N</div>
        <div className="brand-text">
          <span className="brand-title">NEXUS</span>
          <span className="brand-subtitle">AI Research Scientist</span>
        </div>
      </div>

      {/* Active Question Bar & Session Switcher */}
      {session && (
        <div className="topbar-question-pill" ref={dropdownRef} style={{ position: 'relative', cursor: 'pointer' }} onClick={() => setDropdownOpen(!dropdownOpen)}>
          <Radio size={12} className="question-icon" />
          <span className="question-text" title={session.question}>
            {session.question || 'Active Research Investigation'}
          </span>
          <ChevronDown size={14} style={{ color: 'var(--text-tertiary)', marginLeft: 'auto' }} />

          {/* Session Switcher Dropdown */}
          {dropdownOpen && (
            <div
              style={{
                position: 'absolute',
                top: '100%',
                left: 0,
                right: 0,
                marginTop: 6,
                background: 'var(--bg-secondary)',
                border: '1px solid var(--border-secondary)',
                borderRadius: 'var(--radius-md)',
                boxShadow: 'var(--shadow-elevated)',
                maxHeight: 280,
                overflowY: 'auto',
                zIndex: 50,
                padding: 6,
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)', padding: '6px 8px', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
                Active & Previous Investigations
              </div>
              {sessionsList.map((s) => (
                <div
                  key={s.id}
                  onClick={() => {
                    onSelectSession(s.id);
                    setDropdownOpen(false);
                  }}
                  style={{
                    padding: '8px 10px',
                    borderRadius: 'var(--radius-xs)',
                    background: s.id === session.id ? 'var(--bg-elevated)' : 'transparent',
                    borderLeft: s.id === session.id ? '2px solid var(--accent-steel)' : 'none',
                    cursor: 'pointer',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 2,
                    marginBottom: 2,
                  }}
                >
                  <div style={{ fontSize: 12, fontWeight: s.id === session.id ? 600 : 400, color: 'var(--text-primary)', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                    {s.question || s.title || s.id}
                  </div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)' }}>
                    ID: {s.id.slice(0, 8)} · Status: {s.status}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Right Topbar Actions */}
      <div className="topbar-actions">
        {/* Demo / Live Toggle */}
        <button
          onClick={onToggleDemoMode}
          className="telemetry-chip"
          style={{ cursor: 'pointer' }}
          title="Toggle between Live LLM and Deterministic Demo Data"
        >
          <span className="chip-label">EXECUTION:</span>
          <span
            className="chip-value"
            style={{ color: session?.is_demo ? 'var(--accent-copper)' : 'var(--accent-teal)' }}
          >
            {session?.is_demo ? 'DEMO REPLAY' : 'LIVE AGENT'}
          </span>
        </button>

        {/* New Inquiry CTA */}
        <button
          onClick={onNewInquiry}
          className="action-btn-primary"
          title="Open new scientific research investigation"
        >
          <Plus size={13} />
          <span>New Inquiry</span>
        </button>

        {/* Observatory Toggle */}
        <button
          onClick={onToggleObservatory}
          className="action-btn-secondary"
          style={{
            borderColor: isObservatoryOpen ? 'var(--accent-steel)' : 'var(--border-secondary)',
            color: isObservatoryOpen ? 'var(--accent-steel)' : 'var(--text-secondary)',
          }}
          title="Toggle live agent telemetry & trace observatory console"
        >
          <Terminal size={13} />
          <span>Observatory</span>
        </button>
      </div>
    </header>
  );
}
