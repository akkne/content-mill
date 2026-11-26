"use client";
import { DeliveryFields } from "./delivery-fields";
import { useTranslator } from "@/app/interface-language";

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
  const t = useTranslator();
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
            voice_speed: Number(data.get("voice_speed")),
            voice_style: Number(data.get("voice_style")),
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
        {t("Описание", "Description")}
        <textarea
          className={field}
          name="description"
          maxLength={4000}
          defaultValue={voice.description ?? ""}
        />
      </label>
      <label className={fieldLabel}>
        {t("Язык", "Language")}
        <input
          className={field}
          name="language"
          maxLength={80}
          defaultValue={voice.voice_language ?? ""}
        />
      </label>
      <label className={fieldLabel}>
        {t("Пол", "Gender")}
        <select
          className={field}
          name="gender"
          defaultValue={voice.voice_gender ?? ""}
        >
          <option value="">{t("Не указан", "Unspecified")}</option>
          <option value="male">{t("Мужской", "Male")}</option>
          <option value="female">{t("Женский", "Female")}</option>
        </select>
      </label>
      <label className={fieldLabel}>
        {t("Модель синтеза", "Speech model")}
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
      <DeliveryFields speed={voice.voice_speed} style={voice.voice_style} />
      <div className="flex items-end gap-2">
        <button className={primaryButton} disabled={pending}>
          {t("Сохранить", "Save")}
        </button>
        <button
          type="button"
          className={secondaryButton}
          disabled={pending}
          onClick={onCancel}
        >
          {t("Отмена", "Cancel")}
        </button>
      </div>
      {error && <p role="alert">{error}</p>}
    </form>
  );
}
