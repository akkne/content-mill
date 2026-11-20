"use client";
import { optionLabel } from "../video-labels";
import { useTranslator, useInterfaceLanguage } from "@/app/interface-language";

import { useRouter } from "next/navigation";
import { useEffect, useState, useTransition } from "react";
import {
  field,
  fieldLabel,
  primaryButton,
  secondaryButton,
  workPanel,
} from "@/app/ui-styles";
import { SpeechPanel } from "@/app/knowledge/voices/speech-panel";
import type { ProjectVideo } from "@/lib/videos";
import { Cover } from "../cover";
import { badge } from "../video-labels";
import { saveVideo } from "../actions";

export function VideoEditor({
  item,
  project,
  projectId,
}: {
  item: ProjectVideo;
  project: string;
  projectId: string;
}) {
  const locale = useInterfaceLanguage();
  const t = useTranslator();
  const router = useRouter();
  const working = item.status === "generating";
  useEffect(() => {
    if (!working) return;
    const timer = setInterval(() => router.refresh(), 1500);
    return () => clearInterval(timer);
  }, [working, router]);
  const original = item.settings.sources.find((s) =>
    s.format.startsWith("video/"),
  );
  const originalUrl =
    original &&
    `/projects/${projectId}/knowledge/files/${original.node_id}/${original.version}`;
  const draft = item.status === "draft";
  const [tab, setTab] = useState("publication");
  const [confirm, setConfirm] = useState(false);
  const [notice, setNotice] = useState("");
  const [script, setScript] = useState(item.script);
  const [caption, setCaption] = useState(item.caption);
  const [date, setDate] = useState("");
  const [pending, start] = useTransition();
  function act(action: string, value = "") {
    const data = new FormData();
    data.set("action", action);
    data.set("value", value);
    start(async () => {
      const message = await saveVideo(projectId, item.id, data);
      setNotice(message || t("Сохранено", "Saved"));
    });
  }
  return (
    <div className="grid gap-6 md:grid-cols-[minmax(200px,320px)_1fr]">
      <aside className="space-y-3">
        {originalUrl ? (
          <video
            className="w-full rounded-xl"
            controls
            playsInline
            src={originalUrl}
          />
        ) : (
          <Cover
            large
            title={item.title}
            duration={item.settings.duration}
            project={project}
          />
        )}
        <p className="text-center text-xs text-muted">
          {originalUrl
            ? t("Ваши исходные кадры", "Your source footage")
            : t("Превью обложки · видео не сгенерировано", "Cover preview · video has yet to be generated")}
        </p>
        <div className="flex flex-wrap justify-center gap-2">
          <a
            className={secondaryButton}
            download={t("Сценарий.txt", "Script.txt")}
            href={
              "data:text/plain;charset=utf-8," + encodeURIComponent(item.script)
            }
          >
            {t("Скачать сценарий", "Download script")}
          </a>
          <a
            className={secondaryButton}
            href={`/projects/${projectId}/videos/${item.id}/cover`}
            download
          >
            {t("Скачать обложку", "Download cover")}
          </a>
          {originalUrl && (
            <a
              className={secondaryButton}
              href={originalUrl}
              download={original?.name}
            >
              {t("Исходное видео", "Source video")}
            </a>
          )}
          <button
            disabled={pending}
            className={secondaryButton}
            onClick={() => act("duplicate")}
          >
            {t("Другой вариант", "Another version")}
          </button>
          <button className={secondaryButton} onClick={() => setConfirm(true)}>
            {t("Удалить", "Delete")}
          </button>
        </div>
        {confirm && (
          <div className={workPanel}>
            <p>{t("Удалить ролик «", "Delete video «")}{item.title}»?</p>
            <button
              disabled={pending}
              className={secondaryButton}
              onClick={() => act("delete")}
            >
              {t("Удалить ролик", "Delete video")}
            </button>{" "}
            <button onClick={() => setConfirm(false)}>{t("Отмена", "Cancel")}</button>
          </div>
        )}
      </aside>
      <section className="min-w-0 space-y-4">
        <span className="inline-block rounded-full bg-selected px-3 py-1 font-bold text-selected-ink">
          {badge(t)[item.status]}
        </span>
        {!draft && !working && (
          <div className="flex flex-wrap gap-2">
            {Object.entries({ publication: t("Публикация", "Publication"), script: t("Сценарий", "Script"), log: t("Журнал", "Log") }).map(([key, label]) => (
              <button
                aria-pressed={tab === key}
                key={key}
                className={
                  secondaryButton +
                  " aria-pressed:bg-selected aria-pressed:text-selected-ink"
                }
                onClick={() => {
                  setTab(key);
                  setNotice("");
                }}
              >
                {label}
              </button>
            ))}
          </div>
        )}
        {working ? (
          <div className={workPanel}>
            <h2 className="text-xl font-bold">{t("Собираем ролик · демонстрация", "Assembling video · demo")}</h2>
            <progress
              aria-label={t("Демо-сборка", "Demo build")}
              className="my-3 w-full"
              value={item.progress}
              max={100}
            />
            <p>{item.progress}%</p>
            <ol className="list-inside list-decimal space-y-2">
              {item.journal.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ol>
          </div>
        ) : draft || tab === "script" ? (
          <div className={workPanel + " grid gap-4"}>
            <h2 className="text-xl font-bold">
              {draft ? t("Черновик готов к работе", "Draft ready") : t("Сценарий ролика", "Video script")}
            </h2>
            <label className={fieldLabel}>
              {t("Сценарий", "Script")}
              <textarea
                className={field}
                rows={9}
                value={script}
                maxLength={6000}
                onChange={(e) => setScript(e.target.value)}
              />
            </label>
            <div className="flex flex-wrap gap-2">
              <button
                className={secondaryButton}
                disabled={pending}
                onClick={() => act("script", script)}
              >
                {t("Сохранить сценарий", "Save script")}
              </button>
              {draft && (
                <button
                  className={primaryButton}
                  disabled={pending || script !== item.script}
                  onClick={() => act("assemble")}
                >
                  {t("Показать демо-сборку", "Show demo build")}
                </button>
              )}
            </div>
            {item.settings.library_voice_id && (
              <details>
                <summary className="cursor-pointer font-semibold">
                  {t("Озвучить сценарий ·", "Narrate script ·")} {item.settings.voice}
                </summary>
                <SpeechPanel
                  voice={item.settings.library_voice_id}
                  initialText={item.script}
                />
              </details>
            )}
          </div>
        ) : tab === "log" ? (
          <div className={workPanel}>
            <h2 className="mb-3 text-xl font-bold">
              {t("Журнал агента · демонстрация", "Agent log · demo")}
            </h2>
            <ol className="list-inside list-decimal space-y-2">
              {item.journal.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ol>
          </div>
        ) : (
          <div className={workPanel + " grid gap-4"}>
            <h2 className="text-xl font-bold">{t("Куда публикуем", "Publishing destination")}</h2>
            <label className={fieldLabel}>
              {t("Подпись к публикации", "Post caption")}
              <textarea
                className={field}
                rows={5}
                maxLength={3000}
                value={caption}
                onChange={(e) => setCaption(e.target.value)}
              />
            </label>
            <div>
              <button
                disabled={pending}
                className={secondaryButton}
                onClick={() => act("caption", caption)}
              >
                {t("Сохранить подпись", "Save caption")}
              </button>
            </div>
            <p className="text-muted">
              {t("Демо-публикация в", "Demo post for")} {optionLabel(item.settings.platform, t)} {t("сохраняется в проекте без отправки в соцсеть.", "is saved in the project without posting to social media.")}
            </p>
            {item.status !== "published" && (
              <div className="flex flex-wrap items-end gap-2">
                <button
                  disabled={pending}
                  className={primaryButton}
                  onClick={() => act("publish")}
                >
                  {t("Опубликовать сейчас", "Publish now")}
                </button>
                <label className={fieldLabel}>
                  {t("Дата и время", "Date and time")}
                  <input
                    className={field}
                    type="datetime-local"
                    value={date}
                    onChange={(e) => setDate(e.target.value)}
                  />
                </label>
                <button
                  disabled={pending || !date}
                  className={secondaryButton}
                  onClick={() => act("schedule", new Date(date).toISOString())}
                >
                  {t("Запланировать", "Schedule")}
                </button>
              </div>
            )}
            <h3 className="font-bold">{t("Публикации", "Posts")}</h3>
            <p>
              {item.settings.publication
                ? badge(t)[item.status] +
                  " · " +
                  new Date(item.settings.publication).toLocaleString(locale)
                : t("Здесь появятся запланированные и опубликованные записи.", "Scheduled and published posts will appear here.")}
            </p>
          </div>
        )}
        {item.settings.sources.length > 0 && (
          <div className={workPanel}>
            <h3 className="mb-2 font-bold">{t("Материалы базы знаний", "Knowledge base materials")}</h3>
            {item.settings.sources.map((s) => (
              <p key={s.id}>
                {s.name} · v{s.version}
              </p>
            ))}
          </div>
        )}
        <p role="status">{pending ? t("Сохранение…", "Saving…") : notice}</p>
      </section>
    </div>
  );
}
