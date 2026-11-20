import { getTranslator } from "@/lib/server-language";
import {
  pageTitle,
  pageLead,
  projectGrid,
  projectCard,
  secondaryButton,
} from "@/app/ui-styles";
import { loadProjects } from "@/lib/projects";
import Link from "next/link";
import { redirect } from "next/navigation";
import { VideoShell } from "./video-shell";

export default async function Videos({
  searchParams,
}: {
  searchParams: Promise<{ create?: string }>;
}) {
  const t = await getTranslator();
  const projects = await loadProjects();
  const suffix = (await searchParams).create === "1" ? "/new" : "";
  const href = (id: string) => `/projects/${id}/videos${suffix}`;
  if (projects.length === 1) redirect(href(projects[0].id));
  return (
    <VideoShell>
      <h1 className={pageTitle}>{suffix ? t("Создать ролик", "Create video") : t("Ролики", "Videos")}</h1>
      <p className={pageLead}>
        {projects.length
          ? t("Выберите проект.", "Select a project.")
          : t("Создайте проект, чтобы подготовить первый ролик.", "Create a project to prepare your first video.")}
      </p>
      {projects.length ? (
        <div className={projectGrid}>
          {projects.map((p) => (
            <Link className={projectCard} key={p.id} href={href(p.id)}>
              <strong>{p.name}</strong>
              <span className="text-accent">
                {suffix ? t("Создать ролик", "Create video") : t("Открыть ролики", "Open videos")} →
              </span>
            </Link>
          ))}
        </div>
      ) : (
        <Link className={secondaryButton} href="/projects">
          {t("Создать проект", "Create project")}
        </Link>
      )}
    </VideoShell>
  );
}
