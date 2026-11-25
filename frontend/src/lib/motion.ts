import { getTranslator } from "./server-language";
import { projectRequest } from "./projects";

export type MotionStyle = {
  id: string;
  brand: string;
  duration: number;
  accent: string;
  poster: string;
  reference: string;
  ru: MotionText;
  en: MotionText;
};
export type ReelFormat = {
  id: string;
  duration: number;
  ru: ReelText;
  en: ReelText;
};
type ReelText = {
  title: string;
  description: string;
  pace: string;
  beats: string;
};
type MotionText = {
  title: string;
  description: string;
  tags: string[];
  use: string;
};

export async function motionLibrary(project?: string) {
  const [catalog, reels, saved] = await Promise.all([
    projectRequest("/api/v1/motion/styles"),
    projectRequest("/api/v1/motion/reels"),
    project
      ? projectRequest(
          `/api/v1/projects/${encodeURIComponent(project)}/motion/styles`,
        )
      : null,
  ]);
  if (!reels.ok || !catalog.ok || (saved && !saved.ok)) {
    const t = await getTranslator();
    throw new Error(
      t("Каталог монтажа недоступен.", "Editing catalog unavailable."),
    );
  }
  return {
    reels: (await reels.json()) as ReelFormat[],
    styles: (await catalog.json()) as MotionStyle[],
    saved: saved ? ((await saved.json()) as string[]) : [],
  };
}
