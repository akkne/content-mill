import { getTranslator } from "@/lib/server-language";
import Link from "next/link";
import { notFound } from "next/navigation";
import { backLink, content, pageTitle } from "@/app/ui-styles";
import { loadProject } from "@/lib/projects";
import { AgentAccess } from "../agent-access";

export default async function Integrations({ params }: { params: Promise<{ id: string }> }) {
  const t = await getTranslator();
  const { id } = await params;
  const project = await loadProject(id).catch(() => null);
  if (!project) notFound();
  return <main className={content}>
    <Link className={backLink} href={`/projects/${id}`}>← {project.name}</Link>
    <h1 className={pageTitle}>{t("Внешние интеграции", "External integrations")}</h1>
    <AgentAccess projectId={id} />
  </main>;
}
