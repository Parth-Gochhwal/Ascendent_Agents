import { useState, useEffect } from 'react';
import { Copy, Download, Check } from 'lucide-react';
import type { ResearchSession } from '../types/research';
import { api } from '../services/api';

interface DossierPageProps {
  sessionId: string;
  session: ResearchSession | null;
}

export function DossierPage({ sessionId, session }: DossierPageProps) {
  const [dossier, setDossier] = useState<string>('');
  const [bibStyle, setBibStyle] = useState<'apa' | 'ieee' | 'bibtex'>('apa');
  const [bibFormatted, setBibFormatted] = useState<string>('');
  const [copiedDossier, setCopiedDossier] = useState(false);
  const [copiedBib, setCopiedBib] = useState(false);

  useEffect(() => {
    api.getDossier(sessionId)
      .then((d: { dossier: string; session: ResearchSession }) => setDossier(d.dossier || ''))
      .catch(() => {});

    api.getBibliography(sessionId, bibStyle)
      .then((d: { style: string; formatted: string }) => setBibFormatted(d.formatted || ''))
      .catch(() => {});
  }, [sessionId, bibStyle, session?.status]);

  const copyText = (text: string, isBib: boolean) => {
    navigator.clipboard.writeText(text);
    if (isBib) {
      setCopiedBib(true);
      setTimeout(() => setCopiedBib(false), 2000);
    } else {
      setCopiedDossier(true);
      setTimeout(() => setCopiedDossier(false), 2000);
    }
  };

  const downloadDossierMarkdown = () => {
    const blob = new Blob([dossier], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `NEXUS_Scientific_Dossier_${sessionId.slice(0, 6)}.md`;
    a.click();
  };

  return (
    <div className="workspace-content animate-fade-in">
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--space-5)' }}>
        <div>
          <div className="card-section-label">PUBLICATION-GRADE SYNTHESIS REPORT</div>
          <h1 style={{ fontFamily: 'var(--font-serif)', fontSize: '1.75rem' }}>
            Structured Scientific Research Dossier
          </h1>
          <p style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>
            Complete evidence synthesis, question decomposition, contradiction review, and multi-format bibliography
          </p>
        </div>

        <div className="toolbar-group">
          <button className="action-btn-secondary" onClick={() => copyText(dossier, false)}>
            {copiedDossier ? <Check size={13} color="var(--accent-teal)" /> : <Copy size={13} />}
            <span>{copiedDossier ? 'Copied' : 'Copy Report'}</span>
          </button>
          <button className="action-btn-primary" onClick={downloadDossierMarkdown}>
            <Download size={13} />
            <span>Download Dossier (.md)</span>
          </button>
        </div>
      </div>

      {/* Bibliography Toolbar & Formatter */}
      <div className="editorial-card" style={{ marginBottom: 'var(--space-5)' }}>
        <div className="card-editorial-header">
          <div>
            <div className="card-section-label">CITATION & BIBLIOGRAPHY FORMATTER</div>
            <h3 className="card-editorial-title" style={{ fontSize: '1.1rem' }}>
              Scholarly Bibliography Formatter
            </h3>
          </div>

          <div className="toolbar-group">
            <button
              className={`action-btn-secondary ${bibStyle === 'apa' ? 'action-btn-primary' : ''}`}
              onClick={() => setBibStyle('apa')}
            >
              APA
            </button>
            <button
              className={`action-btn-secondary ${bibStyle === 'ieee' ? 'action-btn-primary' : ''}`}
              onClick={() => setBibStyle('ieee')}
            >
              IEEE
            </button>
            <button
              className={`action-btn-secondary ${bibStyle === 'bibtex' ? 'action-btn-primary' : ''}`}
              onClick={() => setBibStyle('bibtex')}
            >
              BibTeX
            </button>
            <button className="action-btn-secondary" onClick={() => copyText(bibFormatted, true)}>
              {copiedBib ? <Check size={13} color="var(--accent-teal)" /> : <Copy size={13} />}
              <span>{copiedBib ? 'Copied' : 'Copy Citations'}</span>
            </button>
          </div>
        </div>

        <pre
          style={{
            background: 'var(--bg-tertiary)',
            padding: 14,
            borderRadius: 'var(--radius-sm)',
            fontFamily: 'var(--font-mono)',
            fontSize: 12,
            color: 'var(--text-secondary)',
            overflowX: 'auto',
            whiteSpace: 'pre-wrap',
            marginTop: 8,
            lineHeight: 1.6,
          }}
        >
          {bibFormatted || 'Loading bibliography...'}
        </pre>
      </div>

      {/* Dossier Publication View */}
      <div className="dossier-article-view">
        <pre
          style={{
            whiteSpace: 'pre-wrap',
            fontFamily: 'var(--font-serif)',
            fontSize: 14,
            color: 'var(--text-primary)',
            lineHeight: 1.8,
          }}
        >
          {dossier || 'Synthesizing comprehensive research dossier...'}
        </pre>
      </div>
    </div>
  );
}
