import { projectRequest } from "@/lib/projects";

export async function GET(_: Request, { params }: { params: Promise<{ id: string; node: string; version: string }> }) {
  const { id, node, version } = await params;
  if (!/^\d+$/.test(version)) return new Response(null, { status: 404 });
  const result = await projectRequest(`/api/v1/projects/${encodeURIComponent(id)}/nodes/${encodeURIComponent(node)}/download?version=${version}`);
  if (!result.ok) return new Response(null, { status: result.status });
  const { url } = await result.json() as { url: string };
  return new Response(null, { status: 307, headers: { Location: url, "Cache-Control": "private, no-store" } });
}
