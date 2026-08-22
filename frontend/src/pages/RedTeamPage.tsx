import { useState, useEffect } from 'react';
import { ShieldAlert } from 'lucide-react';
import type { RedTeamResult, RedTeamFinding, ResearchSession } from '../types/research';
import { api } from '../services/api';
import { ConfidenceBadge } from '../components/common/Badge';
import { WhyButton } from '../components/common/WhyButton';
import { EmptyState } from '../components/common/EmptyState';

interface RedTeamPageProps {
  sessionId: string;
  session: ResearchSession | null;
  onWhy: (type: string, id: string) => void;
}

export function RedTeamPage({ sessionId, session, onWhy }: RedTeamPageProps) {
  const [redTeam, setRedTeam] = useState<RedTeamResult | null>(null);

  useEffect(() => {
    api.getAudit(sessionId)
      .then((d: { red_team: RedTeamResult | null }) => setRedTeam(d.red_team))
      .catch(() => {});
  }, [sessionId, session?.status]);

  if (!redTeam) {
    return (
      <div className="workspace-content animate-fade-in">
        <EmptyState
          icon={<ShieldAlert size={24} />}
          title="Executing Adversarial Red-Team Stress Test"
          description="Simulating rigorous peer review to stress-test claims against hidden assumptions, dataset bias, cherry-picking, and evaluation leakage."
        />
      </div>
    );
  }

  return (
    <div className="workspace-content animate-fade-in">
      {/* Header */}
      <div style={{ marginBottom: 'var(--space-5)' }}>
        <div className="card-section-label">ADVERSARIAL STRESS TEST & PEER REVIEW</div>
        <h1 style={{ fontFamily: 'var(--font-serif)', fontSize: '1.75rem' }}>
          Red-Team Review & Adjudication
        </h1>
        <p style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>
          Forensic adversarial attacks testing claims against bias, evaluation leakage, and unsupported inferences
        </p>
      </div>

      {/* Challenged Conclusion Card */}
      <div className="editorial-card highlight-crimson" style={{ marginBottom: 'var(--space-4)' }}>
        <div className="card-editorial-header">
          <div>
            <div className="card-section-label">CENTRAL CONCLUSION UNDER ATTACK</div>
            <h2 style={{ fontFamily: 'var(--font-serif)', fontSize: '1.25rem', color: 'var(--text-primary)', margin: '4px 0 8px' }}>
              "{redTeam.conclusion_challenged}"
            </h2>
          </div>

          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <ConfidenceBadge confidence={redTeam.final_confidence} />
            <WhyButton onClick={() => onWhy('red_team', 'red_team')} />
          </div>
        </div>
      </div>

      {/* Adversarial Vulnerability Challenges */}
      <div className="editorial-card" style={{ marginBottom: 'var(--space-4)' }}>
        <div className="card-section-label">IDENTIFIED CRITIQUES & VULNERABILITIES ({redTeam.challenges?.length || 0})</div>
        <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 8 }}>
          {redTeam.challenges?.map((c: string, i: number) => (
            <div key={i} style={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-sm)', padding: 12, display: 'flex', gap: 10 }}>
              <ShieldAlert size={16} color="var(--accent-crimson)" style={{ flexShrink: 0, marginTop: 2 }} />
              <span style={{ fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.5 }}>
                {c}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Detailed Red Team Findings */}
      {redTeam.findings && redTeam.findings.length > 0 && (
        <div className="editorial-card highlight-copper" style={{ marginBottom: 'var(--space-4)' }}>
          <div className="card-section-label">STRUCTURED AUDIT FINDINGS</div>
          <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 10 }}>
            {redTeam.findings.map((f: RedTeamFinding, i: number) => (
              <div key={f.id || i} style={{ background: 'var(--bg-tertiary)', padding: 12, borderRadius: 'var(--radius-sm)', borderLeft: '3px solid var(--accent-copper)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                  <span className="nexus-badge badge-copper">{f.finding_type.replace(/_/g, ' ').toUpperCase()}</span>
                  <span className="telemetry-chip" style={{ fontSize: 10 }}>SEVERITY: {f.severity.toUpperCase()}</span>
                </div>
                <p style={{ fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.5, marginTop: 4 }}>
                  {f.description}
                </p>
                {f.recommended_correction && (
                  <div style={{ fontSize: 12, color: 'var(--accent-teal)', marginTop: 6 }}>
                    <strong>Recommended Remediation:</strong> {f.recommended_correction}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Final Adjudication Box */}
      {redTeam.adjudication && (
        <div className="editorial-card highlight-teal">
          <div className="card-section-label">ADJUDICATION SYNTHESIS & FINAL VERDICT</div>
          <p style={{ fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.65, marginTop: 6 }}>
            {redTeam.adjudication}
          </p>
        </div>
      )}
    </div>
  );
}
