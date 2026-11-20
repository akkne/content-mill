"use server";
import { getTranslator } from "@/lib/server-language";

import { revalidatePath } from "next/cache";

import { projectRequest } from "@/lib/projects";
import { loadKnowledge, type KnowledgeNode } from "@/lib/knowledge";

type Result = { items?: KnowledgeNode[]; node?: KnowledgeNode; error?: string; conflict?: boolean };

export async function searchKnowledge(projectId: string, query: string): Promise<{ ids?: string[]; error?: string }> {
  const t = await getTranslator();
  try {
    const response = await projectRequest(`/api/v1/projects/${projectId}/search?q=${encodeURIComponent(query)}`);
    if (!response.ok) return { error: t("Не удалось выполнить поиск.", "Search failed.") };
    const data = await response.json() as { items: KnowledgeNode[] };
    return { ids: data.items.map((item) => item.id) };
  } catch {
    return { error: t("Сервер недоступен. Повторите поиск позже.", "Server unavailable. Try searching later.") };
  }
}

export type DocumentContent = { node_id: string; revision: number; version: number; format: "markdown" | "plain"; content: string };
export type DocumentVersion = { id: string; node_id: string; version: number; format: string; size_bytes: number; sha256: string; created_at: string };

export async function loadDocument(projectId: string, nodeId: string, version?: number): Promise<{ document?: DocumentContent; versions?: DocumentVersion[]; error?: string }> {
  const t = await getTranslator();
  try {
    const base = `/api/v1/projects/${projectId}/nodes/${nodeId}`;
    const [content, history] = await Promise.all([
      projectRequest(`${base}/content${version ? `?version=${version}` : ""}`),
      projectRequest(`${base}/versions`),
    ]);
    if (!content.ok || !history.ok) return { error: t("Не удалось открыть документ.", "Could not open the document.") };
    const document = await content.json() as DocumentContent;
    const versions = (await history.json() as { items: DocumentVersion[] }).items;
    return { document, versions };
  } catch {
    return { error: t("Сервер недоступен. Повторите попытку позже.", "Server unavailable. Try again later.") };
  }
}

export async function saveDocument(projectId: string, nodeId: string, revision: number, content: string, format: "markdown" | "plain"): Promise<{ document?: DocumentContent; error?: string; conflict?: boolean }> {
  const t = await getTranslator();
  try {
    const response = await projectRequest(`/api/v1/projects/${projectId}/nodes/${nodeId}/content`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", "If-Match": String(revision) },
      body: JSON.stringify({ content, format }),
    });
    if (response.status === 409) return { error: t("Документ изменился в другой вкладке. Закройте и откройте его снова.", "The document changed in another tab. Close and reopen it."), conflict: true };
    if (!response.ok) return { error: response.status === 413 || response.status === 422 ? t("Документ слишком большой или имеет неверный формат.", "The document is too large or has an invalid format.") : t("Не удалось сохранить документ.", "Could not save the document.") };
    revalidatePath(`/projects/${projectId}/knowledge`);
    return { document: await response.json() as DocumentContent };
  } catch {
    return { error: t("Сервер недоступен. Повторите сохранение позже.", "Server unavailable. Try saving later.") };
  }
}

export async function changeKnowledgeNode(
  projectId: string,
  action: "create" | "rename" | "move" | "archive",
  data: { nodeId?: string; revision?: number; parentId?: string | null; name?: string; kind?: "folder" | "document" },
): Promise<Result> {
  const t = await getTranslator();
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
    if (response.status === 409) return { error: t("Данные изменились или имя уже занято. Обновите страницу.", "The data changed or the name is already in use. Refresh the page."), conflict: true };
    if (!response.ok) return { error: response.status === 422 ? t("Проверьте имя и папку назначения.", "Check the name and destination folder.") : t("Не удалось сохранить изменение.", "Could not save the change.") };
    revalidatePath(`/projects/${projectId}/knowledge`);
    if (action === "archive") return { items: await loadKnowledge(projectId) };
    const node = await response.json() as KnowledgeNode;
    if (action === "create" && node.folder_role === "avatar") return { node, items: await loadKnowledge(projectId) };
    return { node };
  } catch {
    return { error: t("Сервер недоступен. Повторите попытку позже.", "Server unavailable. Try again later.") };
  }
}
