import { loadVideos, type VideoOptions } from "@/lib/videos";
import { motionLibrary } from "@/lib/motion";
import { Wizard } from "./wizard";

export default async function NewVideo({
  params,
  searchParams,
}: {
  searchParams: Promise<{ style?: string }>;
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return (
    <Wizard
      projectId={id}
      library={await motionLibrary(id)}
      initialStyle={(await searchParams).style}
      motionOrigin={
        process.env.OPENMOTION_PUBLIC_URL ?? "http://127.0.0.1:4173"
      }
      data={await loadVideos<VideoOptions>(id, "/options")}
    />
  );
}
