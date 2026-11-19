"use server";

import { revalidatePath } from "next/cache";
import { projectRequest } from "@/lib/projects";
import { loadKnowledge, type KnowledgeNode } from "@/lib/knowledge";
export type CatalogVoice = {
  id: string;
  name: string;
  description: string;
  languages: string[];
  gender: string | null;
  preview_url: string | null;
};
export type VoicePage = { items: CatalogVoice[]; next_cursor: string | null };
export type SavedVoice = Pick<
  KnowledgeNode,
  | "id"
  | "name"
  | "description"
  | "voice_language"
  | "catalog_languages"
  | "voice_gender"
  | "voice_preview_url"
  | "elevenlabs_voice_id"
  | "voice_model"
> & { project_ids: string[] };
type Reply<T> = { data: T; error?: never } | { error: string; data?: never };

async function request<T>(
  suffix: string,
  method = "GET",
  body?: object,
): Promise<Reply<T>> {
  try {
    const response = await projectRequest(`/api/v1/voices${suffix}`, {
      method,
      headers: { "Content-Type": "application/json" },
      body: body && JSON.stringify(body),
    });
    const data = await response.json();
    if (response.ok && method !== "GET") {
      revalidatePath("/knowledge/voices");
      revalidatePath("/projects/[id]/knowledge", "page");
    }
    return response.ok
      ? { data }
      : { error: data.error?.message || "Не удалось выполнить запрос" };
  } catch {
    return { error: "Сервер недоступен. Повторите попытку." };
  }
}
export async function listSaved() {
  return request<SavedVoice[]>("");
}
export async function listVoices(filters: Record<string, string>) {
  return request<VoicePage>(`/catalog?${new URLSearchParams(filters)}`);
}
export async function addVoice(body: {
  name: string;
  voice_id: string;
  from_catalog: boolean;
  gender: string | null;
  language: string;
  description: string;
  model: string | null;
}) {
  return request<SavedVoice>("", "POST", body);
}
export async function assignVoice(id: string, add: string[], remove: string[]) {
  return request<KnowledgeNode[]>(
    `/${encodeURIComponent(id)}/projects`,
    "PATCH",
    { add, remove },
  );
}
export async function editVoice(
  id: string,
  data: {
    description: string;
    voice_language: string;
    voice_gender: string | null;
    voice_model: string;
    elevenlabs_voice_id: string | null;
  },
) {
  return request<SavedVoice>(`/${encodeURIComponent(id)}`, "PATCH", data);
}

export async function addToOpenProject(id: string, project: string) {
  const assigned = await assignVoice(id, [project], []);
  if (!assigned.data?.[0])
    return { error: assigned.error ?? "Не удалось назначить голос" };
  try {
    return { node: assigned.data[0], items: await loadKnowledge(project) };
  } catch {
    return {
      error: "Голос назначен. Обновите страницу, чтобы загрузить папку.",
    };
  }
}
