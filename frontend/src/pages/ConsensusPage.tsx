import { useState, useEffect } from 'react';
import { CheckCircle2, AlertTriangle, HelpCircle, ShieldAlert } from 'lucide-react';
import type { ConsensusFinding, CitationEchoCluster, ResearchSession } from '../types/research';
import { api } from '../services/api';
import { ConfidenceBadge } from '../components/common/Badge';
import { WhyButton } from '../components/common/WhyButton';

interface ConsensusPageProps {
  sessionId: string;
  session: ResearchSession | null;
  onWhy: (type: string, id: string) => void;
}

export function ConsensusPage({ sessionId, session, onWhy }: ConsensusPageProps) {
  const [consensus, setConsensus] = useState<ConsensusFinding[]>([]);
  const [echoes, setEchoes] = useState<CitationEchoCluster[]>([]);

  useEffect(() => {
    api.getConsensus(sessionId)
      .then((d: { consensus: ConsensusFinding[] }) => setConsensus(d.consensus || []))
      .catch(() => {});

    api.getCitationEchoes(sessionId)
      .then((d: { echoes: CitationEchoCluster[] }) => setEchoes(d.echoes || []))
      .catch(() => {});
  }, [sessionId, session?.status]);

  const grouped = {
    established: consensus.filter(
      (c) => c.status === 'supported' || c.status === 'likely_supported' || c.status === 'consensus'
    ),
    contested: consensus.filter(
      (c) => c.status === 'contested' || c.status === 'mixed'
    ),
    unresolved: consensus.filter(
      (c) => c.status === 'uncertain' || c.status === 'unresolved' || c.status === 'insufficient_evidence'
    ),
  };

  return (
    <div className="workspace-content animate-fade-in">
      {/* Header */}
      <div style={{ marginBottom: 'var(--space-5)' }}>
        <div className="card-section-label">SCIENTIFIC CONSENSUS SYNTHESIS</div>
        <h1 style={{ fontFamily: 'var(--font-serif)', fontSize: '1.75rem' }}>
          Consensus Analysis & Citation Echo Detection
        </h1>
        <p style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>
          Discerning genuinely validated collective consensus from illusory agreement caused by citation echo chambers
        </p>
      </div>

      {/* Citation Echo Chamber Alert Banner */}
      {echoes.length > 0 && (
        <div className="echo-chamber-alert">
          <ShieldAlert size={20} color="var(--accent-copper)" style={{ flexShrink: 0, marginTop: 2 }} />
          <div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700, color: 'var(--accent-copper)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
              CITATION ECHO CHAMBER DETECTED ({echoes.length} CLUSTERS)
            </div>
            {echoes.map((echo, i) => (
              <div key={echo.id || i} style={{ marginTop: 6, fontSize: 13, color: 'var(--text-primary)' }}>
                <strong>"{echo.claim_statement}"</strong>
                <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>
                  {echo.total_support_count} citing papers trace back to {echo.independent_support_count} originating primary experiments ({echo.originating_paper_title || echo.originating_paper_id}).
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 3-Column Editorial Grid */}
      <div className="consensus-columns-grid">
        {/* Established Consensus Column */}
        <div className="consensus-column highlight-teal">
          <div className="consensus-column-header">
            <span style={{ color: 'var(--accent-teal)', display: 'flex', alignItems: 'center', gap: 6 }}>
              <CheckCircle2 size={13} />
              <span>ESTABLISHED CONSENSUS ({grouped.established.length})</span>
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {grouped.established.map((c) => (
              <div key={c.id} style={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-sm)', padding: 12 }}>
                <div style={{ fontFamily: 'var(--font-serif)', fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.45, marginBottom: 8 }}>
                  "{c.statement}"
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: 6, borderTop: '1px solid var(--border-subtle)' }}>
                  <span className="telemetry-chip" style={{ fontSize: 10 }}>
                    {c.supporting_paper_ids?.length || 0} supporting papers
                  </span>
                  <WhyButton onClick={() => onWhy('consensus', c.id)} />
                </div>
                {c.explanation && (
                  <p style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 6, lineHeight: 1.4 }}>
                    {c.explanation}
                  </p>
                )}
              </div>
            ))}
            {grouped.established.length === 0 && (
              <div style={{ color: 'var(--text-dim)', fontSize: 12, textAlign: 'center', padding: '20px 0' }}>
                No established consensus items
              </div>
            )}
          </div>
        </div>

        {/* Actively Contested Column */}
        <div className="consensus-column highlight-copper">
          <div className="consensus-column-header">
            <span style={{ color: 'var(--accent-copper)', display: 'flex', alignItems: 'center', gap: 6 }}>
              <AlertTriangle size={13} />
              <span>ACTIVELY CONTESTED ({grouped.contested.length})</span>
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {grouped.contested.map((c) => (
              <div key={c.id} style={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-sm)', padding: 12 }}>
                <div style={{ fontFamily: 'var(--font-serif)', fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.45, marginBottom: 8 }}>
                  "{c.statement}"
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: 6, borderTop: '1px solid var(--border-subtle)' }}>
                  <span className="telemetry-chip" style={{ fontSize: 10, color: 'var(--accent-copper)' }}>
                    {c.supporting_paper_ids?.length || 0} support / {c.dissenting_paper_ids?.length || 0} dissent
                  </span>
                  <WhyButton onClick={() => onWhy('consensus', c.id)} />
                </div>
                {c.explanation && (
                  <p style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 6, lineHeight: 1.4 }}>
                    {c.explanation}
                  </p>
                )}
              </div>
            ))}
            {grouped.contested.length === 0 && (
              <div style={{ color: 'var(--text-dim)', fontSize: 12, textAlign: 'center', padding: '20px 0' }}>
                No contested assertions
              </div>
            )}
          </div>
        </div>

        {/* Unresolved & Uncertain Column */}
        <div className="consensus-column">
          <div className="consensus-column-header">
            <span style={{ color: 'var(--text-tertiary)', display: 'flex', alignItems: 'center', gap: 6 }}>
              <HelpCircle size={13} />
              <span>UNRESOLVED & UNCERTAIN ({grouped.unresolved.length})</span>
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {grouped.unresolved.map((c) => (
              <div key={c.id} style={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-sm)', padding: 12 }}>
                <div style={{ fontFamily: 'var(--font-serif)', fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.45, marginBottom: 8 }}>
                  "{c.statement}"
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: 6, borderTop: '1px solid var(--border-subtle)' }}>
                  <ConfidenceBadge confidence={c.confidence} />
                  <WhyButton onClick={() => onWhy('consensus', c.id)} />
                </div>
              </div>
            ))}
            {grouped.unresolved.length === 0 && (
              <div style={{ color: 'var(--text-dim)', fontSize: 12, textAlign: 'center', padding: '20px 0' }}>
                No unresolved questions
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
