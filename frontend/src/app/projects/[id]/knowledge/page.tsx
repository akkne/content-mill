import { KnowledgeHeader } from "@/app/knowledge/knowledge-header";
import { backLink, content, pageTitle } from "@/app/ui-styles";
import { LibraryTiles } from "@/app/knowledge/library-tiles";
import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { AppShell } from "@/app/app-shell";
import { fetchCurrentUser } from "@/lib/backend";
import { loadKnowledge } from "@/lib/knowledge";
import { loadContext, loadProject } from "@/lib/projects";
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
  let context;
  try {
    [project, nodes, context] = await Promise.all([loadProject(id), loadKnowledge(id), loadContext(id)]);
  } catch {
    return <AppShell userName={user.display_name} section="База знаний"><main className={content} id="main-content"><h1 className={pageTitle}>Проект недоступен</h1><Link href="/projects">Вернуться к проектам</Link></main></AppShell>;
  }
  return (
    <AppShell userName={user.display_name} section="База знаний">
      <main className={content} id="main-content">
        <Link className={backLink} href={`/projects/${id}`}>
          ← Контекст проекта
        </Link>
        <KnowledgeHeader project={project.name} description="Материалы бренда, товаров и роликов. Дважды нажмите файл, чтобы открыть его." />
        <KnowledgeBrowser
          initialSources={{ ids: context.source_version_ids, revision: context.revision }}
          initial={nodes}
          projectId={id}
          projectName={project.name}
        />
        <LibraryTiles />
      </main>
    </AppShell>
  );
}
