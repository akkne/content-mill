import { getTranslator } from "@/lib/server-language";
import { backLink, content, eyebrow, pageLead, pageTitle, secondaryButton } from "@/app/ui-styles";
import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { AppShell } from "../../app-shell";
import { fetchCurrentUser } from "@/lib/backend";
import { loadContext, loadProject, loadScripts } from "@/lib/projects";
import { accessCookie } from "@/lib/session";
import { ProjectSettings } from "./project-settings";
import { ScriptPanel } from "./script-panel";
import { ContextEditor } from "./context-editor";

export const dynamic = "force-dynamic";

export default async function ProjectPage({ params }: { params: Promise<{ id: string }> }) {
  const t = await getTranslator();
  const access = (await cookies()).get(accessCookie)?.value;
  if (!access) redirect("/login");
  const user = await fetchCurrentUser(access);
  if (!user) redirect("/login");
  const { id } = await params;
  let project;
  let context;
  try { [project, context] = await Promise.all([loadProject(id), loadContext(id)]); }
  catch { return <AppShell userName={user.display_name} isAdmin={user.is_admin} section="Проекты"><main className={content} id="main-content"><Link href="/projects">{t("← Проекты", "← Projects")}</Link><h1 className={pageTitle}>{t("Проект недоступен", "Project unavailable")}</h1><p>{t("Проверьте адрес или обновите страницу.", "Check the address or refresh the page.")}</p></main></AppShell>; }
  const scripts = await loadScripts(id).catch(() => null);
  return (
    <AppShell userName={user.display_name} isAdmin={user.is_admin} section="Проекты">
      <main className={content} id="main-content">
        <Link className={backLink} href="/projects">
          {t("← Все проекты", "← All projects")}
        </Link>
        <span className={eyebrow}>{t("Контекст клиента", "Client context")}</span>
        <h1 className={pageTitle}>{project.name}</h1>
        <Link
          className={`${secondaryButton} mb-5 inline-flex items-center`}
          href={`/projects/${id}/knowledge`}
        >
          {t("Открыть базу знаний →", "Open knowledge base →")}
        </Link>
        <p className={pageLead}>
          {t("Укажите начальные данные о клиенте, аудитории, продуктах и подтверждённых фактах. Позже их можно будет изменить. Контекст сохраняется в проекте и будет доступен при создании контента.", "Describe the client, audience, products and verified facts. You can edit these later. This project context will be available when creating content.")}
        </p>
        <ProjectSettings project={project} />
        {scripts ? <ScriptPanel id={id} {...scripts} /> : <p role="status">{t("Не удалось загрузить сценарии. Обновите страницу.", "Could not load scripts. Refresh the page.")}</p>}
        <ContextEditor initial={context} />
        <Link className={backLink} href={`/projects/${id}/integrations`}>{t("Внешние интеграции", "External integrations")}</Link>
      </main>
    </AppShell>
  );
}
