import type { VideoFailure } from "./video-failure";
import { getTranslator } from "@/lib/server-language";
import "server-only";
import { notFound } from "next/navigation";
import { projectRequest } from "./projects";

export type VideoSource = {
  id: string;
  name: string;
  version: number;
  format?: string;
  selected?: boolean;
  path?: string;
  node_id?: string;
  parent_id?: string | null;
  character_id?: string | null;
};
export type VideoOptions = {
  motion_default: string;
  project: string;
  products: string[];
  folders: { id: string; parent_id: string | null; name: string }[];
  sources: VideoSource[];
  avatars: {id:string;name:string;default_voice_id:string|null}[];
  lipsync_available: boolean;
  cast_voices: {id:string;name:string;preview:string|null;external_id:string}[];
  voices: Record<string, string>;
  defaults: { duration: number; editing_style: string };
  options: {
    method: string[];
    editing_style: string[];
    platform: string[];
    duration: number[];
    language: string[];
  };
};
export type VideoCard = {
  id: string;
  title: string;
  status: string;
  created_at: string;
  duration: number;
  platform: string;
};
export type ProjectVideo = Omit<VideoCard, "duration" | "platform"> & {
  motion_title?: {ru:string; en:string} | null;
  settings: {
    production?: { motion_export?: { project: string }; stage: string; clip_model?: string; index?: number; line?: number; operation?: string; error?: string; failure?: VideoFailure; files?: Record<string, { node: string; version: string }> };
    short_shots?: boolean;
    speaker_source_id?: string;
    library_voice_id?: string;
    voice?: string;
    duration: number;
    platform: string;
    method: string;
    editing_style?: string;
    sources: (VideoSource & { node_id: string; format: string })[];
    publication?: string;
  };
  progress: number;
  script: string;
  caption: string;
  journal: string[];
};

export async function videoRequest(project: string, path = "", body?: object) {
  return projectRequest(
    `/api/v1/projects/${encodeURIComponent(project)}/videos${path}`,
    body && {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    },
  );
}

export async function loadVideos<T>(project: string, path = ""): Promise<T> {
  const t = await getTranslator();
  const response = await videoRequest(project, path);
  if (response.status === 404) notFound();
  if (!response.ok) throw new Error(t("Не удалось загрузить ролики проекта", "Could not load project videos"));
  return response.json();
}
