"use server";

import { revalidatePath } from "next/cache";
import { getTranslator } from "@/lib/server-language";
import { projectRequest } from "@/lib/projects";

export async function saveClient(id: string, revision: number, _previous: string, data: FormData) {
  const t = await getTranslator();
  const values = {
    revision, sales_mode: data.get("sales_mode"), package_name: data.get("package_name"),
    delivery_notes: data.get("delivery_notes"), video_style: data.get("video_style"),
    video_duration: Number(data.get("video_duration")),
  };
  const response = await projectRequest("/api/v1/admin/clients/" + encodeURIComponent(id), {
    method: "PUT", body: JSON.stringify(values), headers: {"Content-Type": "application/json"},
  });
  if (response.status === 409) return t("Настройки уже изменились. Обновите страницу и повторите правку.", "Settings changed. Refresh the page and reapply your edit.");
  if (!response.ok) return t("Не удалось сохранить настройки. Проверьте поля и доступ.", "Could not save settings. Check the fields and your access.");
  revalidatePath("/admin");
  revalidatePath("/projects/" + id + "/videos/new");
  return t("Сохранено", "Saved");
}
