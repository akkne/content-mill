"use server";

import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";
import { videoRequest } from "@/lib/videos";

export async function saveVideo(
  project: string,
  video: string | null,
  data: FormData,
): Promise<string> {
  const action = String(data.get("action") || "");
  const body = video
    ? { action, value: data.get("value") || "" }
    : {
        ...Object.fromEntries(data),
        action: undefined,
        duration: Number(data.get("duration")),
        sources: data.getAll("sources"),
        assemble: action === "assemble",
      };
  const path = video ? "/" + encodeURIComponent(video) + "/actions" : "";
  let id: string;
  try {
    const res = await videoRequest(project, path, body);
    const result = await res.json();
    if (!res.ok) return result.error?.message || "Не удалось сохранить ролик";
    id = result.id;
  } catch {
    return "Сервер недоступен. Попробуйте ещё раз.";
  }
  const base = `/projects/${project}/videos`;
  revalidatePath(base, "layout");
  if (!video || action === "duplicate") redirect(base + "/" + id);
  if (action === "delete") redirect(base);
  return "";
}
