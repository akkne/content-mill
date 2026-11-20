"use server";
import { getTranslator } from "@/lib/server-language";

import type { KnowledgeNode } from "@/lib/knowledge";
import { projectRequest } from "@/lib/projects";
import type { DocumentVersion } from "./actions";

type Reply<T> = { data: T; error?: never } | { data?: never; error: string };

async function request<T>(project: string, suffix: string, method = "GET", body?: object, revision?: number): Promise<Reply<T>> {
  const t = await getTranslator();
  try {
    const response = await projectRequest(`/api/v1/projects/${encodeURIComponent(project)}/${suffix}`, {
      method,
      headers: { "Content-Type": "application/json", ...(revision ? { "If-Match": String(revision) } : {}) },
      body: body ? JSON.stringify(body) : undefined,
    });
    const data = await response.json();
    if (!response.ok) return { error: data.error?.message || t("Не удалось выполнить операцию.", "Operation failed.") };
    return { data };
  } catch {
    return { error: t("Сервер недоступен. Повторите попытку позже.", "Server unavailable. Try again later.") };
  }
}

export async function beginUpload(project: string, file: { name: string; mime_type: string; size_bytes: number; sha256: string; parent_id: string | null; node_id?: string }, revision?: number) {
  return request<{ upload_id: string; upload_url: string }>(project, "files/uploads", "POST", file, revision);
}

export async function finishUpload(project: string, id: string) {
  return request<{ node: KnowledgeNode; version: DocumentVersion }>(project, `files/uploads/${encodeURIComponent(id)}/complete`, "POST");
}

export async function exampleFiles(project: string) {
  return request<{ items: KnowledgeNode[] }>(project, "files/examples", "POST");
}

export async function mediaPreview(project: string, id: string, version?: number) {
  const node = `nodes/${encodeURIComponent(id)}`;
  const [download, history] = await Promise.all([
    request<{ url: string; version: DocumentVersion }>(project, `${node}/download${version ? `?version=${version}` : ""}`),
    request<{ items: DocumentVersion[] }>(project, `${node}/versions`),
  ]);
  if (!download.data || !history.data) return { error: download.error || history.error };
  return { data: { ...download.data, versions: history.data.items } };
}

export async function saveProfile(project: string, id: string, revision: number, profile: { linked_voice_id: string | null }) {
  return request<KnowledgeNode>(project, `nodes/${encodeURIComponent(id)}/profile`, "PUT", profile, revision);
}
