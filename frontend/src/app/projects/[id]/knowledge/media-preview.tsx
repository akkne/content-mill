"use client";

import { eyebrow, kbDocumentFoot, kbDocumentHead, kbEmpty, secondaryButton } from "@/app/ui-styles";
import { useEffect, useRef, useState, useTransition } from "react";
import type { KnowledgeNode } from "@/lib/knowledge";
import { mediaPreview, updateVoice } from "./media-actions";
import { acceptedMedia, uploadMedia } from "./upload-media";

export function MediaPreview({ project, node, voiceSample, path, onChange, onClose }: {
  voiceSample: boolean; project: string; node: KnowledgeNode; path: string; onChange: (node: KnowledgeNode) => void; onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [number, setNumber] = useState<number>();
  const [preview, setPreview] = useState<Awaited<ReturnType<typeof mediaPreview>>["data"]>();
  const [error, setError] = useState("");
  const [pending, start] = useTransition();
  const [attempt, setAttempt] = useState(0);
  useEffect(() => { const el = dialog.current; el?.showModal(); return () => el?.close(); }, []);
  useEffect(() => {
    let active = true;
    mediaPreview(project, node.id, number).then(result => {
      if (active) { setPreview(result.data); setError(result.error || ""); }
    });
    return () => { active = false; };
  }, [project, node.id, node.revision, number, attempt]);

  return (
    <dialog
      ref={dialog}
      className="m-auto max-h-[85vh] w-[min(780px,calc(100vw-30px))] overflow-auto rounded-2xl border border-line bg-surface text-ink shadow-[0_25px_80px_#0006] backdrop:bg-[rgb(8_15_28/72%)] backdrop:backdrop-blur-[3px]"
      onCancel={onClose}
      aria-labelledby="media-title"
    >
      <header className={kbDocumentHead}>
        <div>
          <span className={eyebrow}>{path}</span>
          <h2 className="mt-1 text-lg" id="media-title">
            {node.name}
          </h2>
        </div>
        <button aria-label="Закрыть" className={`${secondaryButton} text-[22px]`} onClick={onClose}>
          ×
        </button>
      </header>
      {preview ? (
        <>
          <div
            className="grid min-h-[120px] place-items-center"
            onErrorCapture={() => setError("Не удалось открыть файл. Обновите ссылку или скачайте оригинал.")}
          >
            {node.kind === "video" && (
              <video
                className="max-h-[55vh] w-full bg-[#111]"
                key={preview.url}
                src={preview.url}
                controls
                playsInline
                autoPlay
              />
            )}
            {node.kind === "audio" && (
              <audio className="w-[calc(100%-48px)]" key={preview.url} src={preview.url} controls autoPlay />
            )}
            {node.kind === "image" && (
              // eslint-disable-next-line @next/next/no-img-element -- signed original from project storage
              <img className="max-h-[55vh] max-w-full object-contain" src={preview.url} alt={node.name} />
            )}
            {node.kind === "file" && (
              <a href={preview.url} target="_blank" rel="noreferrer">
                Открыть PDF
              </a>
            )}
          </div>
          <div className={kbDocumentFoot}>
            <label>
              Версия{" "}
              <select
                value={preview.version.version}
                onChange={(event) => {
                  setPreview(undefined);
                  setNumber(Number(event.target.value));
                }}
              >
                {preview.versions.map((v) => (
                  <option key={v.id} value={v.version}>
                    {v.version} · {new Date(v.created_at).toLocaleString("ru-RU")}
                  </option>
                ))}
              </select>
            </label>
            <span>
              {preview.version.format} · {Math.ceil(preview.version.size_bytes / 1024)} КиБ
            </span>
            <a href={preview.url} target="_blank" rel="noreferrer">
              Открыть оригинал ↗
            </a>
          </div>
        </>
      ) : (
        !error && <p className={kbEmpty}>Открываем файл…</p>
      )}
      <div className="grid gap-3 px-[22px] py-4 [&_input]:block [&_input]:max-w-full">
        <label>
          Загрузить новую версию{" "}
          <input
            type="file"
            accept={acceptedMedia}
            disabled={pending}
            onChange={(event) => {
              const file = event.target.files?.[0];
              event.target.value = "";
              if (!file) return;
              start(async () => {
                try {
                  const updated = await uploadMedia(project, node.parent_id, file, node);
                  setNumber(undefined);
                  onChange(updated);
                } catch (e) {
                  setError(e instanceof Error ? e.message : "Ошибка загрузки");
                }
              });
            }}
          />
        </label>
        {pending && <span role="status">Сохраняем…</span>}
        {node.kind === "audio" && !voiceSample && (
          <details>
            <summary>Параметры голоса{node.voice_language && ` · ${node.voice_language}`}</summary>
            <form
              className="grid gap-3 px-[22px] py-4"
              onSubmit={(event) => {
                event.preventDefault();
                const data = new FormData(event.currentTarget);
                start(async () => {
                  const result = await updateVoice(
                    project,
                    node.id,
                    node.revision,
                    String(data.get("name")),
                    String(data.get("language")),
                    String(data.get("model")),
                  );
                  if (result.data) onChange(result.data);
                  else setError(result.error);
                });
              }}
            >
              <label>
                Имя голоса
                <input name="name" required maxLength={160} defaultValue={node.name} />
              </label>
              <label>
                Язык
                <input name="language" required maxLength={80} defaultValue={node.voice_language || ""} />
              </label>
              <label>
                Модель ElevenLabs (необязательно)
                <input name="model" maxLength={160} defaultValue={node.voice_model || ""} />
              </label>
              <button className={secondaryButton} disabled={pending}>
                Сохранить голос
              </button>
            </form>
          </details>
        )}
        {error && (
          <div role="alert">
            {error} <button onClick={() => setAttempt(attempt + 1)}>Обновить ссылку</button>
          </div>
        )}
      </div>
    </dialog>
  );
}
