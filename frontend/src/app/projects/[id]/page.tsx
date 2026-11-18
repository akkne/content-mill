import { backLink, content, eyebrow, pageLead, pageTitle, secondaryButton } from "@/app/ui-styles";
import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { AppShell } from "../../app-shell";
import { fetchCurrentUser } from "@/lib/backend";
import { loadContext, loadProject } from "@/lib/projects";
import { accessCookie } from "@/lib/session";
import { ProjectSettings } from "./project-settings";
import { ContextEditor } from "./context-editor";

export const dynamic = "force-dynamic";

export default async function ProjectPage({ params }: { params: Promise<{ id: string }> }) {
  const access = (await cookies()).get(accessCookie)?.value;
  if (!access) redirect("/login");
  const user = await fetchCurrentUser(access);
  if (!user) redirect("/login");
  const { id } = await params;
  let project;
  let context;
  try { [project, context] = await Promise.all([loadProject(id), loadContext(id)]); }
  catch { return <AppShell userName={user.display_name} section="Проекты"><main className={content} id="main-content"><Link href="/projects">← Проекты</Link><h1 className={pageTitle}>Проект недоступен</h1><p>Проверьте адрес или обновите страницу.</p></main></AppShell>; }
  return (
    <AppShell userName={user.display_name} section="Проекты">
      <main className={content} id="main-content">
        <Link className={backLink} href="/projects">
          ← Все проекты
        </Link>
        <span className={eyebrow}>Контекст клиента</span>
        <h1 className={pageTitle}>{project.name}</h1>
        <Link
          className={`${secondaryButton} mb-5 inline-flex items-center`}
          href={`/projects/${id}/knowledge`}
        >
          Открыть базу знаний →
        </Link>
        <p className={pageLead}>
          Укажите начальные данные о клиенте, аудитории, продуктах и подтверждённых фактах. Позже их можно
          будет изменить. Контекст сохраняется в проекте и будет доступен при создании контента.
        </p>
        <ProjectSettings project={project} />
        <ContextEditor initial={context} />
      </main>
    </AppShell>
  );
}
