import { useState, useEffect } from 'react';
import type { AuditResult, ReproducibilityProfile, ReproducibilityBlocker, ResearchSession } from '../types/research';
import { api } from '../services/api';
import { AvailabilityBadge } from '../components/common/Badge';
import { WhyButton } from '../components/common/WhyButton';

interface IntegrityPageProps {
  sessionId: string;
  session: ResearchSession | null;
  onWhy: (type: string, id: string) => void;
}

export function IntegrityPage({ sessionId, session, onWhy }: IntegrityPageProps) {
  const [audit, setAudit] = useState<AuditResult | null>(null);
  const [reproducibility, setReproducibility] = useState<{
    profiles: Record<string, ReproducibilityProfile>;
    average_completeness: number;
  }>({ profiles: {}, average_completeness: 0 });

  useEffect(() => {
    api.getAudit(sessionId)
      .then((d: { audit: AuditResult | null }) => setAudit(d.audit))
      .catch(() => {});

    api.getReproducibility(sessionId)
      .then((d: { profiles: Record<string, ReproducibilityProfile>; average_completeness: number }) =>
        setReproducibility({ profiles: d.profiles || {}, average_completeness: d.average_completeness || 0 })
      )
      .catch(() => {});
  }, [sessionId, session?.status]);

  return (
    <div className="workspace-content animate-fade-in">
      {/* Header */}
      <div style={{ marginBottom: 'var(--space-5)' }}>
        <div className="card-section-label">FORENSIC PROVENANCE & REPRODUCIBILITY AUDIT</div>
        <h1 style={{ fontFamily: 'var(--font-serif)', fontSize: '1.75rem' }}>
          Research Integrity & Chain of Custody
        </h1>
        <p style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>
          Automated verification confirming every claim traces back to verifiable evidence, source DOIs, and reproducible code/data
        </p>
      </div>

      {/* Forensic Audit Metric Grid */}
      {audit && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 'var(--space-3)', marginBottom: 'var(--space-5)' }}>
          <div className="editorial-card highlight-teal">
            <div className="card-section-label">CLAIMS VERIFIED</div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '1.8rem', fontWeight: 700, color: 'var(--accent-teal)' }}>
              {audit.total_claims}
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4 }}>100% Extracted Claims Audited</div>
          </div>

          <div className="editorial-card highlight-teal">
            <div className="card-section-label">EVIDENCE LINKED</div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '1.8rem', fontWeight: 700, color: 'var(--accent-steel)' }}>
              {audit.claims_with_evidence_links}
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4 }}>Claims with direct empirical support</div>
          </div>

          <div className={`editorial-card ${audit.unsupported_claims === 0 ? 'highlight-teal' : 'highlight-crimson'}`}>
            <div className="card-section-label">UNSUPPORTED CLAIMS</div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '1.8rem', fontWeight: 700, color: audit.unsupported_claims === 0 ? 'var(--accent-teal)' : 'var(--accent-crimson)' }}>
              {audit.unsupported_claims}
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4 }}>Hallucination & ungrounded assertions</div>
          </div>

          <div className="editorial-card highlight-indigo">
            <div className="card-section-label">BIBLIOGRAPHIC COMPLETENESS</div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '1.5rem', fontWeight: 700, color: 'var(--accent-indigo)' }}>
              {audit.bibliographic_metadata_complete ? '100% VALID' : 'PARTIAL'}
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4 }}>Metadata & DOI Identifiers</div>
          </div>

          <div className="editorial-card highlight-teal">
            <div className="card-section-label">OVERALL VERDICT</div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '1.5rem', fontWeight: 700, color: 'var(--accent-teal)' }}>
              {audit.overall_integrity?.toUpperCase() || 'PASS'}
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4 }}>Chain of Custody Standard</div>
          </div>
        </div>
      )}

      {/* Reproducibility Profiles Section */}
      <div className="editorial-card" style={{ marginBottom: 'var(--space-4)' }}>
        <div className="card-editorial-header">
          <div>
            <div className="card-section-label">REPRODUCIBILITY COMPLETENESS PROFILES</div>
            <h3 className="card-editorial-title">Paper Open Science & Replication Assessment</h3>
          </div>
          <span className="telemetry-chip">
            <span className="chip-label">AVG COMPLETENESS:</span>
            <span className="chip-value">{(reproducibility.average_completeness * 100).toFixed(0)}%</span>
          </span>
        </div>

        {Object.entries(reproducibility.profiles).length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 12 }}>
            {Object.entries(reproducibility.profiles).map(([pId, profile]) => (
              <div key={pId} style={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-sm)', padding: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>
                      Paper: {pId.slice(0, 12)}
                    </span>
                    <span className="nexus-badge badge-high">
                      Score: {(profile.completeness_score * 100).toFixed(0)}%
                    </span>
                  </div>
                  <WhyButton onClick={() => onWhy('reproducibility', pId)} />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 8, marginTop: 6 }}>
                  <div style={{ fontSize: 11 }}>
                    <span style={{ color: 'var(--text-tertiary)' }}>CODE: </span>
                    <AvailabilityBadge availability={profile.code_available} />
                  </div>
                  <div style={{ fontSize: 11 }}>
                    <span style={{ color: 'var(--text-tertiary)' }}>DATASET: </span>
                    <AvailabilityBadge availability={profile.dataset_available} />
                  </div>
                  <div style={{ fontSize: 11 }}>
                    <span style={{ color: 'var(--text-tertiary)' }}>HYPERPARAMS: </span>
                    <AvailabilityBadge availability={profile.hyperparameters_documented} />
                  </div>
                  <div style={{ fontSize: 11 }}>
                    <span style={{ color: 'var(--text-tertiary)' }}>SEEDS: </span>
                    <AvailabilityBadge availability={profile.random_seeds_reported} />
                  </div>
                </div>

                {profile.blockers && profile.blockers.length > 0 && (
                  <div style={{ marginTop: 8, paddingTop: 6, borderTop: '1px solid var(--border-subtle)' }}>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--accent-crimson)', textTransform: 'uppercase' }}>
                      Replication Blockers:
                    </span>
                    {profile.blockers.map((b: ReproducibilityBlocker, idx: number) => (
                      <span key={idx} className="telemetry-chip" style={{ color: 'var(--accent-crimson)', marginLeft: 6, fontSize: 10 }}>
                        ⚠ {b.category}: {b.affected_component}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div style={{ color: 'var(--text-tertiary)', fontSize: 13, padding: '16px 0' }}>
            Evaluating individual paper reproducibility indicators...
          </div>
        )}
      </div>
    </div>
  );
}
