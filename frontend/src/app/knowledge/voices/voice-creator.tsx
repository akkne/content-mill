"use client";

import { useEffect, useState, useTransition } from "react";
import {
  field,
  fieldLabel,
  formError,
  primaryButton,
  secondaryButton,
} from "@/app/ui-styles";
import { genderName, languageName } from "./labels";
import {
  addVoice,
  listVoices,
  type CatalogVoice,
  type VoicePage,
  type SavedVoice,
} from "./actions";

const languages = [
  "ru",
  "en",
  "de",
  "es",
  "fr",
  "it",
  "pt",
  "uk",
  "pl",
  "zh",
  "ja",
  "ko",
  "ar",
  "hi",
  "tr",
];
export function VoiceCreator({
  onSave,
  initialMode,
}: {
  onSave: (voice: SavedVoice) => void;
  initialMode: "catalog" | "manual";
}) {
  const [mode, setMode] = useState(initialMode);
  const [description, setDescription] = useState("");
  const [manualLanguage, setManualLanguage] = useState("");
  const [model, setModel] = useState("");
  const [query, setQuery] = useState("");
  const [exact, setExact] = useState(false);
  const [language, setLanguage] = useState("");
  const [gender, setGender] = useState("");
  const [cursors, setCursors] = useState([""]);
  const [attempt, setAttempt] = useState(0);
  const [result, setResult] = useState<{
    key: string;
    data?: VoicePage;
    error?: string;
  }>();
  const [selected, setSelected] = useState<CatalogVoice>();
  const [name, setName] = useState("");
  const [manualId, setManualId] = useState("");
  const [manualGender, setManualGender] = useState("");
  const [playing, setPlaying] = useState("");
  const [error, setError] = useState("");
  const [saving, startSave] = useTransition();
  const cursor = cursors[cursors.length - 1];
  const filters = new URLSearchParams({
    query: query.trim(),
    exact: String(exact),
    language,
    cursor,
  });
  if (gender) filters.set("gender", gender);
  const params = filters.toString();
  const key = JSON.stringify([params, attempt]);
  const current = result?.key === key ? result : undefined;

  useEffect(() => {
    if (mode !== "catalog" || (exact && !query.trim())) return;
    let active = true;
    const timer = window.setTimeout(async () => {
      const response = await listVoices(
        Object.fromEntries(new URLSearchParams(params)),
      );
      if (active) setResult({ key, ...response });
    }, 250);
    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [mode, params, key, exact, query]);

  function resetPage() {
    setCursors([""]);
    setSelected(undefined);
    setPlaying("");
    setError("");
  }
  function save() {
    const fromCatalog = mode === "catalog";
    const id = fromCatalog ? selected?.id : manualId.trim();
    if (!id || !name.trim() || saving) return;
    setError("");
    startSave(async () => {
      const reply = await addVoice({
        description,
        language: manualLanguage,
        model: model || null,
        name: name.trim(),
        voice_id: id,
        from_catalog: fromCatalog,
        gender: fromCatalog ? null : manualGender || null,
      });
      if (reply.data) onSave(reply.data);
      else setError(reply.error);
    });
  }

  return (
    <section
      aria-label="Создание голоса"
      className="rounded-3xl border border-line bg-surface p-5 shadow-panel sm:p-7"
    >
      <fieldset disabled={saving}>
        <div className="mb-5 flex flex-wrap gap-2">
          {(["catalog", "manual"] as const).map((value) => (
            <button
              key={value}
              aria-pressed={mode === value}
              className={mode === value ? primaryButton : secondaryButton}
              onClick={() => {
                setMode(value);
                resetPage();
                setName("");
              }}
            >
              {value === "catalog"
                ? "Каталог ElevenLabs"
                : "Вставить ID вручную"}
            </button>
          ))}
        </div>
        {mode === "catalog" && (
          <>
            <div className="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <label className={fieldLabel}>
                Искать по
                <select
                  className={field}
                  value={exact ? "id" : "name"}
                  onChange={(e) => {
                    setExact(e.target.value === "id");
                    resetPage();
                  }}
                >
                  <option value="name">Названию</option>
                  <option value="id">Точному ID</option>
                </select>
              </label>
              <label className={fieldLabel}>
                {exact ? "ID ElevenLabs" : "Название голоса"}
                <input
                  className={field}
                  value={query}
                  maxLength={160}
                  onChange={(e) => {
                    setQuery(e.target.value);
                    resetPage();
                  }}
                />
              </label>
              <label className={fieldLabel}>
                Язык
                <input
                  className={field}
                  list="voice-languages"
                  placeholder="Все языки"
                  value={language}
                  maxLength={80}
                  onChange={(e) => {
                    setLanguage(e.target.value);
                    resetPage();
                  }}
                />
                <datalist id="voice-languages">
                  {languages.map((code) => (
                    <option key={code} value={code}>
                      {languageName(code)}
                    </option>
                  ))}
                </datalist>
              </label>
              <label className={fieldLabel}>
                Пол голоса
                <select
                  className={field}
                  value={gender}
                  onChange={(e) => {
                    setGender(e.target.value);
                    resetPage();
                  }}
                >
                  <option value="">Любой</option>
                  <option value="male">Мужской</option>
                  <option value="female">Женский</option>
                </select>
              </label>
            </div>
            {exact && !query.trim() ? (
              <p>Введите ID голоса.</p>
            ) : !current ? (
              <p role="status">Загружаем голоса…</p>
            ) : current.error ? (
              <div role="alert">
                {current.error}{" "}
                <button
                  className={secondaryButton}
                  onClick={() => setAttempt(attempt + 1)}
                >
                  Повторить
                </button>
              </div>
            ) : (
              <div className="grid gap-3 sm:grid-cols-2">
                {!current.data?.items.length && <p>Голоса не найдены.</p>}
                {current.data?.items.map((voice) => (
                  <article
                    key={voice.id}
                    className="grid content-start gap-2 rounded-xl border border-line p-4"
                  >
                    <h3 className="font-semibold">{voice.name}</h3>
                    <small className="break-all text-muted">{voice.id}</small>
                    <p>{voice.description || "Описание не указано"}</p>
                    <p className="text-sm">
                      {genderName(voice.gender)} ·{" "}
                      {voice.languages.map(languageName).join(", ") ||
                        "Языки не указаны"}
                    </p>
                    <div className="flex flex-wrap items-center gap-2">
                      <button
                        className={secondaryButton}
                        onClick={() => {
                          setSelected(voice);
                          setName(voice.name.slice(0, 160));
                          setError("");
                        }}
                      >
                        {selected?.id === voice.id ? "Выбран" : "Выбрать"}
                      </button>
                      {voice.preview_url ? (
                        playing === voice.id ? (
                          <audio
                            controls
                            autoPlay
                            className="max-w-full"
                            src={voice.preview_url}
                            aria-label={`Пример · ${voice.name}`}
                          />
                        ) : (
                          <button
                            className={secondaryButton}
                            onClick={() => setPlaying(voice.id)}
                          >
                            Послушать
                          </button>
                        )
                      ) : (
                        <small>Пример недоступен</small>
                      )}
                    </div>
                  </article>
                ))}
              </div>
            )}
            <nav
              aria-label="Страницы каталога"
              className="my-4 flex items-center gap-3"
            >
              <button
                className={secondaryButton}
                disabled={cursors.length === 1}
                onClick={() => {
                  setCursors(cursors.slice(0, -1));
                  setPlaying("");
                }}
              >
                Назад
              </button>
              <span>Страница {cursors.length}</span>
              <button
                className={secondaryButton}
                disabled={!current?.data?.next_cursor}
                onClick={() => {
                  if (current?.data?.next_cursor)
                    setCursors([...cursors, current.data.next_cursor]);
                  setPlaying("");
                }}
              >
                Далее
              </button>
            </nav>
          </>
        )}
        {(mode === "manual" || selected) && (
          <form
            className="sticky bottom-0 mt-5 grid gap-3 border-t border-line bg-surface py-3 sm:grid-cols-2"
            onSubmit={(event) => {
              event.preventDefault();
              save();
            }}
          >
            {mode === "manual" && (
              <>
                <label className={fieldLabel}>
                  Описание
                  <input
                    className={field}
                    value={description}
                    maxLength={4000}
                    onChange={(e) => setDescription(e.target.value)}
                  />
                </label>
                <label className={fieldLabel}>
                  Язык
                  <input
                    className={field}
                    value={manualLanguage}
                    maxLength={80}
                    onChange={(e) => setManualLanguage(e.target.value)}
                  />
                </label>
                <label className={fieldLabel}>
                  Модель синтеза
                  <input
                    className={field}
                    value={model}
                    maxLength={160}
                    onChange={(e) => setModel(e.target.value)}
                  />
                </label>
                <label className={fieldLabel}>
                  ID голоса ElevenLabs
                  <input
                    className={field}
                    value={manualId}
                    required
                    maxLength={160}
                    onChange={(e) => setManualId(e.target.value)}
                  />
                </label>
                <label className={fieldLabel}>
                  Пол голоса
                  <select
                    className={field}
                    value={manualGender}
                    onChange={(e) => setManualGender(e.target.value)}
                  >
                    <option value="">Не указан</option>
                    <option value="male">Мужской</option>
                    <option value="female">Женский</option>
                  </select>
                </label>
              </>
            )}
            <label className={fieldLabel}>
              Название голоса
              <input
                className={field}
                value={name}
                required
                maxLength={160}
                onChange={(e) => setName(e.target.value)}
              />
            </label>
            <button className={primaryButton} disabled={saving}>
              {saving ? "Сохраняем…" : "Сохранить в библиотеку"}
            </button>
          </form>
        )}
      </fieldset>
      {error && (
        <p className={formError} role="alert">
          {error}
        </p>
      )}
    </section>
  );
}
