"use client";
import { failureCode, videoFailureMessage } from "@/lib/video-failure";
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
  const production = item.settings.production;
  const files = production?.files ?? {};
  const fileUrl = (node: string) => `/projects/${projectId}/knowledge/files/${node}/1`;
  const final = files["final.mp4"];
  const mediaUrl = final ? fileUrl(final.node) : originalUrl;
  const stages: Record<string, string> = {
    storyboard: t("Раскадровка и промпты", "Storyboard and prompts"),
    frame: t("Стартовый кадр · Nano Banana 2.1", "First frame · Nano Banana 2.1"),
    collect_frame: t("Получение кадра · Nano Banana", "Retrieving frame · Nano Banana"),
    submit: t("Запуск Kling 2.6", "Submitting to Kling 2.6"),
    collect: production?.clip_model === "kling/v2.6"
      ? t("Получение клипа · Kling 2.6", "Retrieving clip · Kling 2.6")
      : t("Получение клипа · Veo Fast", "Retrieving clip · Veo Fast"),
    speech: t("Озвучка реплики","Synthesizing dialogue"),
    collect_speech: t("Ожидание реплики","Waiting for speech"),
    mix_speech: t("Подготовка дорожки сцены","Preparing scene audio"),
    sync: t("Ведущий · HeyGen Avatar 6 Turbo","Presenter · HeyGen Avatar 6 Turbo"),
    collect_sync: t("Ожидание синхронизации губ","Waiting for lip sync"),
    dub: t("Сборка озвученной сцены","Assembling dubbed scene"),
    edit: t("Монтажный лист · Codex", "Edit decisions · Codex"),
    render: t("Рендер MP4", "Rendering MP4"),
    done: t("Готово", "Complete"),
  };
  const failure = production?.failure;
  const reason = failure?.reason ?? production?.error ?? "stage_failed";
  const stoppedStage = failure?.stage ?? production?.stage ?? "";
  const resumeStage = production?.stage ?? "";
  const polling = resumeStage.startsWith("collect") && !!production?.operation;
  const newOrder = ["frame", "submit", "sync", "speech"].includes(resumeStage);
  const sceneStage = ["frame", "collect_frame", "submit", "collect", "speech", "collect_speech", "sync", "collect_sync", "mix_speech", "dub"].includes(stoppedStage);
  const uncertainOrder = ["frame", "submit", "sync"].includes(resumeStage) && !production?.operation && stoppedStage === resumeStage && ["order_unconfirmed", "network", "timeout"].includes(reason);
  const failed = item.status === "failed";
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
        {mediaUrl ? (
          <video
            className="w-full rounded-xl"
            controls
            playsInline
            src={mediaUrl}
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
          {final ? t("Готовое видео", "Final video") : originalUrl
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
            href={files["scene-01.png"] ? fileUrl(files["scene-01.png"].node) : `/projects/${projectId}/videos/${item.id}/cover`}
            download
          >
            {t("Скачать обложку", "Download cover")}
          </a>
          {final && <a className={primaryButton} href={fileUrl(final.node)} download="final.mp4">{t("Открыть готовый MP4", "Open final MP4")}</a>}
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
          <button disabled={working} className={secondaryButton} onClick={() => setConfirm(true)}>
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
        {!draft && !working && !failed && (
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
        {working || failed ? (
          <div className={workPanel}>
            <h2 className="text-xl font-bold">{production ? (stages[failed ? stoppedStage : production.stage] ?? badge(t)[item.status]) : badge(t)[item.status]}</h2>
            <progress
              aria-label={t("Сборка видео", "Video assembly")}
              className="my-3 w-full"
              value={item.progress}
              max={100}
            />
            <p>{item.progress}%</p>
            {failed && <div role="alert" className="my-3 grid gap-2 border-l-2 border-current pl-3">
              {sceneStage && typeof production?.index === "number" && <p className="text-sm font-semibold">
                {t("Сцена", "Scene")} {production.index + 1} / {Math.ceil(item.settings.duration / 8)}
                {["speech", "collect_speech"].includes(stoppedStage) && typeof production.line === "number" && ` · ${t("Реплика", "Line")} ${production.line + 1}`}
              </p>}
              <p>{polling && ["submit", "frame"].includes(stoppedStage)
                ? t("Номер заказа Polza восстановлен. Можно получить результат.", "The Polza order ID has been recovered. You can retrieve the result.")
                : videoFailureMessage(t, uncertainOrder ? "order_unconfirmed" : reason)}</p>
              <p className="text-sm text-muted">{t("Код", "Code")} · {failure ? failureCode(failure) : reason}</p>
              <p className="text-sm">{polling
                ? t("Повтор проверит результат по сохранённому номеру заказа.", "Retry checks the existing order for its result.")
                : uncertainOrder && resumeStage === "sync" ? t("Проверьте заказ в кабинете HeyGen перед повторной отправкой.", "Check the order in your HeyGen account before resubmitting.")
                : uncertainOrder ? t("Сверьте заказ в истории Polza. Если он существует, администратор может восстановить его по ID. Создание ещё одного заказа может привести к повторной оплате.", "Check your Polza history. An administrator can recover an existing order by ID. Creating another order may incur a second charge.")
                : newOrder ? t("Повтор отправит новый заказ для этой сцены. Провайдер может списать средства.", "Retry submits a new order for this scene. The provider may charge for it.")
                : ["edit", "storyboard"].includes(resumeStage) ? t("Повтор продолжит этап подготовки. Новый вызов модели расходует квоту.", "Retry resumes preparation. A new model call uses quota.")
                : t("Повтор возобновит обработку с сохранённого этапа.", "Retry resumes processing from the saved stage.")}</p>
              <button disabled={pending} className={secondaryButton + " justify-self-start"} onClick={() => act("assemble", uncertainOrder ? "new_order" : "")}>{uncertainOrder ? t("Создать новый платный заказ", "Create a new paid order") : polling ? t("Получить результат заказа", "Retrieve order result") : t("Повторить этап", "Retry stage")}</button>
            </div>}
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
                readOnly={!draft && !!production}
                value={script}
                maxLength={6000}
                onChange={(e) => setScript(e.target.value)}
              />
            </label>
            <div className="flex flex-wrap gap-2">
              <button
                className={secondaryButton}
                disabled={pending || (!draft && !!production)}
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
                  {t("Собрать видео · платная генерация", "Generate video · paid")}
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
              {t("Монтажный лист", "Edit plan")}
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
        {Object.keys(files).length > 0 && <section className={workPanel}>
          <h3 className="mb-2 font-bold">{t("Файлы сборки", "Production files")}</h3>
          {Object.entries(files).map(([name, file]) => <a key={name} href={fileUrl(file.node)} className="block text-accent">{name}</a>)}
        </section>}
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
