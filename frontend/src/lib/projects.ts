import { getTranslator } from "@/lib/server-language";
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
  const t = await getTranslator();
  const token = (await cookies()).get(accessCookie)?.value;
  if (!token) throw new Error(t("Сессия истекла. Войдите снова.", "Session expired. Sign in again."));
  return fetch(backendUrl(path), {
    ...init,
    headers: { Authorization: `Bearer ${token}`, ...init?.headers },
    cache: "no-store",
  });
}

export async function loadProjects(): Promise<Project[]> {
  const t = await getTranslator();
  const projects: Project[] = [];
  let cursor: string | null = null;
  do {
    const response = await projectRequest(`/api/v1/projects?limit=100${cursor ? `&cursor=${cursor}` : ""}`);
    if (!response.ok) throw new Error(t("Не удалось загрузить проекты", "Could not load projects"));
    const data = await response.json() as { items: Project[]; next_cursor: string | null };
    projects.push(...data.items);
    cursor = data.next_cursor;
  } while (cursor);
  return projects;
}

export async function loadProject(id: string): Promise<Project> {
  const t = await getTranslator();
  const response = await projectRequest(`/api/v1/projects/${id}`);
  if (!response.ok) throw new Error(t("Проект не найден или недоступен", "Project unavailable or missing"));
  return response.json() as Promise<Project>;
}

export async function loadContext(id: string): Promise<ProjectContext> {
  const t = await getTranslator();
  const response = await projectRequest(`/api/v1/projects/${id}/context`);
  if (!response.ok) throw new Error(t("Не удалось загрузить контекст", "Could not load context"));
  return response.json() as Promise<ProjectContext>;
}

export type ScriptJob = {
  id: string;
  brief: string;
  model: string;
  run_at: string;
  status: "queued" | "running" | "done" | "failed" | "cancelled";
  result: string | null;
};
export async function loadScripts(id: string): Promise<{ enabled: boolean; items: ScriptJob[] }> {
  const t = await getTranslator();
  const response = await projectRequest(`/api/v1/projects/${encodeURIComponent(id)}/scripts`);
  if (!response.ok) throw new Error(t("Не удалось загрузить сценарии", "Could not load scripts"));
  return response.json();
}
