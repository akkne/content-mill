"use server";
import { failureCode, videoFailureMessage } from "@/lib/video-failure";
import { apiError } from "@/lib/api-error";
import { getTranslator } from "@/lib/server-language";

import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";
import { videoRequest } from "@/lib/videos";

export async function saveVideo(
  project: string,
  video: string | null,
  data: FormData,
): Promise<string> {
  const t = await getTranslator();
  const action = String(data.get("action") || "");
  const body = video
    ? { action, value: data.get("value") || "" }
    : {
        ...Object.fromEntries(data),
        action: undefined,
        duration: Number(data.get("duration")),
        characters: JSON.parse(String(data.get("characters") || "[]")),
        sources: data.getAll("sources"),
        assemble: action === "assemble",
      };
  const path = video ? "/" + encodeURIComponent(video) + "/actions" : "";
  let id: string;
  try {
    const res = await videoRequest(project, path, body);
    const result = await res.json();
    if (!res.ok && result.error?.failure?.stage === "script") {
      const failure = result.error.failure;
      return [t("Подготовка сценария", "Script preparation"), videoFailureMessage(t, failure.reason), failureCode(failure)].join(" · ");
    }
    if (!res.ok) return apiError(t, result.error?.message, t("Не удалось сохранить ролик", "Could not save video"));
    id = result.id;
  } catch {
    return t("Сервер недоступен. Попробуйте ещё раз.", "Server unavailable. Try again.");
  }
  const base = `/projects/${project}/videos`;
  revalidatePath(base, "layout");
  if (!video || action === "duplicate") redirect(base + "/" + id);
  if (action === "delete") redirect(base);
  return "";
}
