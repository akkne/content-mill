import { loadVideos, type VideoOptions } from "@/lib/videos";
import { Wizard } from "./wizard";

export default async function NewVideo({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return (
    <Wizard
      projectId={id}
      data={await loadVideos<VideoOptions>(id, "/options")}
    />
  );
}
