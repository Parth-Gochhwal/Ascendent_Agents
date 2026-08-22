import { useState, useEffect } from 'react';
import { Settings2 } from 'lucide-react';
import type { MethodPipeline, ResearchSession } from '../types/research';
import { api } from '../services/api';
import { WhyButton } from '../components/common/WhyButton';
import { EmptyState } from '../components/common/EmptyState';

interface MethodsPageProps {
  sessionId: string;
  session: ResearchSession | null;
  onWhy: (type: string, id: string) => void;
}

export function MethodsPage({ sessionId, session, onWhy }: MethodsPageProps) {
  const [methods, setMethods] = useState<MethodPipeline[]>([]);

  useEffect(() => {
    api.getMethods(sessionId)
      .then((d: { methods: MethodPipeline[] }) => setMethods(d.methods || []))
      .catch(() => {});
  }, [sessionId, session?.status]);

  const uniqueModels = Array.from(new Set(methods.map((m) => m.model_architecture).filter(Boolean))) as string[];
  const uniqueDatasets = Array.from(new Set(methods.map((m) => m.dataset).filter(Boolean))) as string[];

  return (
    <div className="workspace-content animate-fade-in">
      {/* Header */}
      <div style={{ marginBottom: 'var(--space-5)' }}>
        <div className="card-section-label">METHODOLOGICAL REPOSITORY</div>
        <h1 style={{ fontFamily: 'var(--font-serif)', fontSize: '1.75rem' }}>
          Methodological Pipelines & Coverage Matrix
        </h1>
        <p style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>
          Detailed architectures, loss functions, evaluation protocols, and Model × Dataset intersection matrix
        </p>
      </div>

      {/* 2D Coverage Grid (Model vs Dataset Matrix) */}
      <div className="editorial-card highlight-indigo" style={{ marginBottom: 'var(--space-5)' }}>
        <div className="card-editorial-header">
          <div>
            <div className="card-section-label">2D COVERAGE INTERSECTION</div>
            <h3 className="card-editorial-title">Model Architecture × Benchmark Dataset Matrix</h3>
          </div>
          <div style={{ display: 'flex', gap: 8, fontSize: 11, fontFamily: 'var(--font-mono)' }}>
            <span style={{ color: 'var(--accent-teal)' }}>■ Explored</span>
            <span style={{ color: 'var(--text-tertiary)' }}>□ Underexplored</span>
          </div>
        </div>

        {uniqueModels.length > 0 && uniqueDatasets.length > 0 ? (
          <div className="scholarly-table-container" style={{ marginTop: 10 }}>
            <table className="scholarly-table">
              <thead>
                <tr>
                  <th>Model Architecture</th>
                  {uniqueDatasets.map((d) => (
                    <th key={d} style={{ textAlign: 'center' }}>{d}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {uniqueModels.map((model) => (
                  <tr key={model}>
                    <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{model}</td>
                    {uniqueDatasets.map((dataset) => {
                      const match = methods.some(
                        (m) => m.model_architecture === model && m.dataset === dataset
                      );

                      return (
                        <td
                          key={dataset}
                          style={{
                            textAlign: 'center',
                            background: match ? 'rgba(20, 184, 166, 0.08)' : 'transparent',
                          }}
                        >
                          {match ? (
                            <span style={{ color: 'var(--accent-teal)', fontWeight: 700 }}>✓ Explored</span>
                          ) : (
                            <span style={{ color: 'var(--text-dim)', fontSize: 11 }}>— Underexplored</span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ padding: '20px 0', color: 'var(--text-tertiary)', fontSize: 13 }}>
            Extracting method pipelines to populate 2D intersection matrix...
          </div>
        )}
      </div>

      {/* Structured Method Pipeline Cards */}
      {methods.length > 0 ? (
        <div style={{ display: 'grid', gap: 'var(--space-3)' }}>
          {methods.map((m, i) => (
            <div key={m.id || i} className="editorial-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  {m.model_architecture && (
                    <span className="nexus-badge badge-indigo">{m.model_architecture}</span>
                  )}
                  {m.dataset && (
                    <span className="nexus-badge badge-blue">{m.dataset}</span>
                  )}
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-tertiary)' }}>
                    Paper: {m.paper_id.slice(0, 10)}
                  </span>
                </div>
                <WhyButton label="Paper Context" onClick={() => onWhy('paper', m.paper_id)} />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12, fontSize: 13 }}>
                {m.preprocessing && m.preprocessing.length > 0 && (
                  <div style={{ background: 'var(--bg-tertiary)', padding: 10, borderRadius: 'var(--radius-sm)' }}>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)' }}>PREPROCESSING PIPELINE</div>
                    <div style={{ color: 'var(--text-primary)', marginTop: 4 }}>{m.preprocessing.join(' → ')}</div>
                  </div>
                )}
                {m.loss_function && (
                  <div style={{ background: 'var(--bg-tertiary)', padding: 10, borderRadius: 'var(--radius-sm)' }}>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)' }}>LOSS FUNCTION</div>
                    <div style={{ color: 'var(--text-primary)', marginTop: 4 }}>{m.loss_function}</div>
                  </div>
                )}
                {m.optimizer && (
                  <div style={{ background: 'var(--bg-tertiary)', padding: 10, borderRadius: 'var(--radius-sm)' }}>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)' }}>OPTIMIZER & HYPERPARAMETERS</div>
                    <div style={{ color: 'var(--text-primary)', marginTop: 4 }}>{m.optimizer}</div>
                  </div>
                )}
                {m.evaluation_protocol && (
                  <div style={{ background: 'var(--bg-tertiary)', padding: 10, borderRadius: 'var(--radius-sm)' }}>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)' }}>EVALUATION PROTOCOL</div>
                    <div style={{ color: 'var(--text-primary)', marginTop: 4 }}>{m.evaluation_protocol}</div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState
          icon={<Settings2 size={24} />}
          title="No Methodological Pipelines Extracted"
          description="Pipeline extraction maps model components, loss objectives, and evaluation protocols."
        />
      )}
    </div>
  );
}
