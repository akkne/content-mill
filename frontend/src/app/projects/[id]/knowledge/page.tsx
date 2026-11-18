import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { AppShell } from "@/app/app-shell";
import { fetchCurrentUser } from "@/lib/backend";
import { loadKnowledge } from "@/lib/knowledge";
import { loadProject } from "@/lib/projects";
import { accessCookie } from "@/lib/session";
import { KnowledgeBrowser } from "./knowledge-browser";

export const dynamic = "force-dynamic";

export default async function KnowledgePage({ params }: { params: Promise<{ id: string }> }) {
  const access = (await cookies()).get(accessCookie)?.value;
  if (!access) redirect("/login");
  const user = await fetchCurrentUser(access);
  if (!user) redirect("/login");
  const { id } = await params;
  let project;
  let nodes;
  try {
    [project, nodes] = await Promise.all([loadProject(id), loadKnowledge(id)]);
  } catch {
    return <AppShell userName={user.display_name} section="База знаний"><main className="content" id="main-content"><h1 className="page-title">Проект недоступен</h1><Link href="/projects">Вернуться к проектам</Link></main></AppShell>;
  }
  return <AppShell userName={user.display_name} section="База знаний"><main className="content" id="main-content">
    <Link className="back-link" href={`/projects/${id}`}>← Контекст проекта</Link>
    <span className="eyebrow">База знаний</span>
    <h1 className="page-title">{project.name}</h1>
    <p className="page-lead">Организуйте материалы проекта по папкам, создавайте текстовые документы и возвращайтесь к прежним версиям.</p>
    <KnowledgeBrowser initial={nodes} projectId={id} projectName={project.name} />
  </main></AppShell>;
}
