import { getTranslator } from "@/lib/server-language";
import { LibraryIllustration } from "../library-illustration";
import { listSaved } from "../voices/actions";
import { loadProjects, projectRequest } from "@/lib/projects";
import { loadKnowledge } from "@/lib/knowledge";
import { KnowledgeBrowser } from "@/app/projects/[id]/knowledge/knowledge-browser";
import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { AppShell } from "@/app/app-shell";
import { backLink, content } from "@/app/ui-styles";
import { fetchCurrentUser } from "@/lib/backend";
import { accessCookie } from "@/lib/session";

export default async function AvatarsPage() {
  const t = await getTranslator();
  const token = (await cookies()).get(accessCookie)?.value;
  const user = token && (await fetchCurrentUser(token));
  if (!user) redirect("/login");

  const response = await projectRequest("/api/v1/avatars/workspace", {
    method: "POST",
  });
  if (!response.ok)
    throw new Error(
      t("Не удалось открыть библиотеку.", "Could not open library."),
    );
  const { project_id, assignments } = await response.json();
  const [nodes, projects, voices] = await Promise.all([
    loadKnowledge(project_id),
    loadProjects(),
    listSaved(),
  ]);
  return (
    <AppShell userName={user.display_name} isAdmin={user.is_admin} section="База знаний">
      <main className={content} id="main-content">
        <Link className={backLink} href="/knowledge">
          {t("← База знаний", "← Knowledge base")}
        </Link>
        <header className="flex items-center justify-between gap-4 overflow-hidden rounded-[22px] border border-line bg-hero px-6 py-8 shadow-panel sm:px-9">
          <div>
            <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
              {t("Аватары", "Avatars")}
            </h1>
            <p className="mt-3 text-sm leading-relaxed text-muted">
              {t(
                "Создайте персонажа и перетащите фото в папки лица, полного роста или одежды. Если у вас есть согласие на использование изображения или голоса, его можно сохранить в «Разрешениях».",
                "Create a character and drop photos into face, full-body or clothing folders. If you have consent to use the likeness or voice, you can save it in Permissions.",
              )}
            </p>
          </div>
          <LibraryIllustration kind="avatar" />
        </header>
        <KnowledgeBrowser
          initial={nodes}
          projectId={project_id}
          projectName={t("Моя библиотека", "My library")}
          initialSources={{ ids: [], revision: 1 }}
          avatarProjects={projects}
          avatarAssignments={assignments}
          libraryVoices={voices.data}
        />
      </main>
    </AppShell>
  );
}
