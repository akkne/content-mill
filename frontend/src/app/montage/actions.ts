"use server";
import { projectRequest } from "@/lib/projects";
import { revalidatePath } from "next/cache";

export async function assignStyle(project: string, style: string) {
  const res = await projectRequest(
    `/api/v1/projects/${encodeURIComponent(project)}/motion/styles/${encodeURIComponent(style)}`,
    { method: "PUT" },
  );
  if (res.ok) revalidatePath(`/projects/${project}/knowledge`);
  return res.ok;
}
