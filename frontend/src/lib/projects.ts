import "server-only";

import { cookies } from "next/headers";
import { backendUrl } from "./backend";
import { accessCookie } from "./session";

export type Project = { id: string; owner_id: string; name: string; revision: number; created_at: string };
export type ProjectContext = {
  project_id: string;
  revision: number;
  description: string;
  audiences: string[];
  products: { name: string; description: string }[];
  facts: { text: string; source_url: string | null }[];
  tone_of_voice: string;
  forbidden_terms: string[];
  source_version_ids: string[];
};

export async function projectRequest(path: string, init?: RequestInit): Promise<Response> {
  const token = (await cookies()).get(accessCookie)?.value;
  if (!token) throw new Error("Сессия истекла. Войдите снова.");
  return fetch(backendUrl(path), {
    ...init,
    headers: { Authorization: `Bearer ${token}`, ...init?.headers },
    cache: "no-store",
  });
}

export async function loadProjects(): Promise<Project[]> {
  const projects: Project[] = [];
  let cursor: string | null = null;
  do {
    const response = await projectRequest(`/api/v1/projects?limit=100${cursor ? `&cursor=${cursor}` : ""}`);
    if (!response.ok) throw new Error("Не удалось загрузить проекты");
    const data = await response.json() as { items: Project[]; next_cursor: string | null };
    projects.push(...data.items);
    cursor = data.next_cursor;
  } while (cursor);
  return projects;
}

export async function loadProject(id: string): Promise<Project> {
  const response = await projectRequest(`/api/v1/projects/${id}`);
  if (!response.ok) throw new Error("Проект не найден или недоступен");
  return response.json() as Promise<Project>;
}

export async function loadContext(id: string): Promise<ProjectContext> {
  const response = await projectRequest(`/api/v1/projects/${id}/context`);
  if (!response.ok) throw new Error("Не удалось загрузить контекст");
  return response.json() as Promise<ProjectContext>;
}
