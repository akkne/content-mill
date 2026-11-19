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
  const projects = await loadProjects();
  const suffix = (await searchParams).create === "1" ? "/new" : "";
  const href = (id: string) => `/projects/${id}/videos${suffix}`;
  if (projects.length === 1) redirect(href(projects[0].id));
  return (
    <VideoShell>
      <h1 className={pageTitle}>{suffix ? "Создать ролик" : "Ролики"}</h1>
      <p className={pageLead}>
        {projects.length
          ? "Выберите проект."
          : "Создайте проект, чтобы подготовить первый ролик."}
      </p>
      {projects.length ? (
        <div className={projectGrid}>
          {projects.map((p) => (
            <Link className={projectCard} key={p.id} href={href(p.id)}>
              <strong>{p.name}</strong>
              <span className="text-accent">
                {suffix ? "Создать ролик" : "Открыть ролики"} →
              </span>
            </Link>
          ))}
        </div>
      ) : (
        <Link className={secondaryButton} href="/projects">
          Создать проект
        </Link>
      )}
    </VideoShell>
  );
}
