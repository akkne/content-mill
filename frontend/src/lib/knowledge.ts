import "server-only";

import { projectRequest } from "./projects";

export type KnowledgeNode = {
  id: string;
  project_id: string;
  parent_id: string | null;
  kind: "folder" | "document" | "image" | "audio" | "video" | "file";
  voice_language: string | null;
  folder_role: string | null;
  description: string | null;
  elevenlabs_voice_id: string | null;
  linked_voice_id: string | null;
  voice_model: string | null;
  name: string;
  revision: number;
  created_at: string;
  archived_at: string | null;
};

export async function loadKnowledge(projectId: string): Promise<KnowledgeNode[]> {
  const response = await projectRequest(`/api/v1/projects/${projectId}/nodes/tree`);
  if (!response.ok) throw new Error("Не удалось загрузить базу знаний");
  const data = await response.json() as { items: KnowledgeNode[] };
  return data.items;
}
