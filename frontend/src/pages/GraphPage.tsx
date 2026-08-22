import { useState, useEffect, useRef } from 'react';
import type { ResearchGraph, ResearchSession } from '../types/research';
import { api } from '../services/api';

interface GraphPageProps {
  sessionId: string;
  session: ResearchSession | null;
}

export function GraphPage({ sessionId, session }: GraphPageProps) {
  const [graph, setGraph] = useState<ResearchGraph | null>(null);
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [nodeTypeFilter, setNodeTypeFilter] = useState<string>('all');
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    api.getResearchGraph(sessionId)
      .then((d: ResearchGraph) => setGraph(d))
      .catch(() => {
        // Fallback: fetch citations
        api.getCitations(sessionId).then((c) => {
          const nodes = Object.entries(c.papers || {}).map(([id, p]) => ({
            id,
            node_type: 'PAPER' as const,
            label: p.title || id,
            metadata: { year: p.year },
          }));
          const edges = (c.citations || []).map((e) => ({
            source_id: e.source_paper_id,
            target_id: e.target_paper_id,
            edge_type: e.relation || 'CITES',
            weight: 1.0,
            metadata: {},
          }));
          setGraph({ nodes, edges, clusters: {} });
        }).catch(() => {});
      });
  }, [sessionId, session?.status]);

  const nodes = graph?.nodes || [];
  const edges = graph?.edges || [];

  const filteredNodes = nodes.filter(
    (n) => nodeTypeFilter === 'all' || n.node_type === nodeTypeFilter
  );

  // Position nodes in a clean radial orbital layout
  const nodePositions: Record<string, { x: number; y: number }> = {};
  const width = 860;
  const height = 580;
  const centerX = width / 2;
  const centerY = height / 2;

  filteredNodes.forEach((node, idx) => {
    const angle = (2 * Math.PI * idx) / Math.max(filteredNodes.length, 1);
    const radius = Math.min(220, 30 + filteredNodes.length * 15);
    nodePositions[node.id] = {
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle),
    };
  });

  return (
    <div className="workspace-content animate-fade-in">
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--space-4)' }}>
        <div>
          <div className="card-section-label">INTERACTIVE RESEARCH KNOWLEDGE GRAPH</div>
          <h1 style={{ fontFamily: 'var(--font-serif)', fontSize: '1.75rem' }}>
            Citation & Knowledge Network
          </h1>
          <p style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>
            {nodes.length} entities and {edges.length} relational edges mapped across papers and claims
          </p>
        </div>

        {/* Filter */}
        <div className="toolbar-group">
          <select
            style={{ height: 32, padding: '0 10px', fontSize: 11, fontFamily: 'var(--font-mono)' }}
            value={nodeTypeFilter}
            onChange={(e) => setNodeTypeFilter(e.target.value)}
          >
            <option value="all">ALL ENTITY TYPES ({nodes.length})</option>
            <option value="PAPER">PAPERS ONLY</option>
            <option value="CLAIM">CLAIMS ONLY</option>
            <option value="METHOD">METHODS ONLY</option>
          </select>
        </div>
      </div>

      {/* Graph Visual Container */}
      <div
        style={{
          background: 'var(--bg-secondary)',
          border: '1px solid var(--border-primary)',
          borderRadius: 'var(--radius-lg)',
          height: 600,
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <svg ref={svgRef} width="100%" height="100%" viewBox={`0 0 ${width} ${height}`}>
          <defs>
            <marker id="arrow" markerWidth="8" markerHeight="6" refX="12" refY="3" orient="auto">
              <polygon points="0 0, 8 3, 0 6" fill="var(--accent-steel)" />
            </marker>
            <marker id="arrow-crimson" markerWidth="8" markerHeight="6" refX="12" refY="3" orient="auto">
              <polygon points="0 0, 8 3, 0 6" fill="var(--accent-crimson)" />
            </marker>
          </defs>

          {/* Edges */}
          {edges.map((e, idx) => {
            const src = nodePositions[e.source_id];
            const tgt = nodePositions[e.target_id];
            if (!src || !tgt) return null;

            const isContradiction = e.edge_type === 'CONTRADICTS';

            return (
              <line
                key={idx}
                x1={src.x}
                y1={src.y}
                x2={tgt.x}
                y2={tgt.y}
                stroke={isContradiction ? 'var(--accent-crimson)' : 'var(--accent-steel)'}
                strokeWidth={isContradiction ? 2 : 1.2}
                strokeDasharray={isContradiction ? '4 2' : undefined}
                opacity={0.65}
                markerEnd={isContradiction ? 'url(#arrow-crimson)' : 'url(#arrow)'}
              />
            );
          })}

          {/* Nodes */}
          {filteredNodes.map((node) => {
            const pos = nodePositions[node.id];
            if (!pos) return null;

            const isSelected = selectedNode?.id === node.id;
            const isPaper = node.node_type === 'PAPER';

            return (
              <g
                key={node.id}
                transform={`translate(${pos.x}, ${pos.y})`}
                onClick={() => setSelectedNode(node)}
                style={{ cursor: 'pointer' }}
              >
                <circle
                  r={isPaper ? 22 : 16}
                  fill={isSelected ? 'var(--bg-elevated)' : 'var(--bg-tertiary)'}
                  stroke={isSelected ? 'var(--accent-teal)' : isPaper ? 'var(--accent-steel)' : 'var(--accent-indigo)'}
                  strokeWidth={isSelected ? 3 : 1.5}
                />
                <text
                  textAnchor="middle"
                  dy={4}
                  fill="var(--text-primary)"
                  fontSize={10}
                  fontFamily="var(--font-mono)"
                  fontWeight={600}
                >
                  {isPaper ? (node.metadata?.year || 'DOC') : node.node_type.slice(0, 3)}
                </text>
                <text
                  textAnchor="middle"
                  dy={32}
                  fill="var(--text-secondary)"
                  fontSize={10}
                  fontFamily="var(--font-sans)"
                >
                  {node.label.length > 20 ? `${node.label.substring(0, 18)}...` : node.label}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Selected Node Details Overlay */}
        {selectedNode && (
          <div
            style={{
              position: 'absolute',
              bottom: 16,
              left: 16,
              right: 16,
              maxWidth: 420,
              background: 'var(--bg-primary)',
              border: '1px solid var(--border-secondary)',
              borderRadius: 'var(--radius-md)',
              padding: 12,
              boxShadow: 'var(--shadow-elevated)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
              <span className="nexus-badge badge-blue">{selectedNode.node_type}</span>
              <button onClick={() => setSelectedNode(null)} style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>✕</button>
            </div>
            <div style={{ fontFamily: 'var(--font-serif)', fontSize: 13, color: 'var(--text-primary)', fontWeight: 500 }}>
              {selectedNode.label}
            </div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)', marginTop: 4 }}>
              ID: {selectedNode.id}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
