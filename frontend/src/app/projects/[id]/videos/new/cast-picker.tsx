"use client";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { useTranslator } from "@/app/interface-language";
import { primaryButton, secondaryButton } from "@/app/ui-styles";
import { listVoices } from "@/app/knowledge/voices/actions";
import type { VideoOptions } from "@/lib/videos";

export type CastRow = {
  key: number;
  character_id: string;
  voice_id: string | null;
};
type Target = { key: number; kind: "avatar" | "voice" };
export function CastPicker({
  data,
  rows,
  change,
}: {
  data: VideoOptions;
  rows: CastRow[];
  change: (rows: CastRow[]) => void;
}) {
  const t = useTranslator();
  const router = useRouter();
  const nextKey = useRef(1);
  const dialog = useRef<HTMLDialogElement>(null);
  const audio = useRef<HTMLAudioElement>(null);
  const previewRequest = useRef(0);
  const [target, setTarget] = useState<Target | null>(null);
  const [selected, select] = useState("");
  const [notice, setNotice] = useState("");
  const isVoice = target?.kind === "voice";
  const choices = isVoice
    ? data.cast_voices
    : data.avatars.filter(
        (a) =>
          !rows.some((r) => r.key !== target?.key && r.character_id === a.id),
      );
  useEffect(() => {
    const modal = dialog.current;
    if (target) modal?.showModal();
    return () => {
      modal?.close();
    };
  }, [target]);
  function stop() {
    previewRequest.current++;
    audio.current?.pause();
    setNotice("");
  }
  function open(row: CastRow, kind: Target["kind"]) {
    stop();
    select(kind === "avatar" ? row.character_id : (row.voice_id ?? ""));
    setTarget({ key: row.key, kind });
  }
  function close() {
    stop();
    setTarget(null);
  }
  async function preview() {
    stop();
    const request = previewRequest.current;
    const voice = data.cast_voices.find((v) => v.id === selected);
    if (!voice) return;
    let url = voice.preview;
    if (!url) {
      const result = await listVoices({
        query: voice.external_id,
        exact: "true",
      });
      if (request !== previewRequest.current) return;
      if (result.error) {
        setNotice(result.error);
        return;
      }
      url = result.data?.items[0]?.preview_url ?? null;
    }
    if (!url) {
      setNotice(
        t(
          "У этого голоса нет примера в каталоге.",
          "This voice has no catalog sample.",
        ),
      );
      return;
    }
    if (audio.current) {
      audio.current.src = url;
      try {
        await audio.current.play();
      } catch {
        if (request === previewRequest.current)
          setNotice(
            t("Не удалось воспроизвести пример.", "Could not play the sample."),
          );
      }
    }
  }
  return (
    <fieldset className="grid gap-3 rounded-xl border border-line p-4">
      <legend className="px-1 font-bold">
        {t("Персонажи и голоса", "Characters and voices")}
      </legend>
      {rows.map((r, i) => (
        <div
          className="grid items-end gap-2 sm:grid-cols-[1fr_1fr_auto]"
          key={r.key}
        >
          <div className="grid gap-1">
            {t("Персонаж", "Character")} {i + 1}
            <button
              type="button"
              className={secondaryButton}
              onClick={() => open(r, "avatar")}
            >
              {data.avatars.find((a) => a.id === r.character_id)?.name ??
                t("Выбрать аватар", "Choose avatar")}
            </button>
          </div>
          <div className="grid gap-1">
            {t("Голос", "Voice")}
            <button
              type="button"
              className={secondaryButton}
              disabled={!r.character_id}
              onClick={() => open(r, "voice")}
            >
              {data.cast_voices.find((v) => v.id === r.voice_id)?.name ??
                t("Без реплик", "No dialogue")}
            </button>
          </div>
          <button
            className={secondaryButton}
            type="button"
            aria-label={
              t("Убрать персонажа", "Remove character") + " " + (i + 1)
            }
            onClick={() => change(rows.filter((row) => row.key !== r.key))}
          >
            ×
          </button>
        </div>
      ))}
      <button
        type="button"
        className={secondaryButton + " w-fit"}
        onClick={() =>
          change([
            ...rows,
            { key: nextKey.current++, character_id: "", voice_id: null },
          ])
        }
      >
        {t("+ Добавить персонажа", "+ Add character")}
      </button>
      <input
        type="hidden"
        name="characters"
        value={JSON.stringify(
          rows.map((r) => ({
            character_id: r.character_id,
            voice_id: r.voice_id,
          })),
        )}
      />
      <dialog
        ref={dialog}
        aria-label={
          isVoice
            ? t("Выбрать голос", "Choose voice")
            : t("Выбрать аватар", "Choose avatar")
        }
        onCancel={close}
        className="m-auto w-[min(92vw,620px)] rounded-2xl border border-line bg-surface p-0 text-ink shadow-panel backdrop:bg-black/40"
      >
        <h2 className="border-b border-line p-4 text-lg font-bold">
          {isVoice
            ? t("Голоса проекта", "Project voices")
            : t("Аватары проекта", "Project avatars")}
        </h2>
        <div className="grid max-h-72 min-h-36 content-start overflow-auto p-2">
          {(isVoice
            ? [{ id: "", name: t("Без реплик", "No dialogue") }, ...choices]
            : choices
          ).map((item) => (
            <button
              type="button"
              key={item.id}
              aria-pressed={selected === item.id}
              className="rounded-lg px-4 py-2 text-left hover:bg-tint aria-pressed:bg-selected aria-pressed:text-selected-ink"
              onClick={() => {
                stop();
                select(item.id);
              }}
            >
              {item.name}
            </button>
          ))}
          {!isVoice && <div className="flex flex-wrap items-center gap-4 px-3 py-2">
            <a href="/knowledge/avatars" target="_blank" rel="noopener" className="font-bold text-accent underline">
              {t("Создать аватар в библиотеке ↗", "Create an avatar in the library ↗")}
            </a>
            <button type="button" className={secondaryButton} onClick={() => router.refresh()}>
              {t("Обновить список проекта", "Refresh project list")}
            </button>
          </div>}
          {!choices.length && (
            <p className="p-3 text-muted">
              {t(
                "Добавьте материалы из личной библиотеки в проект.",
                "Add items from your personal library to this project.",
              )}
            </p>
          )}
        </div>
        <audio ref={audio} />
        <p role="status" className="px-4">
          {notice}
        </p>
        <div className="flex flex-wrap justify-end gap-2 border-t border-line p-3">
          {isVoice && selected && (
            <button
              type="button"
              className={secondaryButton + " mr-auto"}
              onClick={preview}
            >
              {t("Предпросмотр", "Preview")}
            </button>
          )}
          <button type="button" className={secondaryButton} onClick={close}>
            {t("Отмена", "Cancel")}
          </button>
          <button
            type="button"
            className={primaryButton}
            disabled={!isVoice && !selected}
            onClick={() => {
              change(
                rows.map((r) =>
                  r.key !== target?.key
                    ? r
                    : isVoice
                      ? { ...r, voice_id: selected || null }
                      : {
                          ...r,
                          character_id: selected,
                          voice_id:
                            data.avatars.find((a) => a.id === selected)
                              ?.default_voice_id ?? null,
                        },
                ),
              );
              close();
            }}
          >
            {t("Выбрать", "Select")}
          </button>
        </div>
      </dialog>
    </fieldset>
  );
}
