"use client";
import { DeliveryFields } from "./delivery-fields";
import { useTranslator } from "@/app/interface-language";

import { useEffect, useState, useTransition } from "react";
import {
  field,
  fieldLabel,
  formError,
  primaryButton,
  secondaryButton,
} from "@/app/ui-styles";
import { useInterfaceLanguage } from "@/app/interface-language";
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
  const t = useTranslator();
  const [mode, setMode] = useState(initialMode);
  const [description, setDescription] = useState("");
  const [manualLanguage, setManualLanguage] = useState("");
  const [model, setModel] = useState("");
  const [query, setQuery] = useState("");
  const [exact, setExact] = useState(false);
  const locale = useInterfaceLanguage();
  const [lastLocale, setLastLocale] = useState(locale);
  const [language, setLanguage] = useState<string>(locale);
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
  if (lastLocale !== locale) {
    setLastLocale(locale);
    setLanguage(locale);
    setCursors([""]);
    setSelected(undefined);
    setPlaying("");
    setError("");
  }
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
  function save(data: FormData) {
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
        voice_speed: Number(data.get("voice_speed")),
        voice_style: Number(data.get("voice_style")),
        gender: fromCatalog ? null : manualGender || null,
      });
      if (reply.data) onSave(reply.data);
      else setError(reply.error);
    });
  }

  return (
    <section
      aria-label={t("Создание голоса", "Create a voice")}
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
                ? t("ElevenLabs через Lumean", "ElevenLabs via Lumean")
                : t("Вставить ID вручную", "Enter ID manually")}
            </button>
          ))}
        </div>
        {mode === "catalog" && (
          <>
            <div className="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <label className={fieldLabel}>
                {t("Искать по", "Search by")}
                <select
                  className={field}
                  value={exact ? "id" : "name"}
                  onChange={(e) => {
                    setExact(e.target.value === "id");
                    resetPage();
                  }}
                >
                  <option value="name">{t("Названию", "Name")}</option>
                  <option value="id">{t("Точному ID", "Exact ID")}</option>
                </select>
              </label>
              <label className={fieldLabel}>
                {exact ? "ID ElevenLabs" : t("Название голоса", "Voice name")}
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
                {t("Язык", "Language")}
                <input
                  className={field}
                  list="voice-languages"
                  placeholder={t("Все языки", "All languages")}
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
                      {languageName(code, locale)}
                    </option>
                  ))}
                </datalist>
              </label>
              <label className={fieldLabel}>
                {t("Пол голоса", "Voice gender")}
                <select
                  className={field}
                  value={gender}
                  onChange={(e) => {
                    setGender(e.target.value);
                    resetPage();
                  }}
                >
                  <option value="">{t("Любой", "Any")}</option>
                  <option value="male">{t("Мужской", "Male")}</option>
                  <option value="female">{t("Женский", "Female")}</option>
                </select>
              </label>
            </div>
            {exact && !query.trim() ? (
              <p>{t("Введите ID голоса.", "Enter a voice ID.")}</p>
            ) : !current ? (
              <p role="status">{t("Загружаем голоса…", "Loading voices…")}</p>
            ) : current.error ? (
              <div role="alert">
                {current.error}{" "}
                <button
                  className={secondaryButton}
                  onClick={() => setAttempt(attempt + 1)}
                >
                  {t("Повторить", "Retry")}
                </button>
              </div>
            ) : (
              <div className="grid gap-3 sm:grid-cols-2">
                {!current.data?.items.length && <p>{t("Голоса не найдены.", "No voices found.")}</p>}
                {current.data?.items.map((voice) => (
                  <article
                    key={voice.id}
                    className="grid content-start gap-2 rounded-xl border border-line p-4"
                  >
                    <h3 className="font-semibold">{voice.name}</h3>
                    <small className="break-all text-muted">{voice.id}</small>
                    <p>{voice.description || t("Описание не указано", "No description")}</p>
                    <p className="text-sm">
                      {genderName(voice.gender, locale)} ·{" "}
                      {voice.languages.map(code => languageName(code, locale)).join(", ") ||
                        t("Языки не указаны", "No languages specified")}
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
                        {selected?.id === voice.id ? t("Выбран", "Selected") : t("Выбрать", "Select")}
                      </button>
                      {voice.preview_url ? (
                        playing === voice.id ? (
                          <audio
                            controls
                            autoPlay
                            className="max-w-full"
                            src={voice.preview_url}
                            aria-label={t(`Пример · ${voice.name}`, `Sample · ${voice.name}`)}
                          />
                        ) : (
                          <button
                            className={secondaryButton}
                            onClick={() => setPlaying(voice.id)}
                          >
                            {t("Послушать", "Listen")}
                          </button>
                        )
                      ) : (
                        <small>{t("Пример недоступен", "Sample unavailable")}</small>
                      )}
                    </div>
                  </article>
                ))}
              </div>
            )}
            <nav
              aria-label={t("Страницы каталога", "Catalog pages")}
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
                {t("Назад", "Back")}
              </button>
              <span>{t("Страница", "Page")} {cursors.length}</span>
              <button
                className={secondaryButton}
                disabled={!current?.data?.next_cursor}
                onClick={() => {
                  if (current?.data?.next_cursor)
                    setCursors([...cursors, current.data.next_cursor]);
                  setPlaying("");
                }}
              >
                {t("Далее", "Next")}
              </button>
            </nav>
          </>
        )}
        {(mode === "manual" || selected) && (
          <form
            className="sticky bottom-0 mt-5 grid gap-3 border-t border-line bg-surface py-3 sm:grid-cols-2"
            onSubmit={(event) => {
              event.preventDefault();
              save(new FormData(event.currentTarget));
            }}
          >
            {mode === "manual" && (
              <>
                <label className={fieldLabel}>
                  {t("Описание", "Description")}
                  <input
                    className={field}
                    value={description}
                    maxLength={4000}
                    onChange={(e) => setDescription(e.target.value)}
                  />
                </label>
                <label className={fieldLabel}>
                  {t("Язык", "Language")}
                  <input
                    className={field}
                    value={manualLanguage}
                    maxLength={80}
                    onChange={(e) => setManualLanguage(e.target.value)}
                  />
                </label>
                <label className={fieldLabel}>
                  {t("Модель синтеза", "Speech model")}
                  <input
                    className={field}
                    value={model}
                    maxLength={160}
                    onChange={(e) => setModel(e.target.value)}
                  />
                </label>
                <label className={fieldLabel}>
                  {t("ID голоса ElevenLabs", "ElevenLabs voice ID")}
                  <input
                    className={field}
                    value={manualId}
                    required
                    maxLength={160}
                    onChange={(e) => setManualId(e.target.value)}
                  />
                </label>
                <label className={fieldLabel}>
                  {t("Пол голоса", "Voice gender")}
                  <select
                    className={field}
                    value={manualGender}
                    onChange={(e) => setManualGender(e.target.value)}
                  >
                    <option value="">{t("Не указан", "Unspecified")}</option>
                    <option value="male">{t("Мужской", "Male")}</option>
                    <option value="female">{t("Женский", "Female")}</option>
                  </select>
                </label>
              </>
            )}
            <label className={fieldLabel}>
              {t("Название голоса", "Voice name")}
              <input
                className={field}
                value={name}
                required
                maxLength={160}
                onChange={(e) => setName(e.target.value)}
              />
            </label>
            <DeliveryFields />
            <button className={primaryButton} disabled={saving}>
              {saving ? t("Сохраняем…", "Saving…") : t("Сохранить в библиотеку", "Save to library")}
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
