import type { GenerateAllResult, HealthStatus, Project, RenderResult, Scene } from './types';

const BASE = '/api';

async function asJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = '';
    try {
      detail = await res.text();
    } catch {
      /* ignore */
    }
    throw new Error(`${res.status} ${res.statusText}${detail ? ` — ${detail}` : ''}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => fetch(`${BASE}/health`).then((r) => asJson<HealthStatus>(r)),

  listProjects: () => fetch(`${BASE}/projects`).then((r) => asJson<Project[]>(r)),

  getProject: (id: string) => fetch(`${BASE}/projects/${id}`).then((r) => asJson<Project>(r)),

  saveProject: (p: Project) =>
    fetch(`${BASE}/projects/${p.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(p),
    }).then((r) => asJson<Project>(r)),

  generateScene: (projectId: string, sceneId: string, force = false) =>
    fetch(`${BASE}/projects/${projectId}/scenes/${sceneId}/generate?force=${force}`, {
      method: 'POST',
    }).then((r) => asJson<Scene>(r)),

  generateAll: (projectId: string, force = false, limit = 4) =>
    fetch(`${BASE}/projects/${projectId}/generate-all?force=${force}&limit=${limit}`, {
      method: 'POST',
    }).then((r) => asJson<GenerateAllResult>(r)),

  renderProject: (projectId: string) =>
    fetch(`${BASE}/projects/${projectId}/render`, { method: 'POST' }).then((r) =>
      asJson<RenderResult>(r),
    ),
};

export const mediaUrl = (relPath: string | null): string | undefined =>
  relPath ? `/media/${relPath}` : undefined;
