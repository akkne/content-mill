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
          ← Все ролики
        </Link>
      </div>
      <p className={pageLead}>
        {project.name} · {item.settings.method} · {item.settings.duration} сек ·{" "}
        {item.settings.platform}
      </p>
      <VideoEditor item={item} project={project.name} projectId={id} />
    </>
  );
}
