import { content, eyebrow, formError, pageLead, pageTitle, projectCard, projectGrid, sectionTitle, workPanel } from "@/app/ui-styles";
import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { AppShell } from "../app-shell";
import { fetchCurrentUser } from "@/lib/backend";
import { loadProjects, type Project } from "@/lib/projects";
import { accessCookie } from "@/lib/session";
import { CreateProjectForm } from "./create-project-form";

export const dynamic = "force-dynamic";

export default async function ProjectsPage() {
  const access = (await cookies()).get(accessCookie)?.value;
  if (!access) redirect("/login");
  const user = await fetchCurrentUser(access);
  if (!user) redirect("/login");
  let projects: Project[];
  let error = "";
  try { projects = await loadProjects(); } catch { projects = []; error = "Не удалось загрузить список проектов. Обновите страницу."; }
  return (
    <AppShell userName={user.display_name} section="Проекты">
      <main className={content} id="main-content">
        <span className={eyebrow}>Рабочее пространство</span>
        <h1 className={pageTitle}>Проекты</h1>
        <p className={pageLead}>Создайте проект для клиента и соберите его контекст в одном месте.</p>
        <section className={workPanel}>
          <h2 className="mb-3.5 text-[17px]">Новый проект</h2>
          <CreateProjectForm />
        </section>
        <h2 className={sectionTitle}>Ваши проекты</h2>
        {error && (
          <p className={formError} role="alert">
            {error}
          </p>
        )}
        {projects.length === 0 && !error ? (
          <p className="rounded-[14px] border border-dashed border-line p-8 text-muted">
            Проектов пока нет. Создайте первый проект выше.
          </p>
        ) : (
          <div className={projectGrid}>
            {projects.map((project) => (
              <Link className={projectCard} href={`/projects/${project.id}`} key={project.id}>
                <span
                  className="grid size-10 place-items-center rounded-[11px] bg-tint text-[19px] font-extrabold text-accent"
                  aria-hidden="true"
                >
                  {project.name.slice(0, 1).toUpperCase()}
                </span>
                <strong className="text-base">{project.name}</strong>
                <span className="font-bold text-accent">Открыть контекст →</span>
              </Link>
            ))}
          </div>
        )}
      </main>
    </AppShell>
  );
}
