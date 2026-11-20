import { getTranslator } from "@/lib/server-language";
import { KnowledgeHeader } from "@/app/knowledge/knowledge-header";
import { content, projectCard, projectGrid, secondaryButton } from "@/app/ui-styles";
import { LibraryTiles } from "@/app/knowledge/library-tiles";
import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { AppShell } from "@/app/app-shell";
import { fetchCurrentUser } from "@/lib/backend";
import { loadProjects } from "@/lib/projects";
import { accessCookie } from "@/lib/session";

export default async function KnowledgeProjects() {
  const t = await getTranslator();
  const token = (await cookies()).get(accessCookie)?.value;
  const user = token && await fetchCurrentUser(token);
  if (!user) redirect("/login");
  const projects = await loadProjects();
  if (projects.length === 1) redirect(`/projects/${projects[0].id}/knowledge`);
  return (
    <AppShell userName={user.display_name} section="База знаний">
      <main className={content} id="main-content">
        <KnowledgeHeader description={projects.length ? t("Выберите проект, чтобы открыть его папки и файлы.", "Choose a project to open its folders and files.") : t("Создайте проект, чтобы собрать материалы бренда и роликов в одном месте.", "Create a project to keep brand and video materials together.")} />
        {projects.length ? (
          <div className={projectGrid}>
            {projects.map((p) => (
              <Link className={projectCard} href={`/projects/${p.id}/knowledge`} key={p.id}>
                <strong className="text-base">{p.name}</strong>
                <span className="font-bold text-accent">{t("Открыть папки →", "Open folders →")}</span>
              </Link>
            ))}
          </div>
        ) : (
          <Link className={secondaryButton} href="/projects">
            {t("Создать первый проект", "Create your first project")}
          </Link>
        )}
        <LibraryTiles />
      </main>
    </AppShell>
  );
}
