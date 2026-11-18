"use server";

import { revalidatePath } from "next/cache";

import { projectRequest } from "@/lib/projects";
import type { KnowledgeNode } from "@/lib/knowledge";

type Result = { node?: KnowledgeNode; error?: string; conflict?: boolean };

export async function searchKnowledge(projectId: string, query: string): Promise<{ ids?: string[]; error?: string }> {
  try {
    const response = await projectRequest(`/api/v1/projects/${projectId}/search?q=${encodeURIComponent(query)}`);
    if (!response.ok) return { error: "Не удалось выполнить поиск." };
    const data = await response.json() as { items: KnowledgeNode[] };
    return { ids: data.items.map((item) => item.id) };
  } catch {
    return { error: "Сервер недоступен. Повторите поиск позже." };
  }
}

export type DocumentContent = { node_id: string; revision: number; version: number; format: "markdown" | "plain"; content: string };
export type DocumentVersion = { id: string; node_id: string; version: number; format: string; size_bytes: number; sha256: string; created_at: string };

export async function loadDocument(projectId: string, nodeId: string, version?: number): Promise<{ document?: DocumentContent; versions?: DocumentVersion[]; error?: string }> {
  try {
    const base = `/api/v1/projects/${projectId}/nodes/${nodeId}`;
    const [content, history] = await Promise.all([
      projectRequest(`${base}/content${version ? `?version=${version}` : ""}`),
      projectRequest(`${base}/versions`),
    ]);
    if (!content.ok || !history.ok) return { error: "Не удалось открыть документ." };
    const document = await content.json() as DocumentContent;
    const versions = (await history.json() as { items: DocumentVersion[] }).items;
    return { document, versions };
  } catch {
    return { error: "Сервер недоступен. Повторите попытку позже." };
  }
}

export async function saveDocument(projectId: string, nodeId: string, revision: number, content: string, format: "markdown" | "plain"): Promise<{ document?: DocumentContent; error?: string; conflict?: boolean }> {
  try {
    const response = await projectRequest(`/api/v1/projects/${projectId}/nodes/${nodeId}/content`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", "If-Match": String(revision) },
      body: JSON.stringify({ content, format }),
    });
    if (response.status === 409) return { error: "Документ изменился в другой вкладке. Закройте и откройте его снова.", conflict: true };
    if (!response.ok) return { error: response.status === 413 || response.status === 422 ? "Документ слишком большой или имеет неверный формат." : "Не удалось сохранить документ." };
    revalidatePath(`/projects/${projectId}/knowledge`);
    return { document: await response.json() as DocumentContent };
  } catch {
    return { error: "Сервер недоступен. Повторите сохранение позже." };
  }
}

export async function changeKnowledgeNode(
  projectId: string,
  action: "create" | "rename" | "move" | "archive",
  data: { nodeId?: string; revision?: number; parentId?: string | null; name?: string; kind?: "folder" | "document" },
): Promise<Result> {
  const base = `/api/v1/projects/${projectId}/nodes`;
  const path = action === "create" ? base : `${base}/${data.nodeId}${action === "move" ? "/move" : ""}`;
  const body = action === "create" ? { parent_id: data.parentId, name: data.name, kind: data.kind }
    : action === "rename" ? { name: data.name }
      : action === "move" ? { new_parent_id: data.parentId } : undefined;
  try {
    const response = await projectRequest(path, {
      method: action === "create" ? "POST" : action === "rename" ? "PATCH" : action === "move" ? "POST" : "DELETE",
      headers: { "Content-Type": "application/json", ...(data.revision ? { "If-Match": String(data.revision) } : {}) },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (response.status === 409) return { error: "Данные изменились или имя уже занято. Обновите страницу.", conflict: true };
    if (!response.ok) return { error: response.status === 422 ? "Проверьте имя и папку назначения." : "Не удалось сохранить изменение." };
    revalidatePath(`/projects/${projectId}/knowledge`);
    return action === "archive" ? {} : { node: await response.json() as KnowledgeNode };
  } catch {
    return { error: "Сервер недоступен. Повторите попытку позже." };
  }
}
