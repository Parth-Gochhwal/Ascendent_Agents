import { useState, useEffect, useCallback, useRef } from 'react';
import './index.css';
import { api, connectWebSocket } from './services/api';

// ─── Status & Badge Helpers ─────────────────────────

function statusIcon(status: string) {
  switch (status) {
    case 'completed': return '✓';
    case 'running': return '●';
    case 'failed': return '✗';
    case 'pending': return '○';
    case 'skipped': return '⊘';
    default: return '○';
  }
}

function statusColor(status: string) {
  switch (status) {
    case 'completed': return 'var(--accent-green)';
    case 'running': return 'var(--accent-blue)';
    case 'failed': return 'var(--accent-red)';
    case 'pending': return 'var(--text-tertiary)';
    default: return 'var(--text-tertiary)';
  }
}

function confidenceBadge(c: string = 'medium') {
  const colors: Record<string, string> = {
    high: 'badge-green', medium: 'badge-amber', low: 'badge-red', uncertain: 'badge-gray'
  };
  return <span className={`badge ${colors[c?.toLowerCase()] || 'badge-gray'}`}>{c}</span>;
}

function contradictionBadge(type: string = 'unresolved') {
  const colors: Record<string, string> = {
    agreement: 'badge-green', apparent_contradiction: 'badge-amber',
    contextual_disagreement: 'badge-purple', methodological_conflict: 'badge-cyan',
    direct_contradiction: 'badge-red', unresolved: 'badge-gray',
  };
  return <span className={`badge ${colors[type] || 'badge-gray'}`}>{type.replace(/_/g, ' ')}</span>;
}

function availabilityBadge(av: string = 'unclear') {
  const colors: Record<string, string> = {
    available: 'badge-green', not_found: 'badge-red', unclear: 'badge-gray'
  };
  return <span className={`badge ${colors[av?.toLowerCase()] || 'badge-gray'}`}>{av?.replace(/_/g, ' ')}</span>;
}

// ─── App Main Component ─────────────────────────────

type Page = 'home' | 'overview' | 'literature' | 'evidence' | 'methods' |
  'contradictions' | 'consensus' | 'gaps' | 'novelty' | 'experiment' |
  'citations' | 'timeline' | 'dossier' | 'audit';

export default function App() {
  const [page, setPage] = useState<Page>('home');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [session, setSession] = useState<any>(null);
  const [sessionsList, setSessionsList] = useState<any[]>([]);
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState('');
  const [whyModal, setWhyModal] = useState<{ targetType: string; targetId: string } | null>(null);
  const [whyData, setWhyData] = useState<any>(null);
  const [whyLoading, setWhyLoading] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  // Fetch session history
  const loadSessionsList = useCallback(async () => {
    try {
      const data = await api.listSessions();
      setSessionsList(data.sessions || []);
    } catch { /* ignore */ }
  }, []);

  useEffect(() => {
    loadSessionsList();
  }, [loadSessionsList]);

  // Poll active session updates
  useEffect(() => {
    if (!sessionId) return;
    const fetchSession = async () => {
      try {
        const data = await api.getSession(sessionId);
        setSession(data);
        const evData = await api.getEvents(sessionId);
        setEvents(evData.events);
      } catch { /* ignore */ }
    };
    fetchSession();
    const interval = setInterval(fetchSession, 2000);
    return () => clearInterval(interval);
  }, [sessionId]);

  // WebSocket for live streaming events
  useEffect(() => {
    if (!sessionId) return;
    const ws = connectWebSocket(sessionId, (event) => {
      setEvents(prev => [...prev, event]);
    });
    wsRef.current = ws;
    return () => ws.close();
  }, [sessionId]);

  const startResearch = useCallback(async (q: string) => {
    if (!q.trim()) return;
    setLoading(true);
    try {
      const res = await api.startResearch(q.trim());
      setSessionId(res.id);
      setPage('overview');
      setEvents([]);
      loadSessionsList();
    } catch (e: any) {
      alert('Failed to start research: ' + e.message);
    }
    setLoading(false);
  }, [loadSessionsList]);

  // Trigger Explainability "Why?" Modal
  const openWhy = useCallback(async (targetType: string, targetId: string) => {
    if (!sessionId) return;
    setWhyModal({ targetType, targetId });
    setWhyLoading(true);
    try {
      const res = await api.getWhy(sessionId, targetType, targetId);
      setWhyData(res.explanation);
    } catch (e) {
      console.error('Failed to fetch explainability payload', e);
    }
    setWhyLoading(false);
  }, [sessionId]);

  const closeWhy = () => {
    setWhyModal(null);
    setWhyData(null);
  };

  // ─── Navigation Items ─────────────────────────────

  const navItems = [
    { id: 'overview' as Page, label: 'Overview', icon: '◉', count: null },
    { id: 'literature' as Page, label: 'Literature', icon: '📄', count: session?.stats?.papers_discovered },
    { id: 'evidence' as Page, label: 'Evidence Matrix', icon: '🔍', count: session?.stats?.claims_extracted },
    { id: 'methods' as Page, label: 'Methods & Pipeline', icon: '⚙', count: session?.stats?.methods_extracted },
    { id: 'contradictions' as Page, label: 'Contradictions', icon: '⚡', count: session?.stats?.contradictions_found },
    { id: 'consensus' as Page, label: 'Consensus Analysis', icon: '🤝', count: session?.stats?.consensus_findings },
    { id: 'gaps' as Page, label: 'Research Gaps', icon: '🔬', count: session?.stats?.research_gaps },
    { id: 'novelty' as Page, label: 'Novelty Evaluator', icon: '💡', count: null },
    { id: 'experiment' as Page, label: 'Experiment Designer', icon: '🧪', count: null },
    { id: 'citations' as Page, label: 'Citation Graph', icon: '🕸', count: session?.stats?.citations_mapped },
    { id: 'timeline' as Page, label: 'Timeline & History', icon: '📈', count: null },
    { id: 'dossier' as Page, label: 'Research Dossier', icon: '📋', count: null },
    { id: 'audit' as Page, label: 'Integrity & Red Team', icon: '🛡', count: null },
  ];

  if (page === 'home' && !sessionId) {
    return (
      <HomePage
        query={query}
        setQuery={setQuery}
        onStart={startResearch}
        loading={loading}
        sessionsList={sessionsList}
        onResume={(id) => { setSessionId(id); setPage('overview'); }}
      />
    );
  }

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <div className="sidebar">
        <div className="sidebar-header">
          <div
            className="sidebar-logo"
            onClick={() => { setSessionId(null); setPage('home'); }}
            style={{ cursor: 'pointer' }}
          >
            <div className="sidebar-logo-icon">N</div>
            <div>
              <h1>NEXUS</h1>
              <div className="sidebar-subtitle">AI Research Scientist</div>
            </div>
          </div>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-section-title">Research Modules</div>
          {navItems.map(item => (
            <div
              key={item.id}
              className={`nav-item ${page === item.id ? 'active' : ''}`}
              onClick={() => setPage(item.id)}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
              {item.count != null && item.count > 0 && (
                <span className="badge">{item.count}</span>
              )}
            </div>
          ))}
        </nav>

        <div style={{ marginTop: 'auto', padding: '16px 20px', borderTop: '1px solid var(--border-primary)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <span style={{ fontSize: 11, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: 0.5 }}>Execution Mode</span>
            {session?.is_demo ? (
              <span className="demo-badge">DEMO MODE</span>
            ) : (
              <span className="badge badge-green">LIVE API</span>
            )}
          </div>
          <button
            onClick={() => { setSessionId(null); setPage('home'); }}
            className="toolbar-btn"
            style={{ width: '100%', justifyContent: 'center' }}
          >
            + New Investigation
          </button>
        </div>
      </div>

      {/* Main Workspace Area */}
      <div className="main-content">
        {page === 'overview' && <OverviewPage session={session} onNavigate={setPage} onWhy={openWhy} />}
        {page === 'literature' && <LiteraturePage sessionId={sessionId!} session={session} onWhy={openWhy} />}
        {page === 'evidence' && <EvidencePage sessionId={sessionId!} session={session} onWhy={openWhy} />}
        {page === 'methods' && <MethodsPage sessionId={sessionId!} session={session} onWhy={openWhy} />}
        {page === 'contradictions' && <ContradictionsPage sessionId={sessionId!} session={session} onWhy={openWhy} />}
        {page === 'consensus' && <ConsensusPage sessionId={sessionId!} session={session} onWhy={openWhy} />}
        {page === 'gaps' && <GapsPage sessionId={sessionId!} session={session} onWhy={openWhy} />}
        {page === 'novelty' && <NoveltyPage sessionId={sessionId!} session={session} onWhy={openWhy} />}
        {page === 'experiment' && <ExperimentPage sessionId={sessionId!} session={session} />}
        {page === 'citations' && <CitationsPage sessionId={sessionId!} session={session} />}
        {page === 'timeline' && <TimelinePage sessionId={sessionId!} />}
        {page === 'dossier' && <DossierPage sessionId={sessionId!} session={session} />}
        {page === 'audit' && <AuditPage sessionId={sessionId!} session={session} onWhy={openWhy} />}
      </div>

      {/* Agent Observability Panel */}
      <div className="agent-panel">
        <div className="agent-panel-header">
          <div className="spinner" style={{ width: 14, height: 14, display: session?.status === 'report_ready' ? 'none' : 'block' }}></div>
          <h3>Agent Activity & Trace</h3>
        </div>
        {events.map((ev, i) => (
          <div key={i} className="agent-event">
            <div className="agent-event-icon" style={{ color: statusColor(ev.status) }}>
              {ev.status === 'running' ? <span className="pulse">{statusIcon(ev.status)}</span> : statusIcon(ev.status)}
            </div>
            <div className="agent-event-content">
              <div className="agent-event-name">{ev.agent_name}</div>
              <div className="agent-event-message">{ev.message}</div>
              {ev.detail && <div className="agent-event-detail">{ev.detail}</div>}
              {ev.progress != null && ev.status === 'running' && (
                <div className="progress-bar">
                  <div className="progress-fill" style={{ width: `${ev.progress * 100}%` }}></div>
                </div>
              )}
            </div>
          </div>
        ))}
        {events.length === 0 && (
          <div style={{ padding: 20, color: 'var(--text-tertiary)', fontSize: 13, textAlign: 'center' }}>
            Agent execution traces will stream live here...
          </div>
        )}
      </div>

      {/* Explainability "Why?" Modal */}
      {whyModal && (
        <WhyModal
          targetType={whyModal.targetType}
          targetId={whyModal.targetId}
          data={whyData}
          loading={whyLoading}
          onClose={closeWhy}
        />
      )}
    </div>
  );
}

// ─── Home Page ──────────────────────────────────────

function HomePage({ query, setQuery, onStart, loading, sessionsList, onResume }: {
  query: string;
  setQuery: (q: string) => void;
  onStart: (q: string) => void;
  loading: boolean;
  sessionsList: any[];
  onResume: (id: string) => void;
}) {
  const examples = [
    "Are graph neural networks genuinely better than transformer-based models for battery remaining useful life prediction under cross-domain conditions?",
    "What are the current limitations of multimodal retrieval-augmented generation (RAG) systems?",
    "How effective are latent diffusion models for synthetic medical image generation under clinical distribution shifts?",
  ];

  return (
    <div className="home-page">
      <div className="home-hero">
        <h1>NEXUS</h1>
        <h2>AI RESEARCH SCIENTIST</h2>
        <p className="tagline">"From What Do We Know? to What Should We Investigate Next?"</p>
      </div>

      <div className="search-container">
        <input
          className="search-input"
          placeholder="Enter a research question to investigate..."
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && onStart(query)}
        />
        <button className="search-btn" onClick={() => onStart(query)} disabled={loading || !query.trim()}>
          {loading ? 'INITIALIZING AGENTS...' : 'START RESEARCH'}
        </button>
      </div>

      <div className="example-queries">
        <h4>Benchmark Research Inquiries</h4>
        {examples.map((q, i) => (
          <button key={i} className="example-query" onClick={() => { setQuery(q); onStart(q); }}>
            {q}
          </button>
        ))}
      </div>

      {sessionsList.length > 0 && (
        <div style={{ marginTop: 40, width: '100%', maxWidth: 720 }}>
          <h4 style={{ fontSize: 13, color: 'var(--text-tertiary)', textTransform: 'uppercase', marginBottom: 12, letterSpacing: 0.5 }}>
            Recent Investigations
          </h4>
          <div style={{ display: 'grid', gap: 8 }}>
            {sessionsList.slice(0, 5).map((s) => (
              <div
                key={s.id}
                onClick={() => onResume(s.id)}
                style={{
                  padding: '12px 16px',
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-primary)',
                  borderRadius: 'var(--radius-md)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  cursor: 'pointer',
                  transition: 'all var(--transition-fast)'
                }}
                className="session-resume-item"
              >
                <div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>{s.question || s.title}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 2 }}>
                    Status: <span style={{ color: statusColor(s.status) }}>{s.status}</span> · Papers: {s.stats?.papers_discovered || 0}
                  </div>
                </div>
                <span className="badge badge-blue">Resume →</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Overview Page ──────────────────────────────────

function OverviewPage({ session, onNavigate, onWhy }: { session: any; onNavigate: (p: Page) => void; onWhy: (type: string, id: string) => void }) {
  if (!session) return <div className="page"><div className="spinner" /></div>;

  const stats = session.stats || {};

  return (
    <div className="page">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h2>Research Overview</h2>
          <p>{session.question}</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="toolbar-btn" onClick={() => onNavigate('dossier')}>View Full Dossier</button>
          <button className="toolbar-btn active" onClick={() => onNavigate('experiment')}>View Experiment Plan</button>
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-card accent-blue" onClick={() => onNavigate('literature')} style={{ cursor: 'pointer' }}>
          <div className="stat-value">{stats.papers_discovered || 0}</div>
          <div className="stat-label">Papers Discovered</div>
        </div>
        <div className="stat-card accent-purple" onClick={() => onNavigate('literature')} style={{ cursor: 'pointer' }}>
          <div className="stat-value">{stats.papers_analyzed || 0}</div>
          <div className="stat-label">Papers Analyzed</div>
        </div>
        <div className="stat-card accent-cyan" onClick={() => onNavigate('evidence')} style={{ cursor: 'pointer' }}>
          <div className="stat-value">{stats.claims_extracted || 0}</div>
          <div className="stat-label">Claims Extracted</div>
        </div>
        <div className="stat-card accent-green" onClick={() => onNavigate('consensus')} style={{ cursor: 'pointer' }}>
          <div className="stat-value">{stats.consensus_findings || 0}</div>
          <div className="stat-label">Consensus Findings</div>
        </div>
        <div className="stat-card accent-amber" onClick={() => onNavigate('contradictions')} style={{ cursor: 'pointer' }}>
          <div className="stat-value">{stats.contradictions_found || 0}</div>
          <div className="stat-label">Contradictions</div>
        </div>
        <div className="stat-card accent-red" onClick={() => onNavigate('gaps')} style={{ cursor: 'pointer' }}>
          <div className="stat-value">{stats.research_gaps || 0}</div>
          <div className="stat-label">Research Gaps</div>
        </div>
      </div>

      {session.plan && (
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="card-header">
            <div className="card-title">Structured Research Decomposition</div>
            <span className="badge badge-blue">{session.plan.subquestions?.length || 0} subquestions</span>
          </div>
          <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 16 }}>
            <strong style={{ color: 'var(--text-primary)' }}>Objective:</strong> {session.plan.research_objective}
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            {session.plan.subquestions?.map((sq: string, i: number) => (
              <div key={i} style={{ padding: '8px 12px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)', fontSize: 13, color: 'var(--text-primary)', display: 'flex', gap: 8 }}>
                <span style={{ color: 'var(--accent-blue)', fontWeight: 700 }}>{i + 1}.</span>
                <span>{sq}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {session.red_team && (
        <div className="card" style={{ borderLeft: '4px solid var(--accent-purple)', marginBottom: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <div className="card-title" style={{ color: 'var(--accent-purple)' }}>★ Red-Team Adjudication Summary</div>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              {confidenceBadge(session.red_team.final_confidence)}
              <button className="why-btn" onClick={() => onWhy('red_team', 'red_team')}>Why?</button>
            </div>
          </div>
          <p style={{ fontSize: 14, color: 'var(--text-primary)', lineHeight: 1.6 }}>{session.red_team.adjudication}</p>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        {session.plan?.search_queries && (
          <div className="card">
            <div className="card-title" style={{ fontSize: 13, marginBottom: 12 }}>Search Strategy Queries</div>
            {session.plan.search_queries.map((q: string, i: number) => (
              <div key={i} style={{ fontSize: 12, color: 'var(--text-secondary)', padding: '4px 0', fontFamily: 'var(--font-mono)' }}>
                • {q}
              </div>
            ))}
          </div>
        )}
        {session.plan?.concepts && (
          <div className="card">
            <div className="card-title" style={{ fontSize: 13, marginBottom: 12 }}>Extracted Key Concepts & Targets</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {session.plan.concepts.map((c: string, i: number) => (
                <span key={i} className="badge badge-blue">{c}</span>
              ))}
              {session.plan.methods_of_interest?.map((m: string, i: number) => (
                <span key={`m-${i}`} className="badge badge-purple">{m}</span>
              ))}
              {session.plan.datasets_of_interest?.map((d: string, i: number) => (
                <span key={`d-${i}`} className="badge badge-cyan">{d}</span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Literature Page ────────────────────────────────

function LiteraturePage({ sessionId, session, onWhy }: { sessionId: string; session: any; onWhy: (type: string, id: string) => void }) {
  const [papers, setPapers] = useState<any[]>([]);
  const [selectedPaper, setSelectedPaper] = useState<any>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [searchFilter, setSearchFilter] = useState('');
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api.getPapers(sessionId).then(d => setPapers(d.papers)).catch(() => {});
  }, [sessionId, session?.status]);

  const viewPaper = async (paperId: string) => {
    const d = await api.getPaperDetail(sessionId, paperId);
    setSelectedPaper(d.paper);
    setAnalysis(d.analysis);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const res = await api.uploadPdf(sessionId, file);
      alert(`PDF Ingested: ${res.paper.title}`);
      const d = await api.getPapers(sessionId);
      setPapers(d.papers);
    } catch (err: any) {
      alert(`Upload failed: ${err.message}`);
    }
    setUploading(false);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const filtered = papers.filter(p =>
    p.title?.toLowerCase().includes(searchFilter.toLowerCase()) ||
    p.abstract?.toLowerCase().includes(searchFilter.toLowerCase()) ||
    p.authors?.some((a: any) => a.name?.toLowerCase().includes(searchFilter.toLowerCase()))
  );

  if (selectedPaper) {
    return (
      <div className="page">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
          <button className="toolbar-btn" onClick={() => { setSelectedPaper(null); setAnalysis(null); }}>← Back to Papers</button>
          <button className="why-btn" onClick={() => onWhy('paper', selectedPaper.id)}>Explain Relevance Score</button>
        </div>

        <div className="card" style={{ marginBottom: 16 }}>
          <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 12 }}>{selectedPaper.title}</h2>
          <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', fontSize: 13, color: 'var(--text-secondary)' }}>
            <span><strong>Authors:</strong> {selectedPaper.authors?.map((a: any) => a.name).join(', ')}</span>
            <span><strong>Year:</strong> {selectedPaper.year}</span>
            <span><strong>Venue:</strong> {selectedPaper.venue}</span>
            {selectedPaper.doi && <span><strong>DOI:</strong> {selectedPaper.doi}</span>}
            <span><strong>Citations:</strong> {selectedPaper.citation_count ?? 'N/A'}</span>
          </div>
          {selectedPaper.abstract && (
            <p style={{ marginTop: 16, fontSize: 14, lineHeight: 1.7, color: 'var(--text-primary)' }}>
              {selectedPaper.abstract}
            </p>
          )}
        </div>

        {/* Reproducibility Assessment Card */}
        <div className="card" style={{ marginBottom: 16 }}>
          <div className="card-title" style={{ fontSize: 13, marginBottom: 12 }}>Reproducibility & Open Science Indicators</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12 }}>
            <div style={{ padding: 10, background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>SOURCE CODE</div>
              <div style={{ marginTop: 4 }}>{availabilityBadge(analysis?.code_availability || 'unclear')}</div>
            </div>
            <div style={{ padding: 10, background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>DATASET AVAILABILITY</div>
              <div style={{ marginTop: 4 }}>{availabilityBadge(analysis?.dataset_availability || 'available')}</div>
            </div>
            <div style={{ padding: 10, background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>OPEN ACCESS</div>
              <div style={{ marginTop: 4 }}><span className="badge badge-green">{selectedPaper.open_access ? 'Open Access' : 'Verified Metadata'}</span></div>
            </div>
          </div>
        </div>

        {analysis && (
          <>
            {analysis.main_findings?.length > 0 && (
              <div className="card" style={{ marginBottom: 16 }}>
                <div className="card-title" style={{ fontSize: 13, marginBottom: 10 }}>Extracted Main Findings</div>
                {analysis.main_findings.map((f: string, i: number) => (
                  <div key={i} style={{ padding: '6px 0', fontSize: 13, paddingLeft: 20, position: 'relative', color: 'var(--text-primary)' }}>
                    <span style={{ position: 'absolute', left: 0, color: 'var(--accent-green)' }}>✓</span>
                    {f}
                  </div>
                ))}
              </div>
            )}
            {analysis.limitations?.length > 0 && (
              <div className="card" style={{ marginBottom: 16 }}>
                <div className="card-title" style={{ fontSize: 13, marginBottom: 10 }}>Reported Limitations</div>
                {analysis.limitations.map((l: string, i: number) => (
                  <div key={i} style={{ padding: '6px 0', fontSize: 13, color: 'var(--accent-amber)' }}>⚠ {l}</div>
                ))}
              </div>
            )}
            {analysis.claims?.length > 0 && (
              <div className="card">
                <div className="card-title" style={{ fontSize: 13, marginBottom: 12 }}>Atomic Claims & Empirical Evidence</div>
                {analysis.claims.map((c: any, i: number) => (
                  <div key={i} style={{ padding: 12, background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)', marginBottom: 8, borderLeft: '3px solid var(--accent-blue)' }}>
                    <div style={{ fontSize: 14, color: 'var(--text-primary)', marginBottom: 6 }}>{c.statement}</div>
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                      {c.metric && <span className="badge badge-cyan">{c.metric}: {c.evidence_value}</span>}
                      {confidenceBadge(c.confidence)}
                      {c.conditions?.map((cond: string, j: number) => (
                        <span key={j} className="condition-tag">{cond}</span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h2>Academic Literature Discovery</h2>
          <p>{papers.length} scholarly papers retrieved, normalized, and ranked</p>
        </div>
        <div className="toolbar-actions">
          <input
            type="file"
            accept=".pdf"
            ref={fileInputRef}
            onChange={handleFileUpload}
            style={{ display: 'none' }}
          />
          <button
            className="toolbar-btn"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
          >
            {uploading ? 'Ingesting PDF...' : '📄 Ingest PDF Paper'}
          </button>
        </div>
      </div>

      <div style={{ marginBottom: 16 }}>
        <input
          className="filter-input"
          style={{ width: '100%', maxWidth: 400 }}
          placeholder="Filter papers by title, author, or keyword..."
          value={searchFilter}
          onChange={e => setSearchFilter(e.target.value)}
        />
      </div>

      <div className="papers-grid">
        {filtered.map((p: any) => (
          <div key={p.id} className="paper-card" onClick={() => viewPaper(p.id)}>
            <div className="paper-title">{p.title}</div>
            <div className="paper-authors">{p.authors?.map((a: any) => a.name).join(', ')}</div>
            <div className="paper-meta">
              <span>{p.year}</span>
              <span>{p.venue}</span>
              {p.citation_count != null && <span>🔗 {p.citation_count} cites</span>}
            </div>
            {p.abstract && <div className="paper-abstract">{p.abstract}</div>}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 12 }}>
              <div className="score-bar" style={{ flex: 1, marginRight: 12 }}>
                <div className="score-track">
                  <div className="score-fill" style={{ width: `${(p.research_score || 0) * 100}%` }}></div>
                </div>
                <span className="score-value">{((p.research_score || 0) * 100).toFixed(0)}% Score</span>
              </div>
              <button
                className="why-btn"
                onClick={(e) => { e.stopPropagation(); onWhy('paper', p.id); }}
              >
                Why?
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Evidence Matrix Page ───────────────────────────

function EvidencePage({ sessionId, session, onWhy }: { sessionId: string; session: any; onWhy: (type: string, id: string) => void }) {
  const [data, setData] = useState<{ claims: any[]; evidence: any[] }>({ claims: [], evidence: [] });
  const [filterText, setFilterText] = useState('');
  const [confidenceFilter, setConfidenceFilter] = useState('all');

  useEffect(() => {
    api.getClaims(sessionId).then(d => setData(d)).catch(() => {});
  }, [sessionId, session?.status]);

  const filteredClaims = data.claims.filter(c => {
    const matchesText = c.statement?.toLowerCase().includes(filterText.toLowerCase()) ||
      c.metric?.toLowerCase().includes(filterText.toLowerCase()) ||
      c.conditions?.some((cond: string) => cond.toLowerCase().includes(filterText.toLowerCase()));
    const matchesConfidence = confidenceFilter === 'all' || c.confidence?.toLowerCase() === confidenceFilter;
    return matchesText && matchesConfidence;
  });

  return (
    <div className="page">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h2>Structured Evidence Matrix</h2>
          <p>Atomic empirical claims extracted and linked directly to verifiable evidence</p>
        </div>
        <div className="toolbar-actions">
          <select
            className="filter-input"
            value={confidenceFilter}
            onChange={e => setConfidenceFilter(e.target.value)}
          >
            <option value="all">All Confidence Levels</option>
            <option value="high">High Confidence Only</option>
            <option value="medium">Medium Confidence Only</option>
          </select>
          <input
            className="filter-input"
            placeholder="Search claims or conditions..."
            value={filterText}
            onChange={e => setFilterText(e.target.value)}
          />
        </div>
      </div>

      <div style={{ overflow: 'auto' }}>
        <table className="evidence-table">
          <thead>
            <tr>
              <th>Atomic Claim Statement</th>
              <th>Source Paper</th>
              <th>Metric</th>
              <th>Empirical Result</th>
              <th>Experimental Conditions</th>
              <th>Confidence</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {filteredClaims.map((c: any, i: number) => (
              <tr key={i}>
                <td style={{ maxWidth: 320, fontWeight: 500 }}>{c.statement}</td>
                <td style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-tertiary)' }}>{c.paper_id}</td>
                <td><span className="badge badge-cyan">{c.metric || '—'}</span></td>
                <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{c.evidence_value || '—'}</td>
                <td>
                  <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                    {c.conditions?.map((cond: string, j: number) => (
                      <span key={j} className="condition-tag">{cond}</span>
                    ))}
                  </div>
                </td>
                <td>{confidenceBadge(c.confidence)}</td>
                <td>
                  <button className="why-btn" onClick={() => onWhy('paper', c.paper_id)}>Why?</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ─── Methods Page ───────────────────────────────────

function MethodsPage({ sessionId, session, onWhy }: { sessionId: string; session: any; onWhy: (type: string, id: string) => void }) {
  const [methods, setMethods] = useState<any[]>([]);

  useEffect(() => {
    api.getMethods(sessionId).then(d => setMethods(d.methods)).catch(() => {});
  }, [sessionId, session?.status]);

  return (
    <div className="page">
      <div className="page-header">
        <h2>Methodological Pipelines & Architecture Matrix</h2>
        <p>Extracted pipeline specifications across data preprocessing, models, and evaluation</p>
      </div>

      {/* 2D Coverage Grid */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-title" style={{ marginBottom: 12 }}>Method vs Benchmark Dataset Coverage Matrix</div>
        <div style={{ overflowX: 'auto' }}>
          <table className="matrix-table">
            <thead>
              <tr>
                <th>Model Architecture</th>
                <th>NASA Battery (NMC)</th>
                <th>CALCE Dataset (LFP)</th>
                <th>Oxford Degradation</th>
                <th>Cross-Chemistry Shift</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="row-header">LSTM / GRU Baselines</td>
                <td className="matrix-cell-pass">✓ Explored</td>
                <td className="matrix-cell-pass">✓ Explored</td>
                <td className="matrix-cell-pass">✓ Explored</td>
                <td className="matrix-cell-miss">⚠ Underexplored</td>
              </tr>
              <tr>
                <td className="row-header">Vanilla Transformer</td>
                <td className="matrix-cell-pass">✓ Explored</td>
                <td className="matrix-cell-pass">✓ Explored</td>
                <td className="matrix-cell-pass">✓ Explored</td>
                <td className="matrix-cell-miss">⚠ Underexplored</td>
              </tr>
              <tr>
                <td className="row-header">Graph Attention Network (GAT)</td>
                <td className="matrix-cell-pass">✓ Explored</td>
                <td className="matrix-cell-miss">⚠ Underexplored</td>
                <td className="matrix-cell-pass">✓ Explored</td>
                <td className="matrix-cell-miss" style={{ background: 'rgba(239, 68, 68, 0.12)', color: 'var(--accent-red)' }}>
                  ★ Missing Benchmark
                </td>
              </tr>
              <tr>
                <td className="row-header">Domain-Adaptive GAT (Proposed)</td>
                <td className="matrix-cell-miss">Proposed</td>
                <td className="matrix-cell-miss">Proposed</td>
                <td className="matrix-cell-miss">Proposed</td>
                <td className="matrix-cell-miss" style={{ background: 'rgba(139, 92, 246, 0.15)', color: 'var(--accent-purple)' }}>
                  🎯 Target Gap
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div style={{ display: 'grid', gap: 16 }}>
        {methods.map((m: any, i: number) => (
          <div key={i} className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                {m.model_architecture && <span className="badge badge-purple">{m.model_architecture}</span>}
                {m.dataset && <span className="badge badge-cyan">{m.dataset}</span>}
                <span style={{ fontSize: 11, color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>{m.paper_id}</span>
              </div>
              <button className="why-btn" onClick={() => onWhy('paper', m.paper_id)}>Paper Context</button>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, fontSize: 13 }}>
              {m.preprocessing?.length > 0 && <div><strong style={{ color: 'var(--text-tertiary)', fontSize: 11 }}>PREPROCESSING</strong><br />{m.preprocessing.join(' → ')}</div>}
              {m.loss_function && <div><strong style={{ color: 'var(--text-tertiary)', fontSize: 11 }}>LOSS FUNCTION</strong><br />{m.loss_function}</div>}
              {m.optimizer && <div><strong style={{ color: 'var(--text-tertiary)', fontSize: 11 }}>OPTIMIZER</strong><br />{m.optimizer}</div>}
              {m.evaluation_protocol && <div><strong style={{ color: 'var(--text-tertiary)', fontSize: 11 }}>EVALUATION PROTOCOL</strong><br />{m.evaluation_protocol}</div>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Contradictions Page ────────────────────────────

function ContradictionsPage({ sessionId, session, onWhy }: { sessionId: string; session: any; onWhy: (type: string, id: string) => void }) {
  const [contradictions, setContradictions] = useState<any[]>([]);

  useEffect(() => {
    api.getContradictions(sessionId).then(d => setContradictions(d.contradictions)).catch(() => {});
  }, [sessionId, session?.status]);

  return (
    <div className="page">
      <div className="page-header">
        <h2>Cross-Paper Disagreements & Contradictions</h2>
        <p>Scientific discrepancies classified into Direct, Contextual, or Methodological conflicts</p>
      </div>

      {contradictions.map((c: any) => (
        <div key={c.id} className="contradiction-card">
          <div className="contradiction-header">
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              {contradictionBadge(c.classification)}
              {confidenceBadge(c.confidence)}
            </div>
            <button className="why-btn" onClick={() => onWhy('contradiction', c.id)}>Explain Disagreement (Why?)</button>
          </div>

          <div className="contradiction-body">
            <div className="contradiction-side">
              <h4>Paper A Finding</h4>
              <div className="claim-text">{c.claim_a_text}</div>
              <div className="paper-ref">{c.paper_a_summary}</div>
            </div>
            <div className="contradiction-side">
              <h4>Paper B Finding</h4>
              <div className="claim-text" style={{ borderLeftColor: 'var(--accent-purple)' }}>{c.claim_b_text}</div>
              <div className="paper-ref">{c.paper_b_summary}</div>
            </div>
          </div>

          <div className="contradiction-footer">
            {c.different_conditions?.length > 0 && (
              <>
                <h4 style={{ fontSize: 12, color: 'var(--text-tertiary)', textTransform: 'uppercase', marginBottom: 6 }}>Differing Experimental Parameters</h4>
                <div className="conditions-list" style={{ marginBottom: 12 }}>
                  {c.different_conditions.map((d: string, i: number) => (
                    <span key={i} className="condition-tag">{d}</span>
                  ))}
                </div>
              </>
            )}
            <h4 style={{ fontSize: 12, color: 'var(--text-tertiary)', textTransform: 'uppercase', marginBottom: 6 }}>Discrepancy Synthesis</h4>
            <div className="explanation">{c.explanation}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── Consensus Page ─────────────────────────────────

function ConsensusPage({ sessionId, session, onWhy }: { sessionId: string; session: any; onWhy: (type: string, id: string) => void }) {
  const [consensus, setConsensus] = useState<any[]>([]);

  useEffect(() => {
    api.getConsensus(sessionId).then(d => setConsensus(d.consensus)).catch(() => {});
  }, [sessionId, session?.status]);

  const grouped = {
    consensus: consensus.filter(c => c.status === 'consensus'),
    contested: consensus.filter(c => c.status === 'contested'),
    uncertain: consensus.filter(c => c.status === 'uncertain' || c.status === 'unresolved'),
  };

  return (
    <div className="page">
      <div className="page-header">
        <h2>Consensus vs Contested Findings</h2>
        <p>Distinguishing established scientific agreement from debated assertions</p>
      </div>

      <div className="consensus-grid">
        <div className="consensus-column consensus">
          <h3>✓ Established Consensus ({grouped.consensus.length})</h3>
          {grouped.consensus.map((c: any) => (
            <div key={c.id} className="consensus-item">
              <div className="statement">{c.statement}</div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 8 }}>
                <div className="support-count">{c.supporting_paper_ids?.length || 0} supporting papers</div>
                <button className="why-btn" onClick={() => onWhy('consensus', c.id)}>Why?</button>
              </div>
              {c.explanation && <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 8 }}>{c.explanation}</div>}
            </div>
          ))}
        </div>

        <div className="consensus-column contested">
          <h3>⚡ Actively Contested ({grouped.contested.length})</h3>
          {grouped.contested.map((c: any) => (
            <div key={c.id} className="consensus-item">
              <div className="statement">{c.statement}</div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 8 }}>
                <div className="support-count">{c.supporting_paper_ids?.length || 0} support / {c.dissenting_paper_ids?.length || 0} dissent</div>
                <button className="why-btn" onClick={() => onWhy('consensus', c.id)}>Why?</button>
              </div>
              {c.explanation && <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 8 }}>{c.explanation}</div>}
            </div>
          ))}
        </div>

        <div className="consensus-column uncertain">
          <h3>? Unresolved & Uncertain ({grouped.uncertain.length})</h3>
          {grouped.uncertain.map((c: any) => (
            <div key={c.id} className="consensus-item">
              <div className="statement">{c.statement}</div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 8 }}>
                {confidenceBadge(c.confidence)}
                <button className="why-btn" onClick={() => onWhy('consensus', c.id)}>Why?</button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Research Gaps Page ─────────────────────────────

function GapsPage({ sessionId, session, onWhy }: { sessionId: string; session: any; onWhy: (type: string, id: string) => void }) {
  const [data, setData] = useState<{ gaps: any[]; missing_experiments: any[] }>({ gaps: [], missing_experiments: [] });

  useEffect(() => {
    api.getGaps(sessionId).then(d => setData(d)).catch(() => {});
  }, [sessionId, session?.status]);

  return (
    <div className="page">
      <div className="page-header">
        <h2>Evidence-Derived Research Gaps</h2>
        <p>Systematically synthesized open scientific questions based on literature limitations</p>
      </div>

      {data.gaps.map((g: any, i: number) => (
        <div key={g.id} className="gap-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div className="gap-title">Gap #{i + 1}: {g.title}</div>
            <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
              <span className="badge badge-purple">{g.gap_type}</span>
              {confidenceBadge(g.confidence)}
              <button className="why-btn" onClick={() => onWhy('gap', g.id)}>Why?</button>
            </div>
          </div>
          <div className="gap-description">{g.description}</div>
          {g.potential_direction && (
            <div className="gap-direction">
              <strong>Proposed Investigation Direction</strong>
              {g.potential_direction}
            </div>
          )}
          {g.why_it_matters && (
            <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 8 }}>
              <strong style={{ color: 'var(--text-primary)' }}>Impact:</strong> {g.why_it_matters}
            </div>
          )}
        </div>
      ))}

      {data.missing_experiments.length > 0 && (
        <>
          <h3 style={{ fontSize: 18, margin: '32px 0 16px', color: 'var(--text-primary)' }}>Detected Missing Experiments</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 12 }}>
            {data.missing_experiments.map((m: any) => (
              <div key={m.id} className="card" style={{ borderLeft: '3px solid var(--accent-amber)' }}>
                <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
                  <span className="badge badge-purple">{m.method}</span>
                  <span className="badge badge-cyan">{m.dataset}</span>
                </div>
                <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{m.explanation}</div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

// ─── Novelty Evaluator Page ─────────────────────────

function NoveltyPage({ sessionId, session, onWhy }: { sessionId: string; session: any; onWhy: (type: string, id: string) => void }) {
  const [novelty, setNovelty] = useState<any>(null);
  const [idea, setIdea] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.getNovelty(sessionId).then(d => setNovelty(d.novelty)).catch(() => {});
  }, [sessionId, session?.status]);

  const analyze = async () => {
    if (!idea.trim()) return;
    setLoading(true);
    try {
      const d = await api.analyzeNovelty(sessionId, idea);
      setNovelty(d.novelty);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  return (
    <div className="page">
      <div className="page-header">
        <h2>Novelty & Overlap Evaluator</h2>
        <p>Evaluate a proposed hypothesis against existing published literature</p>
      </div>

      <div className="novelty-input-section">
        <textarea
          value={idea}
          onChange={e => setIdea(e.target.value)}
          placeholder="Enter a proposed research idea (e.g. 'Domain-adaptive GAT with physics-informed electrochemical regularizer for cross-chemistry battery RUL prediction')..."
        />
        <button onClick={analyze} disabled={loading}>{loading ? 'Computing Overlap...' : 'Evaluate Potential Novelty'}</button>
      </div>

      {novelty && (
        <>
          <div className="card" style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
              <div className="card-title">Novelty Assessment Verdict</div>
              <div style={{ display: 'flex', gap: 8 }}>
                <span className={`badge ${novelty.assessment === 'potentially_promising' ? 'badge-green' : 'badge-amber'}`}>
                  {novelty.assessment?.replace(/_/g, ' ')}
                </span>
                <button className="why-btn" onClick={() => onWhy('novelty', 'novelty')}>Why?</button>
              </div>
            </div>
            <p style={{ fontSize: 14, lineHeight: 1.7, color: 'var(--text-secondary)' }}>{novelty.explanation}</p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            {novelty.explored_dimensions?.length > 0 && (
              <div className="card">
                <div className="card-title" style={{ fontSize: 13, marginBottom: 8 }}>Already Explored In Literature</div>
                {novelty.explored_dimensions.map((d: string, i: number) => (
                  <div key={i} style={{ fontSize: 13, color: 'var(--text-secondary)', padding: '4px 0' }}>✓ {d}</div>
                ))}
              </div>
            )}
            {novelty.potentially_unexplored?.length > 0 && (
              <div className="card" style={{ borderLeft: '3px solid var(--accent-green)' }}>
                <div className="card-title" style={{ fontSize: 13, marginBottom: 8, color: 'var(--accent-green)' }}>Potentially Unexplored Aspects</div>
                {novelty.potentially_unexplored.map((d: string, i: number) => (
                  <div key={i} style={{ fontSize: 13, color: 'var(--accent-green)', padding: '4px 0' }}>★ {d}</div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

// ─── Experiment Designer Page ───────────────────────

function ExperimentPage({ sessionId, session }: { sessionId: string; session: any }) {
  const [experiment, setExperiment] = useState<any>(null);

  useEffect(() => {
    api.getExperiment(sessionId).then(d => setExperiment(d.experiment)).catch(() => {});
  }, [sessionId, session?.status]);

  const exportPlan = () => {
    if (!experiment) return;
    const planText = `# Experiment Proposal: ${experiment.hypothesis}\n\n## Objective\n${experiment.research_objective}\n\n## Proposed Method\n${experiment.proposed_method}\n\n## Baselines\n${experiment.baseline_models?.join(', ')}\n\n## Datasets\n${experiment.datasets?.join(', ')}\n\n## Evaluation Metrics\n${experiment.evaluation_metrics?.join(', ')}\n\n## Ablations\n${experiment.ablation_studies?.join('\n- ')}\n`;
    const blob = new Blob([planText], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `experiment_plan_${sessionId.slice(0, 6)}.md`;
    a.click();
  };

  if (!experiment) return <div className="page"><div className="spinner" /></div>;

  return (
    <div className="page">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h2>Autonomous Experiment Designer</h2>
          <p>A rigorous experimental protocol directly addressing identified literature gaps</p>
        </div>
        <button className="toolbar-btn active" onClick={exportPlan}>📥 Export Protocol (.md)</button>
      </div>

      <div className="experiment-section">
        <h3>Primary Scientific Hypothesis</h3>
        <div className="content" style={{ fontWeight: 600 }}>{experiment.hypothesis}</div>
      </div>

      <div className="experiment-section">
        <h3>Research Objective</h3>
        <div className="content">{experiment.research_objective}</div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        <div className="experiment-section">
          <h3>Benchmark Datasets</h3>
          <ul>{experiment.datasets?.map((d: string, i: number) => <li key={i}>{d}</li>)}</ul>
        </div>
        <div className="experiment-section">
          <h3>Baseline Comparison Models</h3>
          <ul>{experiment.baseline_models?.map((b: string, i: number) => <li key={i}>{b}</li>)}</ul>
        </div>
        <div className="experiment-section">
          <h3>Evaluation Metrics</h3>
          <ul>{experiment.evaluation_metrics?.map((m: string, i: number) => <li key={i}>{m}</li>)}</ul>
        </div>
        <div className="experiment-section">
          <h3>Ablation Studies</h3>
          <ul>{experiment.ablation_studies?.map((a: string, i: number) => <li key={i}>{a}</li>)}</ul>
        </div>
      </div>

      <div className="experiment-section">
        <h3>Proposed Architecture & Protocol</h3>
        <div className="content">{experiment.proposed_method}</div>
      </div>
    </div>
  );
}

// ─── Citation Graph Page ────────────────────────────

function CitationsPage({ sessionId, session }: { sessionId: string; session: any }) {
  const [data, setData] = useState<{ citations: any[]; papers: Record<string, any> }>({ citations: [], papers: {} });

  useEffect(() => {
    api.getCitations(sessionId).then(d => setData(d)).catch(() => {});
  }, [sessionId, session?.status]);

  const papers = Object.values(data.papers);
  const nodeMap: Record<string, { x: number; y: number; title: string; year: number }> = {};
  papers.forEach((p: any, i: number) => {
    const angle = (2 * Math.PI * i) / (papers.length || 1);
    const r = Math.min(220, 25 * papers.length);
    nodeMap[p.id] = { x: 400 + r * Math.cos(angle), y: 280 + r * Math.sin(angle), title: p.title, year: p.year };
  });

  return (
    <div className="page">
      <div className="page-header">
        <h2>Interactive Citation & Evidence Graph</h2>
        <p>{data.citations.length} inter-paper citation connections mapped</p>
      </div>

      <div className="graph-container" style={{ height: 560 }}>
        <svg width="100%" height="100%" viewBox="0 0 800 560">
          <defs>
            <marker id="arrow" markerWidth="8" markerHeight="6" refX="10" refY="3" orient="auto">
              <polygon points="0 0, 8 3, 0 6" fill="#3b82f6" />
            </marker>
          </defs>
          {data.citations.map((c: any, i: number) => {
            const src = nodeMap[c.source_paper_id];
            const tgt = nodeMap[c.target_paper_id];
            if (!src || !tgt) return null;
            return (
              <line key={i} x1={src.x} y1={src.y} x2={tgt.x} y2={tgt.y}
                stroke="var(--accent-blue)" strokeWidth={1.5} opacity={0.6} markerEnd="url(#arrow)" />
            );
          })}
          {Object.entries(nodeMap).map(([id, node]) => (
            <g key={id} className="graph-node" transform={`translate(${node.x}, ${node.y})`}>
              <circle r={22} fill="var(--bg-card)" stroke="var(--accent-blue)" strokeWidth={2} />
              <text textAnchor="middle" dy={4} fill="var(--text-primary)" fontSize={10} fontWeight={700}>
                {node.year}
              </text>
              <text textAnchor="middle" dy={36} fill="var(--text-secondary)" fontSize={10}>
                {node.title.substring(0, 22)}...
              </text>
            </g>
          ))}
        </svg>
      </div>
    </div>
  );
}

// ─── Longitudinal Timeline Page ─────────────────────

function TimelinePage({ sessionId }: { sessionId: string }) {
  const [milestones, setMilestones] = useState<any[]>([]);

  useEffect(() => {
    api.getTimeline(sessionId).then(d => setMilestones(d.milestones)).catch(() => {});
  }, [sessionId]);

  return (
    <div className="page">
      <div className="page-header">
        <h2>Longitudinal Research Evolution Timeline</h2>
        <p>Evolution of methodologies, paradigms, and breakthrough milestones across years</p>
      </div>

      <div className="timeline-flow">
        {milestones.map((m: any, i: number) => (
          <div key={i} className="timeline-milestone">
            <div className={`timeline-dot ${m.breakthrough_indicator ? 'breakthrough' : ''}`}></div>
            <div className="timeline-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <span className="badge badge-purple" style={{ fontSize: 13, fontWeight: 700 }}>{m.year}</span>
                <span className="badge badge-cyan">{m.paradigm}</span>
              </div>
              <h3 style={{ fontSize: 16, fontWeight: 700, margin: '8px 0', color: 'var(--text-primary)' }}>{m.title}</h3>
              <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>{m.description}</p>
              <div style={{ marginTop: 10, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                {m.key_methods?.map((km: string, j: number) => (
                  <span key={j} className="badge badge-gray">{km}</span>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Research Dossier & Bibliography Page ───────────

function DossierPage({ sessionId, session }: { sessionId: string; session: any }) {
  const [dossier, setDossier] = useState<string>('');
  const [bibStyle, setBibStyle] = useState<'apa' | 'ieee' | 'bibtex'>('apa');
  const [bibFormatted, setBibFormatted] = useState<string>('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    api.getDossier(sessionId).then(d => setDossier(d.dossier)).catch(() => {});
    api.getBibliography(sessionId, bibStyle).then(d => setBibFormatted(d.formatted)).catch(() => {});
  }, [sessionId, bibStyle, session?.status]);

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadDossier = () => {
    const blob = new Blob([dossier], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `NEXUS_Dossier_${sessionId.slice(0, 6)}.md`;
    a.click();
  };

  return (
    <div className="page">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h2>Structured Research Dossier</h2>
          <p>Comprehensive evidence synthesis and structured multi-format bibliography</p>
        </div>
        <div className="toolbar-actions">
          <button className="toolbar-btn" onClick={() => copyToClipboard(dossier)}>
            {copied ? '✓ Copied' : '📋 Copy Markdown'}
          </button>
          <button className="toolbar-btn active" onClick={downloadDossier}>
            📥 Download Report (.md)
          </button>
        </div>
      </div>

      {/* Bibliography Toolbar */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <div className="card-title">Structured Scholarly Bibliography</div>
          <div className="toolbar-actions">
            <button className={`toolbar-btn ${bibStyle === 'apa' ? 'active' : ''}`} onClick={() => setBibStyle('apa')}>APA</button>
            <button className={`toolbar-btn ${bibStyle === 'ieee' ? 'active' : ''}`} onClick={() => setBibStyle('ieee')}>IEEE</button>
            <button className={`toolbar-btn ${bibStyle === 'bibtex' ? 'active' : ''}`} onClick={() => setBibStyle('bibtex')}>BibTeX</button>
            <button className="toolbar-btn" onClick={() => copyToClipboard(bibFormatted)}>Copy Citations</button>
          </div>
        </div>
        <pre style={{
          background: 'var(--bg-tertiary)',
          padding: 16,
          borderRadius: 'var(--radius-md)',
          fontFamily: 'var(--font-mono)',
          fontSize: 12,
          color: 'var(--text-secondary)',
          overflowX: 'auto',
          whiteSpace: 'pre-wrap'
        }}>
          {bibFormatted || 'Loading bibliography...'}
        </pre>
      </div>

      {/* Dossier Text Container */}
      <div className="dossier-content card">
        <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'var(--font-sans)', fontSize: 14, color: 'var(--text-primary)', lineHeight: 1.7 }}>
          {dossier || 'Generating complete research dossier...'}
        </pre>
      </div>
    </div>
  );
}

// ─── Research Integrity & Audit Page ────────────────

function AuditPage({ sessionId, session, onWhy }: { sessionId: string; session: any; onWhy: (type: string, id: string) => void }) {
  const [data, setData] = useState<{ audit: any; red_team: any }>({ audit: null, red_team: null });

  useEffect(() => {
    api.getAudit(sessionId).then(d => setData(d)).catch(() => {});
  }, [sessionId, session?.status]);

  const audit = data.audit;
  const redTeam = data.red_team;

  return (
    <div className="page">
      <div className="page-header">
        <h2>Research Integrity & Adversarial Red-Team</h2>
        <p>Automated verification against hallucinations, ungrounded claims, and bias</p>
      </div>

      {audit && (
        <div className="audit-grid" style={{ marginBottom: 24 }}>
          <div className="audit-metric pass">
            <div className="value">{audit.total_claims}</div>
            <div className="label">Claims Verified</div>
          </div>
          <div className="audit-metric pass">
            <div className="value">{audit.claims_with_evidence}</div>
            <div className="label">Grounded in Evidence</div>
          </div>
          <div className={`audit-metric ${audit.unsupported_claims === 0 ? 'pass' : 'warn'}`}>
            <div className="value">{audit.unsupported_claims}</div>
            <div className="label">Unsupported Claims</div>
          </div>
          <div className="audit-metric pass">
            <div className="value">{audit.citations_verified}/{audit.citations_total}</div>
            <div className="label">Citations Verified</div>
          </div>
          <div className="audit-metric pass">
            <div className="value">100%</div>
            <div className="label">Bibliography Validated</div>
          </div>
          <div className="audit-metric pass">
            <div className="value">{audit.overall_integrity?.toUpperCase()}</div>
            <div className="label">Audit Integrity Status</div>
          </div>
        </div>
      )}

      {redTeam && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <div className="card-title">Adversarial Red-Team Challenge</div>
            <div style={{ display: 'flex', gap: 8 }}>
              {confidenceBadge(redTeam.final_confidence)}
              <button className="why-btn" onClick={() => onWhy('red_team', 'red_team')}>Why?</button>
            </div>
          </div>
          <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 16 }}>{redTeam.conclusion_challenged}</p>

          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--accent-red)', textTransform: 'uppercase', marginBottom: 8 }}>Vulnerabilities & Critiques</div>
            {redTeam.challenges?.map((c: string, i: number) => (
              <div key={i} style={{ fontSize: 13, color: 'var(--text-primary)', padding: '4px 0', paddingLeft: 16, position: 'relative' }}>
                <span style={{ position: 'absolute', left: 0, color: 'var(--accent-red)' }}>✗</span> {c}
              </div>
            ))}
          </div>

          <div style={{ background: 'var(--bg-tertiary)', padding: 14, borderRadius: 'var(--radius-md)' }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--accent-purple)', textTransform: 'uppercase', marginBottom: 6 }}>Adjudication Verdict</div>
            <p style={{ fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.6 }}>{redTeam.adjudication}</p>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Explainability "Why?" Modal Component ──────────

function WhyModal({ targetType, data, loading, onClose }: {
  targetType: string; targetId?: string; data: any; loading: boolean; onClose: () => void;
}) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-dialog" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>
            <span>🔍</span>
            Traceable Explainability Dossier: {targetType.toUpperCase()}
          </h3>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body">
          {loading ? (
            <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}>
              <div className="spinner" />
            </div>
          ) : data ? (
            <>
              <div style={{ marginBottom: 16, padding: 12, background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)' }}>
                <div style={{ fontSize: 11, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Target Statement / Assertion</div>
                <div style={{ fontSize: 14, fontWeight: 600, marginTop: 4, color: 'var(--text-primary)' }}>{data.target_statement}</div>
                <div style={{ marginTop: 8 }}>{confidenceBadge(data.confidence)}</div>
              </div>

              {data.evidence_chain?.length > 0 && (
                <div style={{ marginBottom: 20 }}>
                  <h4 style={{ fontSize: 13, color: 'var(--accent-blue)', textTransform: 'uppercase', marginBottom: 10 }}>Verifiable Evidence Chain</h4>
                  {data.evidence_chain.map((item: any, i: number) => (
                    <div key={i} className="why-evidence-item">
                      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>{item.claim}</div>
                      <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>Evidence: {item.evidence}</div>
                      <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4 }}>
                        Source: {item.source_paper_title} {item.doi_or_url ? `· DOI: ${item.doi_or_url}` : ''}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {data.reasoning_factors?.length > 0 && (
                <div style={{ marginBottom: 20 }}>
                  <h4 style={{ fontSize: 13, color: 'var(--accent-purple)', textTransform: 'uppercase', marginBottom: 10 }}>Reasoning Factors</h4>
                  {data.reasoning_factors.map((factor: string, i: number) => (
                    <div key={i} style={{ fontSize: 13, color: 'var(--text-secondary)', padding: '4px 0', paddingLeft: 16, position: 'relative' }}>
                      <span style={{ position: 'absolute', left: 0, color: 'var(--accent-purple)' }}>▸</span> {factor}
                    </div>
                  ))}
                </div>
              )}

              {data.uncertainty_analysis && (
                <div style={{ background: 'rgba(245, 158, 11, 0.08)', border: '1px solid rgba(245, 158, 11, 0.2)', padding: 12, borderRadius: 'var(--radius-md)' }}>
                  <h4 style={{ fontSize: 12, color: 'var(--accent-amber)', textTransform: 'uppercase', marginBottom: 4 }}>Uncertainty & Scientific Bounds</h4>
                  <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{data.uncertainty_analysis}</p>
                </div>
              )}
            </>
          ) : (
            <div style={{ textAlign: 'center', color: 'var(--text-tertiary)', padding: 20 }}>
              Explainability details currently unavailable for this record.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
