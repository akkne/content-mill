import { loadVideos, type VideoOptions } from "@/lib/videos";
import { motionLibrary } from "@/lib/motion";
import { Wizard } from "./wizard";

export default async function NewVideo({
  params,
  searchParams,
}: {
  searchParams: Promise<{ style?: string; reel?: string }>;
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return (
    <Wizard
      projectId={id}
      library={await motionLibrary(id)}
      initialReel={(await searchParams).reel}
      initialStyle={(await searchParams).style}
      data={await loadVideos<VideoOptions>(id, "/options")}
    />
  );
}
