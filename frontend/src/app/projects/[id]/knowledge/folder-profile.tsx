"use client";
import { useTranslator, useInterfaceLanguage } from "@/app/interface-language";

import { assignVoice, type SavedVoice } from "@/app/knowledge/voices/actions";
import Link from "next/link";
import { genderName, languagesOf } from "@/app/knowledge/voices/labels";
import { useState, useTransition } from "react";
import { field, fieldLabel, secondaryButton } from "@/app/ui-styles";
import type { KnowledgeNode } from "@/lib/knowledge";
import { saveProfile } from "./media-actions";

export function FolderProfile({ project, folder, voices, libraryVoices, onVoiceAssigned, onSave }: {
  project: string;
  folder: KnowledgeNode;
  voices: KnowledgeNode[];
  libraryVoices?: SavedVoice[];
  onVoiceAssigned: (node: KnowledgeNode) => void;
  onSave: (node: KnowledgeNode) => void;
}) {
  const locale = useInterfaceLanguage();
  const t = useTranslator();
  const [pending, start] = useTransition();
  const [message, setMessage] = useState("");
  if (folder.folder_role === "voice") return <section className="mb-5 grid gap-3">
    {folder.description && <p>{folder.description}</p>}
    <p className="text-muted">{languagesOf(folder, locale)} · {genderName(folder.voice_gender, locale)}</p>
    {folder.voice_preview_url && <audio aria-label={t("Пример голоса", "Voice sample")} controls preload="none" src={folder.voice_preview_url}/>}
    <Link className="w-fit text-accent" href="/knowledge/voices">{t("Открыть библиотеку голосов →", "Open voice library →")}</Link>
  </section>;
  return (
    <form className="mb-5 grid max-w-xl gap-3" onSubmit={event => {
      event.preventDefault();
      const data = new FormData(event.currentTarget);
      const value = (key: string) => String(data.get(key) ?? "").trim();
      const profile = { linked_voice_id: value("linkedVoice") || null };
      setMessage("");
      start(async () => {
        if(libraryVoices && profile.linked_voice_id){
          const assigned=await assignVoice(profile.linked_voice_id,[project],[]);
          if(!assigned.data?.[0]){setMessage(assigned.error??t("Не удалось назначить голос.","Could not assign voice."));return;}
          onVoiceAssigned(assigned.data[0]);
          profile.linked_voice_id=assigned.data[0].id;
        }
        const result = await saveProfile(project, folder.id, folder.revision, profile);
        if (result.data) onSave(result.data);
        setMessage(result.error ?? t("Сохранено", "Saved"));
      });
    }}>
      <label className={fieldLabel}>{t("Голос аватара", "Avatar voice")}
        <select className={field} name="linkedVoice" defaultValue={libraryVoices?(voices.find(v=>v.id===folder.linked_voice_id)?.library_voice_id??""):(folder.linked_voice_id ?? "")}>
          <option value="">{t("Без привязки", "Unassigned")}</option>
          {(libraryVoices??voices).map(node => <option key={node.id} value={node.id}>{node.name}</option>)}
        </select>
      </label>
      <button className={secondaryButton} disabled={pending}>{t("Сохранить привязку", "Save assignment")}</button>
      <span role="status">{message}</span>
    </form>
  );
}
