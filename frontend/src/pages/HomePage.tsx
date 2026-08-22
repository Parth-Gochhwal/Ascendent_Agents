import { useState } from 'react';
import { Compass, ArrowRight, Clock, Activity } from 'lucide-react';

interface HomePageProps {
  query: string;
  setQuery: (q: string) => void;
  onStart: (q: string) => void;
  loading: boolean;
  sessionsList: Array<{ id: string; question: string; title: string; status: string; stats?: any; is_demo?: boolean; created_at?: string }>;
  onResume: (id: string) => void;
}

export function HomePage({
  query,
  setQuery,
  onStart,
  loading,
  sessionsList,
  onResume,
}: HomePageProps) {
  const [localQuery, setLocalQuery] = useState(query);

  const benchmarks = [
    {
      domain: 'CROSS-DOMAIN BATTERY INFORMATICS',
      question: 'Are graph neural networks genuinely better than transformers for battery RUL prediction under cross-domain chemistry conditions?',
    },
    {
      domain: 'MULTIMODAL INTELLIGENCE',
      question: 'What are the empirical limitations and evaluation leakages in multimodal retrieval-augmented generation (RAG) benchmarks?',
    },
    {
      domain: 'DIFFUSION & GENERATIVE MEDICINE',
      question: 'How robust are latent diffusion models for synthetic histopathology image generation under severe clinical distribution shifts?',
    },
  ];

  const handleExecute = () => {
    if (!localQuery.trim() || loading) return;
    setQuery(localQuery);
    onStart(localQuery);
  };

  return (
    <div className="home-page-container">
      {/* Background coordinate markings */}
      <div className="scientific-grid-bg" />

      {/* Hero Header */}
      <div className="home-hero-section">
        <div className="home-institution-tag">
          <Activity size={12} />
          <span>AUTONOMOUS SCIENTIFIC DISCOVERY WORKSTATION</span>
        </div>

        <h1 className="home-title">NEXUS</h1>

        <p className="home-editorial-quote">
          "From what do we know to what should we investigate next?"
        </p>
      </div>

      {/* Primary Investigation Search Input Box */}
      <div className="home-search-box">
        <textarea
          className="home-search-input"
          placeholder="State a research question, hypothesis, or open scientific tension to investigate..."
          value={localQuery}
          onChange={(e) => setLocalQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleExecute();
            }
          }}
          rows={2}
        />

        <div className="home-search-bottom">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-tertiary)' }}>
            <Compass size={13} style={{ color: 'var(--accent-steel)' }} />
            <span>Autonomous Decomposition · Evidence Extraction · Contradiction Discovery</span>
          </div>

          <button
            className="action-btn-primary"
            onClick={handleExecute}
            disabled={loading || !localQuery.trim()}
            style={{ padding: '8px 16px', fontSize: 12 }}
          >
            <span>{loading ? 'INITIALIZING AGENTS...' : 'BEGIN INVESTIGATION'}</span>
            <ArrowRight size={14} />
          </button>
        </div>
      </div>

      {/* Benchmark Research Inquiries */}
      <div className="home-inquiry-examples">
        <div className="home-examples-label">BENCHMARK SCIENTIFIC INVESTIGATIONS</div>
        {benchmarks.map((bm, i) => (
          <div
            key={i}
            className="home-example-card"
            onClick={() => {
              setLocalQuery(bm.question);
              setQuery(bm.question);
              onStart(bm.question);
            }}
          >
            <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--accent-steel)', letterSpacing: '0.08em' }}>
                {bm.domain}
              </span>
              <span className="home-example-text">{bm.question}</span>
            </div>
            <div style={{ color: 'var(--text-tertiary)', flexShrink: 0 }}>
              <ArrowRight size={14} />
            </div>
          </div>
        ))}
      </div>

      {/* Recent Investigations */}
      {sessionsList && sessionsList.length > 0 && (
        <div style={{ width: '100%', maxWidth: 780, marginTop: 'var(--space-6)' }}>
          <div className="home-examples-label" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Clock size={12} />
            <span>RECENT RESEARCH INVESTIGATIONS</span>
          </div>
          <div style={{ display: 'grid', gap: 8 }}>
            {sessionsList.slice(0, 4).map((s) => (
              <div
                key={s.id}
                onClick={() => onResume(s.id)}
                className="editorial-card"
                style={{
                  padding: '12px 16px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  cursor: 'pointer',
                }}
              >
                <div style={{ minWidth: 0, paddingRight: 16 }}>
                  <div style={{ fontFamily: 'var(--font-serif)', fontSize: 14, color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {s.question || s.title}
                  </div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-tertiary)', marginTop: 2 }}>
                    ID: {s.id.slice(0, 8)} · Status: {s.status.toUpperCase()} · Discovered: {s.stats?.papers_discovered || 0} papers
                  </div>
                </div>
                <button className="action-btn-secondary" style={{ flexShrink: 0 }}>
                  <span>Resume</span>
                  <ArrowRight size={12} />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
