/**
 * NEXUS API Client
 * Connects directly to FastAPI backend routes and WebSockets.
 */
import type {
  ResearchSession,
  Paper,
  PaperAnalysis,
  Claim,
  Evidence,
  Contradiction,
  ConsensusFinding,
  ResearchGap,
  MissingExperiment,
  NoveltyAssessment,
  ExperimentProposal,
  AuditResult,
  RedTeamResult,
  AgentEvent,
  CitationEdge,
  MethodPipeline,
  WhyExplanation,
  TimelineMilestone,
  DeadEnd,
  ReproducibilityProfile,
  ClaimPropagation,
  CitationEchoCluster,
  ResearchGraph,
} from '../types/research';

const HOST = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
const PROTOCOL = typeof window !== 'undefined' && window.location.protocol === 'https:' ? 'https:' : 'http:';
const WS_PROTOCOL = PROTOCOL === 'https:' ? 'wss:' : 'ws:';
const PORT = '8000';
const API_BASE = (import.meta as any).env?.VITE_API_URL || `${PROTOCOL}//${HOST}:${PORT}/api`;
const WS_BASE = (import.meta as any).env?.VITE_WS_URL || `${WS_PROTOCOL}//${HOST}:${PORT}/api`;

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    let errorDetail = res.statusText;
    try {
      const errJson = await res.json();
      if (errJson.detail) errorDetail = errJson.detail;
    } catch {
      // keep statusText
    }
    throw new Error(`API Error ${res.status}: ${errorDetail}`);
  }
  return res.json();
}

export const api = {
  health: () =>
    apiFetch<{ status: string; demo_mode: boolean; gemini_configured: boolean; app: string }>('/health'),

  startResearch: (question: string) =>
    apiFetch<{ id: string; status: string; message: string }>('/research/start', {
      method: 'POST',
      body: JSON.stringify({ question }),
    }),

  listSessions: () =>
    apiFetch<{ sessions: Array<{ id: string; question: string; title: string; status: string; stats?: any; is_demo?: boolean; created_at?: string }> }>('/research/sessions'),

  getSession: (id: string) =>
    apiFetch<ResearchSession>(`/research/session/${id}`),

  getPapers: (id: string) =>
    apiFetch<{ papers: Paper[] }>(`/research/session/${id}/papers`),

  getPaperDetail: (sessionId: string, paperId: string) =>
    apiFetch<{ paper: Paper; analysis: PaperAnalysis | null }>(`/research/session/${sessionId}/paper/${paperId}`),

  getClaims: (id: string) =>
    apiFetch<{ claims: Claim[]; evidence: Evidence[] }>(`/research/session/${id}/claims`),

  getContradictions: (id: string) =>
    apiFetch<{ contradictions: Contradiction[] }>(`/research/session/${id}/contradictions`),

  getConsensus: (id: string) =>
    apiFetch<{ consensus: ConsensusFinding[] }>(`/research/session/${id}/consensus`),

  getGaps: (id: string) =>
    apiFetch<{ gaps: ResearchGap[]; missing_experiments: MissingExperiment[] }>(`/research/session/${id}/gaps`),

  getNovelty: (id: string) =>
    apiFetch<{ novelty: NoveltyAssessment | null }>(`/research/session/${id}/novelty`),

  analyzeNovelty: (id: string, idea: string) =>
    apiFetch<{ novelty: NoveltyAssessment }>(`/research/session/${id}/novelty`, {
      method: 'POST',
      body: JSON.stringify({ idea }),
    }),

  getExperiment: (id: string) =>
    apiFetch<{ experiment: ExperimentProposal | null }>(`/research/session/${id}/experiment`),

  getAudit: (id: string) =>
    apiFetch<{ audit: AuditResult | null; red_team: RedTeamResult | null }>(`/research/session/${id}/audit`),

  getEvents: (id: string) =>
    apiFetch<{ events: AgentEvent[] }>(`/research/session/${id}/events`),

  getCitations: (id: string) =>
    apiFetch<{ citations: CitationEdge[]; papers: Record<string, { id: string; title: string; year?: number }> }>(
      `/research/session/${id}/citations`
    ),

  getMethods: (id: string) =>
    apiFetch<{ methods: MethodPipeline[] }>(`/research/session/${id}/methods`),

  getDeadEnds: (id: string) =>
    apiFetch<{ dead_ends: DeadEnd[]; count: number }>(`/research/session/${id}/dead-ends`),

  getReproducibility: (id: string) =>
    apiFetch<{
      profiles: Record<string, ReproducibilityProfile>;
      count: number;
      average_completeness: number;
    }>(`/research/session/${id}/reproducibility`),

  getClaimPropagations: (id: string) =>
    apiFetch<{ propagations: ClaimPropagation[]; count: number; types: string[] }>(
      `/research/session/${id}/claim-propagations`
    ),

  getCitationEchoes: (id: string) =>
    apiFetch<{ echoes: CitationEchoCluster[]; count: number }>(`/research/session/${id}/citation-echoes`),

  getEvidenceStrength: (id: string) =>
    apiFetch<{ claims: Claim[] }>(`/research/session/${id}/evidence-strength`),

  getResearchGraph: (id: string) =>
    apiFetch<ResearchGraph>(`/research/session/${id}/research-graph`),

  getTimeline: (id: string) =>
    apiFetch<{ milestones: TimelineMilestone[] }>(`/research/session/${id}/timeline`),

  getBibliography: (id: string, style: 'apa' | 'ieee' | 'bibtex' = 'apa') =>
    apiFetch<{ style: string; formatted: string; papers: Paper[] }>(
      `/research/session/${id}/bibliography?style=${style}`
    ),

  getDossier: (id: string) =>
    apiFetch<{ dossier: string; session: ResearchSession }>(`/research/session/${id}/dossier`),

  getWhy: (sessionId: string, targetType: string, targetId: string) =>
    apiFetch<{ explanation: WhyExplanation }>(
      `/research/session/${sessionId}/why?target_type=${encodeURIComponent(targetType)}&target_id=${encodeURIComponent(targetId)}`
    ),

  uploadPdf: async (sessionId: string, file: File): Promise<{ paper: Paper; message: string }> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/research/session/${sessionId}/upload-pdf`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      let msg = res.statusText;
      try {
        const j = await res.json();
        if (j.detail) msg = j.detail;
      } catch {
        // ignore
      }
      throw new Error(`Upload error ${res.status}: ${msg}`);
    }
    return res.json();
  },

  toggleDemoMode: () =>
    apiFetch<{ demo_mode: boolean; message: string }>('/config/toggle-mode', { method: 'POST' }),
};

export function connectWebSocket(sessionId: string, onEvent: (event: AgentEvent) => void): WebSocket {
  const ws = new WebSocket(`${WS_BASE}/ws/research/${sessionId}`);
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onEvent(data);
    } catch (e) {
      console.error('WS parse error:', e);
    }
  };
  ws.onerror = (e) => console.error('WS error:', e);
  return ws;
}
