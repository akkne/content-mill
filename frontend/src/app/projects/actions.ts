"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { projectRequest, type ProjectContext } from "@/lib/projects";

export async function createProject(formData: FormData): Promise<string> {
  const name = String(formData.get("name") ?? "").trim();
  if (!name) return "Введите название проекта";
  let project: { id: string };
  try {
    const response = await projectRequest("/api/v1/projects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });
    if (!response.ok) return "Не удалось создать проект. Попробуйте ещё раз.";
    project = await response.json() as { id: string };
  } catch {
    return "Сервер недоступен. Повторите попытку позже.";
  }
  revalidatePath("/projects");
  redirect(`/projects/${project.id}`);
}

export async function saveProjectContext(
  id: string,
  revision: number,
  input: Partial<Omit<ProjectContext, "project_id" | "revision">>,
): Promise<{ context?: ProjectContext; error?: string; conflict?: boolean }> {
  try {
    const response = await projectRequest(`/api/v1/projects/${id}/context`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", "If-Match": String(revision) },
      body: JSON.stringify(input),
    });
    if (response.status === 409) return { error: "Контекст изменился в другой вкладке. Обновите страницу и повторите правку.", conflict: true };
    if (!response.ok) return { error: response.status === 422 ? "Проверьте длину и заполнение полей." : "Не удалось сохранить контекст." };
    const context = await response.json() as ProjectContext;
    revalidatePath(`/projects/${id}`);
    return { context };
  } catch {
    return { error: "Сервер недоступен. Повторите сохранение позже." };
  }
}

export async function renameProject(id: string, revision: number, name: string) {
  try {
    const response = await projectRequest(`/api/v1/projects/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", "If-Match": String(revision) },
      body: JSON.stringify({ name: name.trim() }),
    });
    if (response.status === 409) return "Название изменилось в другой вкладке. Обновите страницу.";
    if (!response.ok) return "Не удалось сохранить название проекта.";
    revalidatePath("/projects");
    revalidatePath(`/projects/${id}`, "layout");
    return "";
  } catch {
    return "Сервер недоступен. Повторите сохранение позже.";
  }
}
