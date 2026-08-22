import { useState, useEffect, useCallback, useRef } from 'react';
import './index.css';
import type { PageId, ResearchSession, AgentEvent, WhyExplanation } from './types/research';
import { api, connectWebSocket } from './services/api';

// Shell & Common Components
import { TopBar } from './components/shell/TopBar';
import { Sidebar } from './components/shell/Sidebar';
import { Observatory } from './components/shell/Observatory';
import { WhyInspector } from './components/common/WhyInspector';
import { LoadingRadar } from './components/common/LoadingRadar';

// Pages
import { HomePage } from './pages/HomePage';
import { OverviewPage } from './pages/OverviewPage';
import { LiteraturePage } from './pages/LiteraturePage';
import { EvidencePage } from './pages/EvidencePage';
import { MethodsPage } from './pages/MethodsPage';
import { ContradictionsPage } from './pages/ContradictionsPage';
import { ConsensusPage } from './pages/ConsensusPage';
import { GapsPage } from './pages/GapsPage';
import { NoveltyPage } from './pages/NoveltyPage';
import { ExperimentPage } from './pages/ExperimentPage';
import { RedTeamPage } from './pages/RedTeamPage';
import { IntegrityPage } from './pages/IntegrityPage';
import { GraphPage } from './pages/GraphPage';
import { TimelinePage } from './pages/TimelinePage';
import { DossierPage } from './pages/DossierPage';

export default function App() {
  const [page, setPage] = useState<PageId>('home');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [session, setSession] = useState<ResearchSession | null>(null);
  const [sessionsList, setSessionsList] = useState<any[]>([]);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState('');
  const [isObservatoryOpen, setIsObservatoryOpen] = useState(true);

  // Explainability "Why?" Inspector State
  const [whyModal, setWhyModal] = useState<{ targetType: string; targetId: string } | null>(null);
  const [whyData, setWhyData] = useState<WhyExplanation | null>(null);
  const [whyLoading, setWhyLoading] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);

  // Load session history
  const loadSessionsList = useCallback(async () => {
    try {
      const data = await api.listSessions();
      setSessionsList(data.sessions || []);
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    loadSessionsList();
  }, [loadSessionsList]);

  // Polling active session details
  useEffect(() => {
    if (!sessionId) return;
    const fetchSession = async () => {
      try {
        const data = await api.getSession(sessionId);
        setSession(data);
        const evData = await api.getEvents(sessionId);
        setEvents(evData.events || []);
      } catch {
        // ignore
      }
    };

    fetchSession();
    const interval = setInterval(fetchSession, 2500);
    return () => clearInterval(interval);
  }, [sessionId]);

  // WebSocket for live event streaming
  useEffect(() => {
    if (!sessionId) return;
    const ws = connectWebSocket(sessionId, (event) => {
      setEvents((prev) => [...prev, event]);
    });
    wsRef.current = ws;
    return () => {
      ws.close();
    };
  }, [sessionId]);

  // Start new research inquiry
  const startResearch = useCallback(
    async (q: string) => {
      if (!q.trim()) return;
      setLoading(true);
      try {
        const res = await api.startResearch(q.trim());
        setSessionId(res.id);
        setPage('overview');
        setEvents([]);
        loadSessionsList();
      } catch (e: any) {
        alert('Failed to start research investigation: ' + e.message);
      }
      setLoading(false);
    },
    [loadSessionsList]
  );

  // Toggle demo/live execution mode
  const toggleDemo = useCallback(async () => {
    try {
      await api.toggleDemoMode();
      if (sessionId) {
        const s = await api.getSession(sessionId);
        setSession(s);
      }
      loadSessionsList();
    } catch (e: any) {
      alert('Mode toggle error: ' + e.message);
    }
  }, [sessionId, loadSessionsList]);

  // Trigger Explainability "Why?" Modal
  const openWhy = useCallback(
    async (targetType: string, targetId: string) => {
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
    },
    [sessionId]
  );

  const closeWhy = () => {
    setWhyModal(null);
    setWhyData(null);
  };

  // If on home landing view with no active session
  if (page === 'home' && !sessionId) {
    return (
      <HomePage
        query={query}
        setQuery={setQuery}
        onStart={startResearch}
        loading={loading}
        sessionsList={sessionsList}
        onResume={(id) => {
          setSessionId(id);
          setPage('overview');
        }}
      />
    );
  }

  // Check if session is currently executing initial planning
  const isInitializing =
    loading ||
    (session &&
      (session.status === 'planning' || session.status === 'discovering') &&
      (!session.papers || Object.keys(session.papers).length === 0));

  return (
    <div className="workstation-shell">
      {/* Background coordinate grid */}
      <div className="scientific-grid-bg" />

      {/* Top Telemetry Header */}
      <TopBar
        session={session}
        sessionsList={sessionsList}
        onSelectSession={(id) => {
          setSessionId(id);
          setPage('overview');
        }}
        onNewInquiry={() => {
          setSessionId(null);
          setPage('home');
        }}
        onToggleDemoMode={toggleDemo}
        onToggleObservatory={() => setIsObservatoryOpen(!isObservatoryOpen)}
        isObservatoryOpen={isObservatoryOpen}
        onNavigateHome={() => {
          setSessionId(null);
          setPage('home');
        }}
      />

      {/* Workstation Body Grid */}
      <div className="shell-body">
        {/* Left Research Narrative Spine Sidebar */}
        <Sidebar
          activePage={page}
          onNavigate={(p) => setPage(p)}
          session={session}
        />

        {/* Center Analytical Workspace */}
        <main className="shell-workspace">
          {isInitializing ? (
            <LoadingRadar question={session?.question || query} events={events} />
          ) : (
            <>
              {page === 'home' && (
                <OverviewPage session={session} onNavigate={setPage} onWhy={openWhy} />
              )}
              {page === 'overview' && (
                <OverviewPage session={session} onNavigate={setPage} onWhy={openWhy} />
              )}
              {page === 'literature' && (
                <LiteraturePage sessionId={sessionId!} session={session} onWhy={openWhy} />
              )}
              {page === 'evidence' && (
                <EvidencePage sessionId={sessionId!} session={session} onWhy={openWhy} />
              )}
              {page === 'methods' && (
                <MethodsPage sessionId={sessionId!} session={session} onWhy={openWhy} />
              )}
              {page === 'contradictions' && (
                <ContradictionsPage sessionId={sessionId!} session={session} onWhy={openWhy} />
              )}
              {page === 'consensus' && (
                <ConsensusPage sessionId={sessionId!} session={session} onWhy={openWhy} />
              )}
              {page === 'gaps' && (
                <GapsPage sessionId={sessionId!} session={session} onWhy={openWhy} />
              )}
              {page === 'novelty' && (
                <NoveltyPage sessionId={sessionId!} session={session} onWhy={openWhy} />
              )}
              {page === 'experiment' && (
                <ExperimentPage sessionId={sessionId!} session={session} />
              )}
              {page === 'redteam' && (
                <RedTeamPage sessionId={sessionId!} session={session} onWhy={openWhy} />
              )}
              {page === 'integrity' && (
                <IntegrityPage sessionId={sessionId!} session={session} onWhy={openWhy} />
              )}
              {page === 'graph' && (
                <GraphPage sessionId={sessionId!} session={session} />
              )}
              {page === 'timeline' && (
                <TimelinePage sessionId={sessionId!} />
              )}
              {page === 'dossier' && (
                <DossierPage sessionId={sessionId!} session={session} />
              )}
            </>
          )}
        </main>

        {/* Right Observation Console */}
        <Observatory
          isOpen={isObservatoryOpen}
          onClose={() => setIsObservatoryOpen(false)}
          events={events}
          onClearEvents={() => setEvents([])}
          status={session?.status}
        />
      </div>

      {/* Omnipresent "Why?" Provenance Chain Inspector Drawer */}
      {whyModal && (
        <WhyInspector
          isOpen={Boolean(whyModal)}
          onClose={closeWhy}
          targetType={whyModal.targetType}
          targetId={whyModal.targetId}
          data={whyData}
          loading={whyLoading}
        />
      )}
    </div>
  );
}
