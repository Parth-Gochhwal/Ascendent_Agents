import type { EvidenceConfidence, ContradictionType, Availability, ConsensusStatus } from '../../types/research';

export function ConfidenceBadge({ confidence }: { confidence?: EvidenceConfidence | string }) {
  const c = confidence?.toLowerCase() || 'medium';
  let badgeClass = 'badge-neutral';
  if (c === 'high') badgeClass = 'badge-high';
  else if (c === 'medium') badgeClass = 'badge-medium';
  else if (c === 'low' || c === 'insufficient') badgeClass = 'badge-low';

  return (
    <span className={`nexus-badge ${badgeClass}`}>
      <span style={{ fontSize: 9 }}>●</span>
      {confidence?.toUpperCase() || 'UNCERTAIN'}
    </span>
  );
}

export function ContradictionBadge({ type }: { type?: ContradictionType | string }) {
  const t = type || 'unresolved';
  let badgeClass = 'badge-neutral';
  if (t === 'direct_contradiction') badgeClass = 'badge-low';
  else if (t === 'methodological_conflict' || t === 'metric_disagreement') badgeClass = 'badge-copper';
  else if (t === 'contextual_disagreement' || t === 'scope_disagreement') badgeClass = 'badge-indigo';
  else if (t === 'apparent_contradiction') badgeClass = 'badge-medium';
  else if (t === 'agreement') badgeClass = 'badge-high';

  return (
    <span className={`nexus-badge ${badgeClass}`}>
      {t.replace(/_/g, ' ').toUpperCase()}
    </span>
  );
}

export function ConsensusBadge({ status }: { status?: ConsensusStatus | string }) {
  const s = status?.toLowerCase() || 'uncertain';
  let badgeClass = 'badge-neutral';
  if (s === 'supported' || s === 'likely_supported' || s === 'consensus') badgeClass = 'badge-high';
  else if (s === 'contested' || s === 'mixed') badgeClass = 'badge-copper';
  else if (s === 'unresolved' || s === 'insufficient_evidence') badgeClass = 'badge-medium';

  return (
    <span className={`nexus-badge ${badgeClass}`}>
      {status?.replace(/_/g, ' ').toUpperCase() || 'UNCERTAIN'}
    </span>
  );
}

export function AvailabilityBadge({ availability }: { availability?: Availability | string }) {
  const a = availability?.toLowerCase() || 'unknown';
  let badgeClass = 'badge-neutral';
  if (a === 'available') badgeClass = 'badge-high';
  else if (a === 'partial') badgeClass = 'badge-medium';
  else if (a === 'not_found' || a === 'unavailable') badgeClass = 'badge-low';

  return (
    <span className={`nexus-badge ${badgeClass}`}>
      {a.replace(/_/g, ' ').toUpperCase()}
    </span>
  );
}
