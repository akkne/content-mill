"use server";

import { revalidatePath } from "next/cache";

import { projectRequest } from "@/lib/projects";
import type { KnowledgeNode } from "@/lib/knowledge";

type Result = { node?: KnowledgeNode; error?: string; conflict?: boolean };

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
