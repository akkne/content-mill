"use client";

import { useState, useTransition } from "react";
import { field, fieldLabel, secondaryButton } from "@/app/ui-styles";
import type { KnowledgeNode } from "@/lib/knowledge";
import { saveProfile } from "./media-actions";

export function FolderProfile({ project, folder, voices, onSave }: {
  project: string;
  folder: KnowledgeNode;
  voices: KnowledgeNode[];
  onSave: (node: KnowledgeNode) => void;
}) {
  const [pending, start] = useTransition();
  const [message, setMessage] = useState("");
  const voice = folder.folder_role === "voice";
  return (
    <form className="mb-5 grid max-w-xl gap-3" onSubmit={event => {
      event.preventDefault();
      const data = new FormData(event.currentTarget);
      const value = (key: string) => String(data.get(key) ?? "").trim();
      const profile = voice
        ? { voice_gender: value("gender") || null, description: value("description"), voice_language: value("language"), voice_model: value("model"), elevenlabs_voice_id: value("voiceId") || null }
        : { linked_voice_id: value("linkedVoice") || null };
      setMessage("");
      start(async () => {
        const result = await saveProfile(project, folder.id, folder.revision, profile);
        if (result.data) onSave(result.data);
        setMessage(result.error ?? "Сохранено");
      });
    }}>
      {voice ? <>
        <label className={fieldLabel}>Описание голоса
          <textarea className={field} name="description" maxLength={4000} defaultValue={folder.description ?? ""} />
        </label>
        {folder.voice_preview_url && <audio aria-label="Пример ElevenLabs" controls preload="none" src={folder.voice_preview_url} />}
        {!!folder.catalog_languages?.length && <p>Языки ElevenLabs · {folder.catalog_languages.join(", ")}</p>}
        <label className={fieldLabel}>Пол голоса
          <select className={field} name="gender" defaultValue={folder.voice_gender ?? ""}>
            <option value="">Не указан</option><option value="male">Мужской</option><option value="female">Женский</option>
          </select>
        </label>
        <label className={fieldLabel}>Язык
          <input className={field} name="language" maxLength={80} defaultValue={folder.voice_language ?? ""} />
        </label>
        <label className={fieldLabel}>Модель ElevenLabs
          <input className={field} name="model" maxLength={160} defaultValue={folder.voice_model ?? ""} />
        </label>
        <label className={fieldLabel}>ID голоса в ElevenLabs
          <input className={field} name="voiceId" maxLength={160} defaultValue={folder.elevenlabs_voice_id ?? ""} />
        </label>
      </> : <label className={fieldLabel}>Голос аватара
        <select className={field} name="linkedVoice" defaultValue={folder.linked_voice_id ?? ""}>
          <option value="">Без привязки</option>
          {voices.map(node => <option key={node.id} value={node.id}>{node.name}</option>)}
        </select>
      </label>}
      <button className={secondaryButton} disabled={pending}>{voice ? "Сохранить карточку" : "Сохранить привязку"}</button>
      <span role="status">{message}</span>
    </form>
  );
}
