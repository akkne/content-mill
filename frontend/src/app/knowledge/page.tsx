import { content, pageLead, pageTitle, projectCard, projectGrid, secondaryButton } from "@/app/ui-styles";
import { LibraryTiles } from "@/app/knowledge/library-tiles";
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
  return (
    <AppShell userName={user.display_name} section="База знаний">
      <main className={content} id="main-content">
        <h1 className={pageTitle}>База знаний</h1>
        {projects.length ? (
          <>
            <p className={pageLead}>Выберите проект, чтобы открыть его папки и файлы.</p>
            <div className={projectGrid}>
              {projects.map((p) => (
                <Link className={projectCard} href={`/projects/${p.id}/knowledge`} key={p.id}>
                  <strong className="text-base">{p.name}</strong>
                  <span className="font-bold text-accent">Открыть папки →</span>
                </Link>
              ))}
            </div>
          </>
        ) : (
          <Link className={secondaryButton} href="/projects">
            Создать первый проект
          </Link>
        )}
        <LibraryTiles />
      </main>
    </AppShell>
  );
}
