"use client";
import { useTranslator, useInterfaceLanguage } from "@/app/interface-language";

import Link from "next/link";
import { useEffect, useRef, useState, useTransition } from "react";
import { primaryButton, secondaryButton } from "@/app/ui-styles";
import {
  addToOpenProject,
  listSaved,
  type SavedVoice,
} from "@/app/knowledge/voices/actions";
import { genderName, languagesOf } from "@/app/knowledge/voices/labels";
import type { KnowledgeNode } from "@/lib/knowledge";

export function VoicePicker({
  project,
  onClose,
  onSave,
}: {
  project: string;
  onClose: () => void;
  onSave: (node: KnowledgeNode, items: KnowledgeNode[]) => void;
}) {
  const locale = useInterfaceLanguage();
  const t = useTranslator();
  const dialog = useRef<HTMLDialogElement>(null);
  const [items, setItems] = useState<SavedVoice[]>();
  const [error, setError] = useState("");
  const [saving, start] = useTransition();
  useEffect(() => {
    const el = dialog.current;
    el?.showModal();
    let active = true;
    listSaved().then((result) => {
      if (active) {
        setItems(result.data);
        setError(result.error ?? "");
      }
    });
    return () => {
      active = false;
      el?.close();
    };
  }, []);
  function add(id: string) {
    start(async () => {
      const result = await addToOpenProject(id, project);
      if (result.items && result.node) onSave(result.node, result.items);
      else setError(result.error ?? t("Не удалось добавить голос", "Could not add voice"));
    });
  }
  return (
    <dialog
      ref={dialog}
      aria-labelledby="select-voice-title"
      onCancel={(event) => {
        event.preventDefault();
        if (!saving) onClose();
      }}
      className="m-auto h-[88dvh] max-h-[94dvh] w-[min(1120px,96vw)] max-w-[96vw] overflow-auto rounded-3xl border border-line bg-surface p-5 text-ink shadow-xl backdrop:bg-black/60 sm:p-8"
    >
      <header className="mb-6 flex flex-wrap items-center gap-3">
        <h2 id="select-voice-title" className="mr-auto text-2xl font-semibold">
          {t("Голоса из библиотеки", "Library voices")}
        </h2>
        <Link className={primaryButton} href="/knowledge/voices?create=1">
          {t("Создать новый голос", "Create new voice")}
        </Link>
        <button
          className={secondaryButton}
          disabled={saving}
          onClick={onClose}
          aria-label={t("Закрыть", "Close")}
        >
          ×
        </button>
      </header>
      {error && <p role="alert">{error}</p>}
      {!items && !error && <p role="status">{t("Загружаем голоса…", "Loading voices…")}</p>}
      {items && (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm [&_td]:border-t [&_td]:border-line [&_td]:p-3 [&_th]:p-3">
            <thead className="bg-tint text-muted">
              <tr>
                {[t("Название", "Name"), t("Описание", "Description"), t("Язык", "Language"), t("Пол", "Gender"), ""].map((h) => (
                  <th key={h}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {items.map((v) => (
                <tr key={v.id}>
                  <td className="font-bold">{v.name}</td>
                  <td>{v.description || "—"}</td>
                  <td>{languagesOf(v, locale)}</td>
                  <td>{genderName(v.voice_gender, locale)}</td>
                  <td>
                    <button
                      className={secondaryButton}
                      onClick={() => add(v.id)}
                      disabled={saving || v.project_ids.includes(project)}
                    >
                      {v.project_ids.includes(project)
                        ? t("Добавлен", "Added")
                        : t("Добавить", "Add")}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!items.length && (
            <p className="py-8 text-center text-muted">
              {t("В библиотеке пока нет голосов.", "Your voice library is empty.")}
            </p>
          )}
        </div>
      )}
    </dialog>
  );
}
