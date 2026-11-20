import "server-only";
import { notFound } from "next/navigation";
import { projectRequest } from "./projects";

export type VideoSource = {
  id: string;
  name: string;
  version: number;
  selected?: boolean;
};
export type VideoOptions = {
  project: string;
  products: string[];
  sources: VideoSource[];
  voices: Record<string, string>;
  options: {
    method: string[];
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
  settings: {
    library_voice_id?: string;
    voice?: string;
    duration: number;
    platform: string;
    method: string;
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
  const response = await videoRequest(project, path);
  if (response.status === 404) notFound();
  if (!response.ok) throw new Error("Не удалось загрузить ролики проекта");
  return response.json();
}
