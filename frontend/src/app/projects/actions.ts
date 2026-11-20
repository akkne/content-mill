"use server";
import { apiError } from "@/lib/api-error";
import { getTranslator } from "@/lib/server-language";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { projectRequest, type ProjectContext } from "@/lib/projects";

export async function createProject(formData: FormData): Promise<string> {
  const t = await getTranslator();
  const name = String(formData.get("name") ?? "").trim();
  if (!name) return t("Введите название проекта", "Enter a project name");
  let project: { id: string };
  try {
    const response = await projectRequest("/api/v1/projects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });
    if (!response.ok) return t("Не удалось создать проект. Попробуйте ещё раз.", "Could not create project. Try again.");
    project = await response.json() as { id: string };
  } catch {
    return t("Сервер недоступен. Повторите попытку позже.", "Server unavailable. Try again later.");
  }
  revalidatePath("/projects");
  redirect(`/projects/${project.id}`);
}

export async function saveProjectContext(
  id: string,
  revision: number,
  input: Partial<Omit<ProjectContext, "project_id" | "revision">>,
): Promise<{ context?: ProjectContext; error?: string; conflict?: boolean }> {
  const t = await getTranslator();
  try {
    const response = await projectRequest(`/api/v1/projects/${id}/context`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", "If-Match": String(revision) },
      body: JSON.stringify(input),
    });
    if (response.status === 409) return { error: t("Контекст изменился в другой вкладке. Обновите страницу и повторите правку.", "The context changed in another tab. Refresh the page and edit again."), conflict: true };
    if (!response.ok) return { error: response.status === 422 ? t("Проверьте длину и заполнение полей.", "Check field lengths and required values.") : t("Не удалось сохранить контекст.", "Could not save context.") };
    const context = await response.json() as ProjectContext;
    revalidatePath(`/projects/${id}`);
    return { context };
  } catch {
    return { error: t("Сервер недоступен. Повторите сохранение позже.", "Server unavailable. Try saving later.") };
  }
}

export async function renameProject(id: string, revision: number, name: string) {
  const t = await getTranslator();
  try {
    const response = await projectRequest(`/api/v1/projects/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", "If-Match": String(revision) },
      body: JSON.stringify({ name: name.trim() }),
    });
    if (response.status === 409) return t("Название изменилось в другой вкладке. Обновите страницу.", "The name changed in another tab. Refresh the page.");
    if (!response.ok) return t("Не удалось сохранить название проекта.", "Could not save project name.");
    revalidatePath("/projects");
    revalidatePath(`/projects/${id}`, "layout");
    return "";
  } catch {
    return t("Сервер недоступен. Повторите сохранение позже.", "Server unavailable. Try saving later.");
  }
}

export async function manageAgentToken(id: string, action: "issue" | "revoke"): Promise<{token?: string; message: string}> {
  const t = await getTranslator();
  try {
    const response = await projectRequest(`/api/v1/projects/${encodeURIComponent(id)}/mcp-token`, {
      method: action === "issue" ? "POST" : "DELETE",
    });
    if (!response.ok) return {message: t("Не удалось изменить доступ агента.", "Could not change agent access.")};
    if (action === "revoke") return {message: t("Доступ отозван.", "Access revoked.")};
    const {token, expires_at} = await response.json();
    return {token, message: t(`Действует до ${new Date(expires_at).toISOString()}.`, `Valid until ${new Date(expires_at).toISOString()}.`)};
  } catch {
    return {message: t("Сервер недоступен. Попробуйте ещё раз.", "Server unavailable. Try again.")};
  }
}

export async function prepareScript(project: string, brief: string, runAt: string | null) {
  const t = await getTranslator();
  try {
    const response = await projectRequest(`/api/v1/projects/${encodeURIComponent(project)}/scripts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ brief, run_at: runAt }),
    });
    if (!response.ok) return apiError(t, (await response.json()).error?.message, t("Не удалось запустить задание.", "Could not start job."));
    revalidatePath(`/projects/${project}`);
    return "";
  } catch {
    return t("Сервер недоступен. Попробуйте ещё раз.", "Server unavailable. Try again.");
  }
}

export async function cancelScript(project: string, job: string) {
  const t = await getTranslator();
  try {
    const response = await projectRequest(`/api/v1/projects/${encodeURIComponent(project)}/scripts/${encodeURIComponent(job)}`, { method: "DELETE" });
    revalidatePath(`/projects/${project}`);
    return response.ok ? t("Задание отменено.", "Job cancelled.") : t("Задание уже недоступно для отмены.", "The job can no longer be cancelled.");
  } catch {
    return t("Сервер недоступен.", "Server unavailable.");
  }
}
