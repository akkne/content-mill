import { optionLabel } from "../video-labels";
import { getTranslator } from "@/lib/server-language";
import Link from "next/link";
import { loadVideos, type ProjectVideo } from "@/lib/videos";
import { loadProject } from "@/lib/projects";
import { pageLead, pageTitle, secondaryButton } from "@/app/ui-styles";
import { VideoEditor } from "./video-editor";

export default async function VideoPage({
  params,
}: {
  params: Promise<{ id: string; video: string }>;
}) {
  const t = await getTranslator();
  const { id, video } = await params;
  const [item, project] = await Promise.all([
    loadVideos<ProjectVideo>(id, "/" + encodeURIComponent(video)),
    loadProject(id),
  ]);
  return (
    <>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className={pageTitle}>{item.title}</h1>
        <Link className={secondaryButton} href={`/projects/${id}/videos`}>
          {t("← Все ролики", "← All videos")}
        </Link>
      </div>
      <p className={pageLead}>
        {project.name} · {optionLabel(item.settings.method, t)} · {item.settings.duration} {t("сек ·", "sec ·")}{" "}
        {optionLabel(item.settings.platform, t)} · {item.motion_title ? t(item.motion_title.ru,item.motion_title.en) : optionLabel(item.settings.editing_style ?? "По сценарию", t)}
      </p>
      {item.settings.production?.motion_export && (
        <a className={secondaryButton+" mb-4"} target="_blank" rel="noreferrer"
          href={`${process.env.OPENMOTION_PUBLIC_URL ?? "http://127.0.0.1:4173"}/#project/${encodeURIComponent(item.settings.production.motion_export.project)}`}>
          {t("Открыть монтаж в Studio","Open edit in Studio")} ↗
        </a>
      )}
      <VideoEditor item={item} project={project.name} projectId={id} />
    </>
  );
}
