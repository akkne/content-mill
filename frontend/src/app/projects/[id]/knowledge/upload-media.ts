import type { KnowledgeNode } from "@/lib/knowledge";
import { beginUpload, finishUpload } from "./media-actions";

export const mediaFormats = { png: "image/png", jpg: "image/jpeg", jpeg: "image/jpeg", webp: "image/webp", mp3: "audio/mpeg", wav: "audio/wav", m4a: "audio/mp4", mp4: "video/mp4", webm: "video/webm", pdf: "application/pdf" };
export const acceptedMedia = Object.keys(mediaFormats).map(ext => "." + ext).join(",");

export async function uploadMedia(project: string, parent: string | null, file: File, target?: KnowledgeNode) {
  const ext = file.name.toLowerCase().split(".").pop() as keyof typeof mediaFormats;
  const mime = mediaFormats[ext];
  if (!mime) throw new Error("Выберите изображение, видео, аудио или PDF поддерживаемого формата.");
  if (!file.size || file.size > 64 * 1024 * 1024) throw new Error("Размер файла должен быть от 1 байта до 64 МиБ.");
  const hash = await crypto.subtle.digest("SHA-256", await file.arrayBuffer());
  const sha256 = Array.from(new Uint8Array(hash), byte => byte.toString(16).padStart(2, "0")).join("");
  const start = await beginUpload(project, { parent_id: parent, node_id: target?.id, name: file.name, mime_type: mime, size_bytes: file.size, sha256 }, target?.revision);
  if (!start.data) throw new Error(start.error);
  const sent = await fetch(start.data.upload_url, { method: "PUT", body: file, headers: { "Content-Type": mime }, credentials: "omit" });
  if (!sent.ok) throw new Error("Не удалось передать файл в хранилище.");
  const end = await finishUpload(project, start.data.upload_id);
  if (!end.data) throw new Error(end.error);
  return end.data.node;
}
