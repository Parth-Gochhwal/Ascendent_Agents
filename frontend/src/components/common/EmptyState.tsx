import React from 'react';
import { Microscope } from 'lucide-react';

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description: string;
  action?: React.ReactNode;
}

export function EmptyState({
  icon = <Microscope size={22} />,
  title,
  description,
  action,
}: EmptyStateProps) {
  return (
    <div className="scientific-empty-state">
      <div className="empty-state-icon">{icon}</div>
      <h3 className="empty-state-title">{title}</h3>
      <p className="empty-state-desc">{description}</p>
      {action && <div style={{ marginTop: 'var(--space-3)' }}>{action}</div>}
    </div>
  );
}
