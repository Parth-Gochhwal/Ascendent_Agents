import React from 'react';
import {
  Compass,
  BookOpen,
  Layers,
  Settings2,
  Split,
  Users,
  Search,
  Sparkles,
  FlaskConical,
  ShieldAlert,
  ShieldCheck,
  FileText,
  Share2,
  GitCommit,
} from 'lucide-react';
import type { PageId, ResearchSession } from '../../types/research';

interface SidebarProps {
  activePage: PageId;
  onNavigate: (page: PageId) => void;
  session: ResearchSession | null;
}

interface NavModule {
  id: PageId;
  index: string;
  label: string;
  icon: React.ReactNode;
  countKey?: string;
  customCount?: number;
}

export function Sidebar({ activePage, onNavigate, session }: SidebarProps) {
  const stats = session?.stats || {};

  const modules: NavModule[] = [
    { id: 'overview', index: '01', label: 'QUESTION', icon: <Compass size={14} /> },
    { id: 'literature', index: '02', label: 'LITERATURE', icon: <BookOpen size={14} />, countKey: 'papers_discovered' },
    { id: 'evidence', index: '03', label: 'EVIDENCE', icon: <Layers size={14} />, countKey: 'claims_extracted' },
    { id: 'methods', index: '04', label: 'METHODS', icon: <Settings2 size={14} />, countKey: 'methods_extracted' },
    { id: 'contradictions', index: '05', label: 'CONTRADICTIONS', icon: <Split size={14} />, countKey: 'contradictions_found' },
    { id: 'consensus', index: '06', label: 'CONSENSUS', icon: <Users size={14} />, countKey: 'consensus_findings' },
    { id: 'gaps', index: '07', label: 'GAPS & ATLAS', icon: <Search size={14} />, countKey: 'research_gaps' },
    { id: 'novelty', index: '08', label: 'NOVELTY', icon: <Sparkles size={14} /> },
    { id: 'experiment', index: '09', label: 'EXPERIMENT', icon: <FlaskConical size={14} /> },
    { id: 'redteam', index: '10', label: 'RED TEAM', icon: <ShieldAlert size={14} /> },
    { id: 'integrity', index: '11', label: 'INTEGRITY', icon: <ShieldCheck size={14} /> },
    { id: 'dossier', index: '12', label: 'DOSSIER', icon: <FileText size={14} /> },
  ];

  const lenses: NavModule[] = [
    { id: 'graph', index: '◆', label: 'CITATION GRAPH', icon: <Share2 size={14} />, countKey: 'citations_mapped' },
    { id: 'timeline', index: '◆', label: 'TIMELINE', icon: <GitCommit size={14} /> },
  ];

  return (
    <aside className="shell-sidebar">
      <div className="sidebar-header-label">RESEARCH PROGRESSION</div>

      <nav className="sidebar-nav">
        {modules.map((m) => {
          const count = m.countKey ? stats[m.countKey] : m.customCount;
          const isActive = activePage === m.id;

          return (
            <div
              key={m.id}
              className={`nav-module-item ${isActive ? 'active' : ''}`}
              onClick={() => onNavigate(m.id)}
            >
              <div className="nav-module-left">
                <span className="nav-module-idx">{m.index}</span>
                <span style={{ color: isActive ? 'var(--accent-steel)' : 'var(--text-tertiary)', display: 'flex' }}>
                  {m.icon}
                </span>
                <span className="nav-module-title">{m.label}</span>
              </div>
              {count != null && count > 0 && (
                <span className="nav-module-badge">{count}</span>
              )}
            </div>
          );
        })}

        <div className="sidebar-header-label" style={{ marginTop: 'var(--space-3)' }}>
          INTELLIGENCE LENSES
        </div>

        {lenses.map((m) => {
          const count = m.countKey ? stats[m.countKey] : undefined;
          const isActive = activePage === m.id;

          return (
            <div
              key={m.id}
              className={`nav-module-item ${isActive ? 'active' : ''}`}
              onClick={() => onNavigate(m.id)}
            >
              <div className="nav-module-left">
                <span className="nav-module-idx" style={{ fontSize: 9 }}>{m.index}</span>
                <span style={{ color: isActive ? 'var(--accent-steel)' : 'var(--text-tertiary)', display: 'flex' }}>
                  {m.icon}
                </span>
                <span className="nav-module-title">{m.label}</span>
              </div>
              {count != null && count > 0 && (
                <span className="nav-module-badge">{count}</span>
              )}
            </div>
          );
        })}
      </nav>

      {/* Footer telemetry */}
      <div className="sidebar-footer">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)' }}>SESSION STATUS</span>
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 10,
              color: session?.status === 'report_ready' ? 'var(--accent-teal)' : 'var(--accent-steel)',
              textTransform: 'uppercase',
            }}
          >
            {session?.status || 'IDLE'}
          </span>
        </div>
      </div>
    </aside>
  );
}
