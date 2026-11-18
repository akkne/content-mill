import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { AppShell } from "@/app/app-shell";
import { fetchCurrentUser } from "@/lib/backend";
import { loadProjects } from "@/lib/projects";
import { accessCookie } from "@/lib/session";

export default async function KnowledgeProjects() {
  const token = (await cookies()).get(accessCookie)?.value;
  const user = token && await fetchCurrentUser(token);
  if (!user) redirect("/login");
  const projects = await loadProjects();
  if (projects.length === 1) redirect(`/projects/${projects[0].id}/knowledge`);
  return <AppShell userName={user.display_name} section="База знаний"><main className="content" id="main-content">
    <h1 className="page-title">База знаний</h1>
    {projects.length ? <><p className="page-lead">Выберите проект, чтобы открыть его папки и файлы.</p>
      <div className="project-grid">{projects.map(p => <Link className="project-card" href={`/projects/${p.id}/knowledge`} key={p.id}><strong>{p.name}</strong><span>Открыть папки →</span></Link>)}</div></>
      : <Link className="secondary-button" href="/projects">Создать первый проект</Link>}
  </main></AppShell>;
}
