import { useState, useEffect } from 'react';
import { Sparkles, BookOpen, CheckCircle2 } from 'lucide-react';
import type { NoveltyAssessment, ResearchSession } from '../types/research';
import { api } from '../services/api';
import { WhyButton } from '../components/common/WhyButton';

interface NoveltyPageProps {
  sessionId: string;
  session: ResearchSession | null;
  onWhy: (type: string, id: string) => void;
}

export function NoveltyPage({ sessionId, session, onWhy }: NoveltyPageProps) {
  const [novelty, setNovelty] = useState<NoveltyAssessment | null>(null);
  const [idea, setIdea] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.getNovelty(sessionId)
      .then((d: { novelty: NoveltyAssessment | null }) => setNovelty(d.novelty))
      .catch(() => {});
  }, [sessionId, session?.status]);

  const analyzeHypothesis = async () => {
    if (!idea.trim()) return;
    setLoading(true);
    try {
      const d = await api.analyzeNovelty(sessionId, idea);
      setNovelty(d.novelty);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  return (
    <div className="workspace-content animate-fade-in">
      {/* Header */}
      <div style={{ marginBottom: 'var(--space-5)' }}>
        <div className="card-section-label">SCHOLARLY NOVELTY ASSESSMENT</div>
        <h1 style={{ fontFamily: 'var(--font-serif)', fontSize: '1.75rem' }}>
          Novelty & Prior Art Overlap Evaluator
        </h1>
        <p style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>
          Assess proposed research ideas, model architectures, or hypotheses against discovered literature
        </p>
      </div>

      {/* Hypothesis Input Box */}
      <div className="editorial-card" style={{ marginBottom: 'var(--space-5)' }}>
        <div className="card-section-label">TEST A PROPOSED RESEARCH HYPOTHESIS</div>
        <textarea
          style={{
            width: '100%',
            minHeight: 80,
            background: 'var(--bg-tertiary)',
            border: '1px solid var(--border-primary)',
            borderRadius: 'var(--radius-sm)',
            padding: '12px',
            fontFamily: 'var(--font-serif)',
            fontSize: 14,
            color: 'var(--text-primary)',
            marginTop: 8,
            resize: 'vertical',
          }}
          placeholder="State your proposed methodology or hypothesis (e.g., 'Domain-adaptive GAT with physics-informed electrochemical regularizer for cross-chemistry battery RUL prediction')..."
          value={idea}
          onChange={(e) => setIdea(e.target.value)}
        />

        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 10 }}>
          <button
            className="action-btn-primary"
            onClick={analyzeHypothesis}
            disabled={loading || !idea.trim()}
          >
            <Sparkles size={13} />
            <span>{loading ? 'COMPUTING LITERATURE OVERLAP...' : 'EVALUATE POTENTIAL NOVELTY'}</span>
          </button>
        </div>
      </div>

      {/* Assessment Results */}
      {novelty && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          {/* Verdict Card */}
          <div className="editorial-card highlight-teal">
            <div className="card-editorial-header">
              <div>
                <div className="card-section-label">SCHOLARLY NOVELTY VERDICT</div>
                <h3 className="card-editorial-title">
                  {novelty.assessment ? novelty.assessment.replace(/_/g, ' ').toUpperCase() : 'POTENTIALLY NOVEL'}
                </h3>
              </div>

              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <span className="nexus-badge badge-high">
                  {novelty.novelty_level ? String(novelty.novelty_level).toUpperCase() : 'NOVEL'}
                </span>
                <WhyButton onClick={() => onWhy('novelty', 'novelty')} />
              </div>
            </div>

            <p style={{ fontSize: 14, color: 'var(--text-primary)', lineHeight: 1.65 }}>
              {novelty.explanation}
            </p>
          </div>

          {/* Explored vs Unexplored 2-Column Comparison */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }}>
            {/* Explored */}
            <div className="editorial-card">
              <div className="card-section-label">ALREADY EXPLORED IN PRIOR ART</div>
              <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 6 }}>
                {novelty.explored_dimensions && novelty.explored_dimensions.length > 0 ? (
                  novelty.explored_dimensions.map((d: string, i: number) => (
                    <div key={i} style={{ fontSize: 13, color: 'var(--text-secondary)', display: 'flex', gap: 8 }}>
                      <CheckCircle2 size={14} color="var(--accent-steel)" style={{ flexShrink: 0, marginTop: 2 }} />
                      <span>{d}</span>
                    </div>
                  ))
                ) : (
                  <div style={{ color: 'var(--text-dim)', fontSize: 12 }}>No overlapping explored dimensions flagged.</div>
                )}
              </div>
            </div>

            {/* Potentially Unexplored */}
            <div className="editorial-card highlight-teal">
              <div className="card-section-label">POTENTIALLY UNEXPLORED ASPECTS</div>
              <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 6 }}>
                {novelty.potentially_unexplored && novelty.potentially_unexplored.length > 0 ? (
                  novelty.potentially_unexplored.map((d: string, i: number) => (
                    <div key={i} style={{ fontSize: 13, color: 'var(--accent-teal)', display: 'flex', gap: 8 }}>
                      <Sparkles size={14} color="var(--accent-teal)" style={{ flexShrink: 0, marginTop: 2 }} />
                      <span>{d}</span>
                    </div>
                  ))
                ) : (
                  <div style={{ color: 'var(--text-dim)', fontSize: 12 }}>No distinct unexplored facets detected.</div>
                )}
              </div>
            </div>
          </div>

          {/* Closest Prior Art Papers */}
          {novelty.closest_papers && novelty.closest_papers.length > 0 && (
            <div className="editorial-card">
              <div className="card-section-label">CLOSEST PRIOR ART CITATIONS</div>
              <div style={{ marginTop: 8, display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {novelty.closest_papers.map((pId: string, i: number) => (
                  <span key={i} className="telemetry-chip">
                    <BookOpen size={11} />
                    <span className="chip-value">Paper: {pId.slice(0, 12)}</span>
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
