import React from 'react';

export function TelemetryPill({
  label,
  value,
  variant = 'default',
}: {
  label?: string;
  value: React.ReactNode;
  variant?: 'default' | 'doi' | 'metric' | 'claim';
}) {
  if (variant === 'doi') {
    return <span className="doi-chip">DOI:{value}</span>;
  }

  return (
    <span className="telemetry-chip">
      {label && <span className="chip-label">{label}</span>}
      <span className="chip-value">{value}</span>
    </span>
  );
}

export function ClaimIdChip({ id }: { id: string }) {
  return (
    <span
      style={{
        fontFamily: 'var(--font-mono)',
        fontSize: '10px',
        color: 'var(--text-tertiary)',
        background: 'var(--bg-primary)',
        padding: '2px 5px',
        borderRadius: 'var(--radius-xs)',
        border: '1px solid var(--border-primary)',
      }}
    >
      #{id.slice(0, 8)}
    </span>
  );
}
