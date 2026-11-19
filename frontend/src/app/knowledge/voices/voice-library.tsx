"use client";

import Link from "next/link";
import { useState, useTransition } from "react";
import type { Project } from "@/lib/projects";
import { field, primaryButton, secondaryButton } from "@/app/ui-styles";
import { assignVoice, type SavedVoice } from "./actions";
import { genderName, languagesOf } from "./labels";
import { VoiceCreator } from "./voice-creator";
import { VoiceEditor } from "./voice-editor";

function ProjectChecklist({
  voice,
  projects,
  onSave,
  onCancel,
}: {
  voice: SavedVoice;
  projects: Project[];
  onSave: (ids: string[]) => void;
  onCancel: () => void;
}) {
  const [checked, setChecked] = useState(voice.project_ids);
  const [pending, start] = useTransition();
  const [error, setError] = useState("");
  function toggle(id: string) {
    setChecked((current) =>
      current.includes(id) ? current.filter((p) => p !== id) : [...current, id],
    );
  }
  function save() {
    start(async () => {
      const result = await assignVoice(
        voice.id,
        checked.filter((id) => !voice.project_ids.includes(id)),
        voice.project_ids.filter((id) => !checked.includes(id)),
      );
      if (result.data) onSave(checked);
      else setError(result.error);
    });
  }
  return (
    <fieldset
      disabled={pending}
      className="mt-4 rounded-xl border border-line bg-control p-4"
    >
      <legend className="px-1 font-semibold">Проекты для «{voice.name}»</legend>
      <div className="grid max-h-56 gap-2 overflow-y-auto sm:grid-cols-2">
        {projects.map((p) => (
          <label className="flex cursor-pointer items-center gap-2" key={p.id}>
            <input
              type="checkbox"
              className="size-4 accent-action"
              checked={checked.includes(p.id)}
              onChange={() => toggle(p.id)}
            />
            {p.name}
          </label>
        ))}
        {!projects.length && (
          <Link href="/projects" className="text-accent">
            Создать первый проект →
          </Link>
        )}
      </div>
      {error && <p role="alert">{error}</p>}
      <div className="mt-4 flex flex-wrap gap-2">
        <button
          className={primaryButton}
          disabled={!projects.length}
          onClick={save}
        >
          {pending ? "Сохраняем…" : "Сохранить изменения"}
        </button>
        <button className={secondaryButton} onClick={onCancel}>
          Отмена
        </button>
      </div>
    </fieldset>
  );
}

export function VoiceLibrary({
  initial,
  projects,
  creating,
}: {
  initial: SavedVoice[];
  projects: Project[];
  creating: boolean;
}) {
  const [voices, setVoices] = useState(initial);
  const [create, setCreate] = useState(creating);
  const [query, setQuery] = useState("");
  const [assigning, setAssigning] = useState("");
  const [editing, setEditing] = useState("");
  const [playing, setPlaying] = useState("");
  const [notice, setNotice] = useState("");
  const visible = voices.filter((v) =>
    [v.name, v.description, v.elevenlabs_voice_id, languagesOf(v)].some((s) =>
      s?.toLocaleLowerCase().includes(query.trim().toLocaleLowerCase()),
    ),
  );
  return (
    <>
      <div className="mb-6 flex flex-wrap gap-2 border-b border-line pb-4">
        <button
          aria-pressed={!create}
          className={create ? secondaryButton : primaryButton}
          onClick={() => {
            setCreate(false);
            setNotice("");
          }}
        >
          Мои голоса · {voices.length}
        </button>
        <button
          aria-pressed={create}
          className={create ? primaryButton : secondaryButton}
          onClick={() => {
            setCreate(true);
            setNotice("");
          }}
        >
          Создать новый голос
        </button>
      </div>
      {notice && (
        <p role="status" className="mb-3 text-accent">
          {notice}
        </p>
      )}
      {create ? (
        <VoiceCreator
          initialMode="catalog"
          onSave={(v) => {
            setVoices([v, ...voices]);
            setCreate(false);
            setQuery("");
            setNotice(`«${v.name}» добавлен в библиотеку`);
          }}
        />
      ) : (
        <section
          aria-label="Мои голоса"
          className="rounded-3xl border border-line bg-surface p-5 shadow-panel sm:p-7"
        >
          <input
            aria-label="Поиск по библиотеке"
            className={`${field} mb-5 max-w-lg`}
            type="search"
            placeholder="Поиск по библиотеке"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          {!visible.length && (
            <p className="py-8 text-muted">
              {voices.length
                ? "Голоса не найдены."
                : "Здесь появятся ваши сохранённые голоса."}
            </p>
          )}
          <ul className="divide-y divide-line">
            {visible.map((v) => (
              <li key={v.id} className="py-4">
                <div className="flex flex-wrap items-center gap-4">
                  <span
                    aria-hidden
                    className="grid size-12 shrink-0 place-items-center rounded-2xl bg-tint text-xl font-semibold text-accent"
                  >
                    {v.name.slice(0, 1)}
                  </span>
                  <div className="min-w-40 flex-1">
                    <h2 className="text-lg font-semibold">{v.name}</h2>
                    {v.description && (
                      <p className="mt-1 text-sm">{v.description}</p>
                    )}
                    <p className="mt-1 text-sm text-muted">
                      {languagesOf(v)} · {genderName(v.voice_gender)} ·
                      Проектов: {v.project_ids.length}
                    </p>
                  </div>
                  {v.voice_preview_url && (
                    <button
                      className={secondaryButton}
                      onClick={() => setPlaying(playing === v.id ? "" : v.id)}
                    >
                      {playing === v.id ? "Закрыть пример" : "Послушать"}
                    </button>
                  )}
                  <button
                    className={secondaryButton}
                    onClick={() => {
                      setEditing(editing === v.id ? "" : v.id);
                      setAssigning("");
                    }}
                  >
                    Изменить
                  </button>
                  <button
                    className={primaryButton}
                    aria-expanded={assigning === v.id}
                    onClick={() => {
                      setAssigning(assigning === v.id ? "" : v.id);
                      setEditing("");
                    }}
                  >
                    Добавить в проект
                  </button>
                </div>
                {playing === v.id && v.voice_preview_url && (
                  <audio
                    autoPlay
                    controls
                    src={v.voice_preview_url}
                    className="mt-3 max-w-full"
                  />
                )}
                {editing === v.id && (
                  <VoiceEditor
                    voice={v}
                    onCancel={() => setEditing("")}
                    onSave={(updated) => {
                      setVoices((all) =>
                        all.map((item) => (item.id === v.id ? updated : item)),
                      );
                      setEditing("");
                    }}
                  />
                )}
                {assigning === v.id && (
                  <ProjectChecklist
                    voice={v}
                    projects={projects}
                    onCancel={() => setAssigning("")}
                    onSave={(ids) => {
                      setVoices((all) =>
                        all.map((item) =>
                          item.id === v.id
                            ? { ...item, project_ids: ids }
                            : item,
                        ),
                      );
                      setAssigning("");
                      setNotice("Список проектов сохранён");
                    }}
                  />
                )}
              </li>
            ))}
          </ul>
        </section>
      )}
    </>
  );
}
