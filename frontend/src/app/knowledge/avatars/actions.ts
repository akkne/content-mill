"use server";
import { revalidatePath } from "next/cache";
import { projectRequest } from "@/lib/projects";
import { getTranslator } from "@/lib/server-language";

export async function assignAvatar(avatar: string, project: string) {
  const t = await getTranslator();
  try {
    const res = await projectRequest(
      `/api/v1/avatars/${encodeURIComponent(avatar)}/projects/${encodeURIComponent(project)}`,
      { method: "POST" },
    );
    if (res.status === 409)
      return t(
        "В проекте уже есть аватар с таким именем.",
        "This project already has an avatar with that name.",
      );
    if (res.ok) revalidatePath("/knowledge/avatars");
    return res.ok
      ? ""
      : t(
          "Не удалось добавить аватар в проект.",
          "Could not add this avatar to the project.",
        );
  } catch {
    return t("Сервер недоступен.", "Server unavailable.");
  }
}
