import React from 'react';
import { HelpCircle } from 'lucide-react';

interface WhyButtonProps {
  onClick: (e: React.MouseEvent) => void;
  label?: string;
  className?: string;
}

export function WhyButton({ onClick, label = 'Why?', className = '' }: WhyButtonProps) {
  return (
    <button
      type="button"
      className={`why-trigger-btn ${className}`}
      onClick={(e) => {
        e.stopPropagation();
        onClick(e);
      }}
      title="Inspect scientific reasoning, evidence chain, and provenance"
    >
      <HelpCircle size={11} />
      <span>{label}</span>
    </button>
  );
}
