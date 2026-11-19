"use client";

import { useState, useTransition } from "react";
import {
  field,
  fieldLabel,
  primaryButton,
  secondaryButton,
} from "@/app/ui-styles";
import { editVoice, type SavedVoice } from "./actions";

export function VoiceEditor({
  voice,
  onSave,
  onCancel,
}: {
  voice: SavedVoice;
  onSave: (value: SavedVoice) => void;
  onCancel: () => void;
}) {
  const [pending, start] = useTransition();
  const [error, setError] = useState("");
  return (
    <form
      className="mt-4 grid gap-3 rounded-xl border border-line p-4 sm:grid-cols-2"
      onSubmit={(event) => {
        event.preventDefault();
        const data = new FormData(event.currentTarget);
        const val = (key: string) => String(data.get(key) ?? "").trim();
        start(async () => {
          const result = await editVoice(voice.id, {
            description: val("description"),
            voice_language: val("language"),
            voice_model: val("model"),
            voice_gender: val("gender") || null,
            elevenlabs_voice_id: val("id") || null,
          });
          if (result.data) onSave(result.data);
          else setError(result.error);
        });
      }}
    >
      <label className={fieldLabel}>
        Описание
        <textarea
          className={field}
          name="description"
          maxLength={4000}
          defaultValue={voice.description ?? ""}
        />
      </label>
      <label className={fieldLabel}>
        Язык
        <input
          className={field}
          name="language"
          maxLength={80}
          defaultValue={voice.voice_language ?? ""}
        />
      </label>
      <label className={fieldLabel}>
        Пол
        <select
          className={field}
          name="gender"
          defaultValue={voice.voice_gender ?? ""}
        >
          <option value="">Не указан</option>
          <option value="male">Мужской</option>
          <option value="female">Женский</option>
        </select>
      </label>
      <label className={fieldLabel}>
        Модель синтеза
        <input
          className={field}
          name="model"
          maxLength={160}
          defaultValue={voice.voice_model ?? ""}
        />
      </label>
      <label className={fieldLabel}>
        ID ElevenLabs
        <input
          className={field}
          name="id"
          maxLength={160}
          defaultValue={voice.elevenlabs_voice_id ?? ""}
        />
      </label>
      <div className="flex items-end gap-2">
        <button className={primaryButton} disabled={pending}>
          Сохранить
        </button>
        <button
          type="button"
          className={secondaryButton}
          disabled={pending}
          onClick={onCancel}
        >
          Отмена
        </button>
      </div>
      {error && <p role="alert">{error}</p>}
    </form>
  );
}
