"use client";

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
import { Cover, badge } from "../cover";
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
  const [tab, setTab] = useState("Публикация");
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
      setNotice(message || "Сохранено");
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
            ? "Ваши исходные кадры"
            : "Превью обложки · видео не сгенерировано"}
        </p>
        <div className="flex flex-wrap justify-center gap-2">
          <a
            className={secondaryButton}
            download="Сценарий.txt"
            href={
              "data:text/plain;charset=utf-8," + encodeURIComponent(item.script)
            }
          >
            Скачать сценарий
          </a>
          <a
            className={secondaryButton}
            href={`/projects/${projectId}/videos/${item.id}/cover`}
            download
          >
            Скачать обложку
          </a>
          {originalUrl && (
            <a
              className={secondaryButton}
              href={originalUrl}
              download={original?.name}
            >
              Исходное видео
            </a>
          )}
          <button
            disabled={pending}
            className={secondaryButton}
            onClick={() => act("duplicate")}
          >
            Другой вариант
          </button>
          <button className={secondaryButton} onClick={() => setConfirm(true)}>
            Удалить
          </button>
        </div>
        {confirm && (
          <div className={workPanel}>
            <p>Удалить ролик «{item.title}»?</p>
            <button
              disabled={pending}
              className={secondaryButton}
              onClick={() => act("delete")}
            >
              Удалить ролик
            </button>{" "}
            <button onClick={() => setConfirm(false)}>Отмена</button>
          </div>
        )}
      </aside>
      <section className="min-w-0 space-y-4">
        <span className="inline-block rounded-full bg-selected px-3 py-1 font-bold text-selected-ink">
          {badge[item.status]}
        </span>
        {!draft && !working && (
          <div className="flex flex-wrap gap-2">
            {["Публикация", "Сценарий", "Журнал"].map((t) => (
              <button
                aria-pressed={tab === t}
                key={t}
                className={
                  secondaryButton +
                  " aria-pressed:bg-selected aria-pressed:text-selected-ink"
                }
                onClick={() => {
                  setTab(t);
                  setNotice("");
                }}
              >
                {t}
              </button>
            ))}
          </div>
        )}
        {working ? (
          <div className={workPanel}>
            <h2 className="text-xl font-bold">Собираем ролик · демонстрация</h2>
            <progress
              aria-label="Демо-сборка"
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
        ) : draft || tab === "Сценарий" ? (
          <div className={workPanel + " grid gap-4"}>
            <h2 className="text-xl font-bold">
              {draft ? "Черновик готов к работе" : "Сценарий ролика"}
            </h2>
            <label className={fieldLabel}>
              Сценарий
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
                Сохранить сценарий
              </button>
              {draft && (
                <button
                  className={primaryButton}
                  disabled={pending || script !== item.script}
                  onClick={() => act("assemble")}
                >
                  Показать демо-сборку
                </button>
              )}
            </div>
            {item.settings.library_voice_id && (
              <details>
                <summary className="cursor-pointer font-semibold">
                  Озвучить сценарий · {item.settings.voice}
                </summary>
                <SpeechPanel
                  voice={item.settings.library_voice_id}
                  initialText={item.script}
                />
              </details>
            )}
          </div>
        ) : tab === "Журнал" ? (
          <div className={workPanel}>
            <h2 className="mb-3 text-xl font-bold">
              Журнал агента · демонстрация
            </h2>
            <ol className="list-inside list-decimal space-y-2">
              {item.journal.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ol>
          </div>
        ) : (
          <div className={workPanel + " grid gap-4"}>
            <h2 className="text-xl font-bold">Куда публикуем</h2>
            <label className={fieldLabel}>
              Подпись к публикации
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
                Сохранить подпись
              </button>
            </div>
            <p className="text-muted">
              Демо-публикация в {item.settings.platform} сохраняется в проекте
              без отправки в соцсеть.
            </p>
            {item.status !== "published" && (
              <div className="flex flex-wrap items-end gap-2">
                <button
                  disabled={pending}
                  className={primaryButton}
                  onClick={() => act("publish")}
                >
                  Опубликовать сейчас
                </button>
                <label className={fieldLabel}>
                  Дата и время
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
                  Запланировать
                </button>
              </div>
            )}
            <h3 className="font-bold">Публикации</h3>
            <p>
              {item.settings.publication
                ? badge[item.status] +
                  " · " +
                  new Date(item.settings.publication).toLocaleString("ru")
                : "Здесь появятся запланированные и опубликованные записи."}
            </p>
          </div>
        )}
        {item.settings.sources.length > 0 && (
          <div className={workPanel}>
            <h3 className="mb-2 font-bold">Материалы базы знаний</h3>
            {item.settings.sources.map((s) => (
              <p key={s.id}>
                {s.name} · v{s.version}
              </p>
            ))}
          </div>
        )}
        <p role="status">{pending ? "Сохранение…" : notice}</p>
      </section>
    </div>
  );
}
