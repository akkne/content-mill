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
  return <AppShell userName={user.display_name} section="Проекты"><main className="content" id="main-content">
    <span className="eyebrow">Рабочее пространство</span>
    <h1 className="page-title">Проекты</h1>
    <p className="page-lead">Создайте проект для клиента и соберите его контекст в одном месте.</p>
    <section className="work-panel project-create"><h2>Новый проект</h2><CreateProjectForm /></section>
    <h2 className="section-title">Ваши проекты</h2>
    {error && <p className="form-error" role="alert">{error}</p>}
    {projects.length === 0 && !error ? <p className="empty-state">Проектов пока нет. Создайте первый проект выше.</p> : <div className="project-grid">{projects.map((project) => <Link className="project-card" href={`/projects/${project.id}`} key={project.id}><span className="project-card-mark" aria-hidden="true">{project.name.slice(0, 1).toUpperCase()}</span><strong>{project.name}</strong><span>Открыть контекст →</span></Link>)}</div>}
  </main></AppShell>;
}
