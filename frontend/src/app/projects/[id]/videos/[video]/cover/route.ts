import { videoRequest } from "@/lib/videos";

export async function GET(
  _: Request,
  { params }: { params: Promise<{ id: string; video: string }> },
) {
  const { id, video } = await params;
  const response = await videoRequest(
    id,
    "/" + encodeURIComponent(video) + "/cover",
  );
  if (!response.ok) return new Response(null, { status: response.status });
  return new Response(response.body, {
    headers: {
      "Content-Type": "image/svg+xml",
      "Content-Disposition": 'attachment; filename="cover.svg"',
      "Cache-Control": "private, no-store",
    },
  });
}
