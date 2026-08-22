import { useState, useEffect, useRef } from 'react';
import { BookOpen, Search, Upload, CheckCircle2, AlertTriangle, ArrowLeft } from 'lucide-react';
import type { Paper, PaperAnalysis, ResearchSession, Claim } from '../types/research';
import { api } from '../services/api';
import { AvailabilityBadge } from '../components/common/Badge';
import { WhyButton } from '../components/common/WhyButton';
import { EmptyState } from '../components/common/EmptyState';

interface LiteraturePageProps {
  sessionId: string;
  session: ResearchSession | null;
  onWhy: (type: string, id: string) => void;
}

export function LiteraturePage({ sessionId, session, onWhy }: LiteraturePageProps) {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [selectedPaper, setSelectedPaper] = useState<Paper | null>(null);
  const [analysis, setAnalysis] = useState<PaperAnalysis | null>(null);
  const [searchFilter, setSearchFilter] = useState('');
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api.getPapers(sessionId)
      .then((d: { papers: Paper[] }) => setPapers(d.papers || []))
      .catch(() => {});
  }, [sessionId, session?.status]);

  const viewPaper = async (paperId: string) => {
    try {
      const d = await api.getPaperDetail(sessionId, paperId);
      setSelectedPaper(d.paper);
      setAnalysis(d.analysis);
    } catch (e) {
      console.error(e);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const res = await api.uploadPdf(sessionId, file);
      alert(`Paper Ingested: ${res.paper.title}`);
      const d = await api.getPapers(sessionId);
      setPapers(d.papers || []);
    } catch (err: any) {
      alert(`PDF Ingestion Error: ${err.message}`);
    }
    setUploading(false);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const filtered = papers.filter(
    (p) =>
      p.title?.toLowerCase().includes(searchFilter.toLowerCase()) ||
      p.abstract?.toLowerCase().includes(searchFilter.toLowerCase()) ||
      p.authors?.some((a) => a.name?.toLowerCase().includes(searchFilter.toLowerCase())) ||
      p.venue?.toLowerCase().includes(searchFilter.toLowerCase())
  );

  if (selectedPaper) {
    return (
      <div className="workspace-content animate-fade-in">
        {/* Header Back & Action */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-5)' }}>
          <button className="action-btn-secondary" onClick={() => { setSelectedPaper(null); setAnalysis(null); }}>
            <ArrowLeft size={13} />
            <span>Back to Literature Archive</span>
          </button>
          {selectedPaper.research_score != null && (
            <WhyButton label="Explain Relevance Score" onClick={() => onWhy('paper', selectedPaper.id)} />
          )}
        </div>

        {/* Paper Primary Header Card */}
        <div className="editorial-card highlight-steel" style={{ marginBottom: 'var(--space-4)' }}>
          <div className="card-section-label">PEER REVIEWED PUBLICATION RECORD</div>
          <h2 style={{ fontFamily: 'var(--font-serif)', fontSize: '1.5rem', margin: '8px 0 12px', color: 'var(--text-primary)' }}>
            {selectedPaper.title}
          </h2>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16, fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16 }}>
            <span><strong>Authors:</strong> {selectedPaper.authors?.map((a) => a.name).join(', ') || 'N/A'}</span>
            <span><strong>Year:</strong> {selectedPaper.year || 'N/A'}</span>
            <span><strong>Venue:</strong> {selectedPaper.venue || 'N/A'}</span>
            {selectedPaper.doi && (
              <span className="doi-chip">DOI:{selectedPaper.doi}</span>
            )}
            {selectedPaper.citation_count != null && (
              <span><strong>Citations:</strong> {selectedPaper.citation_count}</span>
            )}
          </div>

          {selectedPaper.abstract && (
            <div style={{ background: 'var(--bg-tertiary)', padding: 'var(--space-4)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-primary)' }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)', textTransform: 'uppercase', marginBottom: 4 }}>
                SCHOLARLY ABSTRACT
              </div>
              <p style={{ fontSize: 13, lineHeight: 1.65, color: 'var(--text-primary)' }}>
                {selectedPaper.abstract}
              </p>
            </div>
          )}
        </div>

        {/* Reproducibility & Open Science Indicators */}
        <div className="editorial-card" style={{ marginBottom: 'var(--space-4)' }}>
          <div className="card-section-label">REPRODUCIBILITY & OPEN SCIENCE ARTIFACTS</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12, marginTop: 10 }}>
            <div style={{ background: 'var(--bg-tertiary)', padding: 10, borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-primary)' }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)' }}>SOURCE CODE AVAILABILITY</div>
              <div style={{ marginTop: 6 }}><AvailabilityBadge availability={analysis?.code_availability || 'unclear'} /></div>
            </div>
            <div style={{ background: 'var(--bg-tertiary)', padding: 10, borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-primary)' }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)' }}>DATASET AVAILABILITY</div>
              <div style={{ marginTop: 6 }}><AvailabilityBadge availability={analysis?.dataset_availability || 'available'} /></div>
            </div>
            <div style={{ background: 'var(--bg-tertiary)', padding: 10, borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-primary)' }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)' }}>OPEN ACCESS STATUS</div>
              <div style={{ marginTop: 6 }}>
                <span className={`nexus-badge ${selectedPaper.open_access ? 'badge-high' : 'badge-neutral'}`}>
                  {selectedPaper.open_access ? 'OPEN ACCESS' : 'METADATA RECORD'}
                </span>
              </div>
            </div>
            <div style={{ background: 'var(--bg-tertiary)', padding: 10, borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-primary)' }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)' }}>ANALYSIS DEPTH</div>
              <div style={{ marginTop: 6 }}>
                <span className={`nexus-badge ${selectedPaper.full_text_available ? 'badge-high' : selectedPaper.content_status === 'FULL_TEXT_FAILED' ? 'badge-low' : 'badge-medium'}`}>
                  {selectedPaper.full_text_available
                    ? `FULL TEXT (${selectedPaper.page_count || 'N/A'} pp)`
                    : selectedPaper.content_status === 'FULL_TEXT_FAILED'
                    ? 'ABSTRACT (PDF fetch failed)'
                    : 'ABSTRACT ONLY'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Extracted Findings & Claims */}
        {analysis && (
          <>
            {analysis.main_findings && analysis.main_findings.length > 0 && (
              <div className="editorial-card highlight-teal" style={{ marginBottom: 'var(--space-4)' }}>
                <div className="card-section-label">EMPIRICAL FINDINGS EXTRACTED</div>
                <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {analysis.main_findings.map((f: string, i: number) => (
                    <div key={i} style={{ fontSize: 13, color: 'var(--text-primary)', display: 'flex', gap: 8 }}>
                      <CheckCircle2 size={14} color="var(--accent-teal)" style={{ flexShrink: 0, marginTop: 3 }} />
                      <span>{f}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {analysis.limitations && analysis.limitations.length > 0 && (
              <div className="editorial-card highlight-copper" style={{ marginBottom: 'var(--space-4)' }}>
                <div className="card-section-label">REPORTED METHODOLOGICAL LIMITATIONS</div>
                <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {analysis.limitations.map((lim: string, i: number) => (
                    <div key={i} style={{ fontSize: 13, color: 'var(--accent-copper)', display: 'flex', gap: 8 }}>
                      <AlertTriangle size={14} color="var(--accent-copper)" style={{ flexShrink: 0, marginTop: 3 }} />
                      <span>{lim}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {analysis.claims && analysis.claims.length > 0 && (
              <div className="editorial-card">
                <div className="card-section-label">ATOMIC CLAIMS & METRICS</div>
                <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {analysis.claims.map((c: Claim, i: number) => (
                    <div key={i} style={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-sm)', padding: 10 }}>
                      <div style={{ fontSize: 13, color: 'var(--text-primary)', marginBottom: 6 }}>{c.statement}</div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, alignItems: 'center' }}>
                        {c.metric && <span className="nexus-badge badge-blue">{c.metric}: {c.evidence_value}</span>}
                        {c.conditions?.map((cond: string, j: number) => (
                          <span key={j} className="telemetry-chip">{cond}</span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    );
  }

  return (
    <div className="workspace-content animate-fade-in">
      {/* Page Title & Top Toolbar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--space-5)' }}>
        <div>
          <div className="card-section-label">SCHOLARLY LITERATURE REPOSITORY</div>
          <h1 style={{ fontFamily: 'var(--font-serif)', fontSize: '1.75rem' }}>
            Academic Literature Discovery
          </h1>
          <p style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>
            {papers.length} peer-reviewed scientific papers retrieved, normalized, and ranked
          </p>
        </div>

        <div className="toolbar-group">
          <input
            type="file"
            accept=".pdf"
            ref={fileInputRef}
            onChange={handleFileUpload}
            style={{ display: 'none' }}
          />
          <button
            className="action-btn-secondary"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
          >
            <Upload size={13} />
            <span>{uploading ? 'Ingesting PDF...' : 'Ingest PDF Paper'}</span>
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <div style={{ marginBottom: 'var(--space-4)', display: 'flex', gap: 8 }}>
        <div style={{ position: 'relative', flex: 1, maxWidth: 420 }}>
          <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-tertiary)' }} />
          <input
            style={{ width: '100%', paddingLeft: 32, paddingRight: 12, height: 34, fontSize: 13 }}
            placeholder="Search papers by title, author, venue, or keyword..."
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
          />
        </div>
      </div>

      {/* Papers Grid */}
      {filtered.length > 0 ? (
        <div className="literature-grid">
          {filtered.map((p) => (
            <div key={p.id} className="paper-record-card" onClick={() => viewPaper(p.id)}>
              <div>
                <h3 className="paper-record-title">{p.title}</h3>
                <div className="paper-record-authors">
                  {p.authors?.map((a) => a.name).join(', ') || 'Scholarly Authors'}
                </div>
                <div className="paper-record-meta">
                  <span>{p.year || 'N/A'}</span>
                  <span>·</span>
                  <span>{p.venue || 'Journal / Conference'}</span>
                  {p.citation_count != null && (
                    <>
                      <span>·</span>
                      <span>🔗 {p.citation_count} cites</span>
                    </>
                  )}
                </div>

                {p.abstract && (
                  <p style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5, display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                    {p.abstract}
                  </p>
                )}
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 14, paddingTop: 10, borderTop: '1px solid var(--border-subtle)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  {p.research_score != null ? (
                    <span className="telemetry-chip">
                      <span className="chip-label">SCORE:</span>
                      <span className="chip-value">{(p.research_score * 100).toFixed(0)}%</span>
                    </span>
                  ) : (
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-dim)' }}>
                      UNSCORED
                    </span>
                  )}
                  {p.doi && <span className="doi-chip">DOI</span>}
                  {p.full_text_available ? (
                    <span className="nexus-badge badge-high" style={{ fontSize: 9, padding: '2px 6px' }}>FULL TEXT</span>
                  ) : (
                    <span className="nexus-badge badge-neutral" style={{ fontSize: 9, padding: '2px 6px' }}>ABSTRACT</span>
                  )}
                </div>

                <WhyButton onClick={() => onWhy('paper', p.id)} />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState
          icon={<BookOpen size={24} />}
          title="No Scholarly Papers Found"
          description="Try adjusting your filter search term or ingest a new PDF publication."
        />
      )}
    </div>
  );
}
