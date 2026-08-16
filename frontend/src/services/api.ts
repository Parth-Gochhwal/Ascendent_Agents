/** NEXUS API Client */
const API_BASE = 'http://localhost:8000/api';

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API Error ${res.status}: ${res.statusText}`);
  }
  return res.json();
}

export const api = {
  health: () => apiFetch<{ status: string; demo_mode: boolean }>('/health'),

  startResearch: (question: string) =>
    apiFetch<{ id: string; status: string }>('/research/start', {
      method: 'POST',
      body: JSON.stringify({ question }),
    }),

  listSessions: () => apiFetch<{ sessions: any[] }>('/research/sessions'),

  getSession: (id: string) => apiFetch<any>(`/research/session/${id}`),

  getPapers: (id: string) => apiFetch<{ papers: any[] }>(`/research/session/${id}/papers`),

  getPaperDetail: (sessionId: string, paperId: string) =>
    apiFetch<{ paper: any; analysis: any }>(`/research/session/${sessionId}/paper/${paperId}`),

  getClaims: (id: string) => apiFetch<{ claims: any[]; evidence: any[] }>(`/research/session/${id}/claims`),

  getContradictions: (id: string) =>
    apiFetch<{ contradictions: any[] }>(`/research/session/${id}/contradictions`),

  getConsensus: (id: string) =>
    apiFetch<{ consensus: any[] }>(`/research/session/${id}/consensus`),

  getGaps: (id: string) =>
    apiFetch<{ gaps: any[]; missing_experiments: any[] }>(`/research/session/${id}/gaps`),

  getNovelty: (id: string) => apiFetch<{ novelty: any }>(`/research/session/${id}/novelty`),

  analyzeNovelty: (id: string, idea: string) =>
    apiFetch<{ novelty: any }>(`/research/session/${id}/novelty`, {
      method: 'POST',
      body: JSON.stringify({ idea }),
    }),

  getExperiment: (id: string) => apiFetch<{ experiment: any }>(`/research/session/${id}/experiment`),

  getAudit: (id: string) =>
    apiFetch<{ audit: any; red_team: any }>(`/research/session/${id}/audit`),

  getEvents: (id: string) => apiFetch<{ events: any[] }>(`/research/session/${id}/events`),

  getCitations: (id: string) =>
    apiFetch<{ citations: any[]; papers: Record<string, any> }>(`/research/session/${id}/citations`),

  getMethods: (id: string) => apiFetch<{ methods: any[] }>(`/research/session/${id}/methods`),

  getDossier: (id: string) => apiFetch<{ dossier: string; session: any }>(`/research/session/${id}/dossier`),

  getWhy: (sessionId: string, targetType: string, targetId: string) =>
    apiFetch<{ explanation: any }>(`/research/session/${sessionId}/why?target_type=${encodeURIComponent(targetType)}&target_id=${encodeURIComponent(targetId)}`),

  getTimeline: (id: string) =>
    apiFetch<{ milestones: any[] }>(`/research/session/${id}/timeline`),

  getBibliography: (id: string, style: string = 'apa') =>
    apiFetch<{ style: string; formatted: string; papers: any[] }>(`/research/session/${id}/bibliography?style=${style}`),

  uploadPdf: async (sessionId: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`http://localhost:8000/api/research/session/${sessionId}/upload-pdf`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) throw new Error(`Upload error ${res.status}: ${res.statusText}`);
    return res.json();
  },

  toggleDemoMode: () =>
    apiFetch<{ demo_mode: boolean; message: string }>('/config/toggle-mode', { method: 'POST' }),
};


export function connectWebSocket(sessionId: string, onEvent: (event: any) => void): WebSocket {
  const ws = new WebSocket(`ws://localhost:8000/api/ws/research/${sessionId}`);
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
