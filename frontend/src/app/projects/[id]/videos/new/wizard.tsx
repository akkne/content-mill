"use client";
import Link from "next/link";
import { useState, useTransition } from "react";
import {
  field,
  fieldLabel,
  pageLead,
  pageTitle,
  primaryButton,
  secondaryButton,
  workPanel,
} from "@/app/ui-styles";
import type { VideoOptions } from "@/lib/videos";
import {
  acceptedMedia,
  uploadMediaVersion,
} from "../../knowledge/upload-media";
import { Cover } from "../cover";
import { saveVideo } from "../actions";

const labels = {
  method: "Формат подачи",
  platform: "Площадка",
  duration: "Длительность",
  voice: "Голос",
  language: "Язык",
};

export function Wizard({
  projectId,
  data,
}: {
  projectId: string;
  data: VideoOptions;
}) {
  const [sources, setSources] = useState(data.sources);
  const [uploading, setUploading] = useState(false);
  const [step, setStep] = useState(0);
  const [title, setTitle] = useState("");
  const [duration, setDuration] = useState(30);
  const [review, setReview] = useState<FormData>();
  const [error, setError] = useState("");
  const [pending, start] = useTransition();
  return (
    <>
      <h1 className={pageTitle}>Создать ролик</h1>
      <p className={pageLead}>
        Ваши материалы, голос бренда и подходящий формат.
      </p>
      <ol className="mb-5 flex flex-wrap gap-3">
        {["Материалы", "Формат", "Запуск"].map((s, i) => (
          <li
            key={s}
            aria-current={step === i ? "step" : undefined}
            className="rounded-full bg-control px-4 py-2 font-bold text-muted aria-current:bg-selected aria-current:text-selected-ink"
          >
            {i + 1}　{s}
          </li>
        ))}
      </ol>
      <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <form
          className={workPanel + " self-start"}
          onSubmit={(e) => {
            e.preventDefault();
            const values = new FormData(e.currentTarget);
            const submit = (e.nativeEvent as SubmitEvent)
              .submitter as HTMLButtonElement;
            if (step < 2 && submit?.value !== "draft") {
              setReview(values);
              setStep(step + 1);
              return;
            }
            values.set("action", step === 2 ? "assemble" : "draft");
            start(async () =>
              setError(await saveVideo(projectId, null, values)),
            );
          }}
        >
          <div hidden={step !== 0}>
            <div className="grid gap-4">
              <div className="grid gap-3 sm:grid-cols-2">
                <label className={fieldLabel}>
                  Проект
                  <input className={field} disabled value={data.project} />
                </label>
                <label className={fieldLabel}>
                  Товар или услуга
                  <select className={field} name="product">
                    <option value="">Не выбран</option>
                    {data.products.map((p) => (
                      <option key={p}>{p}</option>
                    ))}
                  </select>
                </label>
              </div>
              <label className={fieldLabel}>
                Название или идея ролика
                <input
                  required
                  className={field}
                  name="title"
                  maxLength={180}
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  pattern=".*\S.*"
                  placeholder="Как подготовить ролик за один день"
                />
              </label>
              <label className={fieldLabel}>
                Что показать и какую мысль донести
                <textarea
                  className={field}
                  name="brief"
                  rows={4}
                  maxLength={2000}
                />
              </label>
              <label className="grid gap-2 rounded-xl border border-dashed border-line p-4">
                <strong>Свои кадры и фото товара</strong>
                <span className="text-muted">
                  Файлы сохранятся в базе знаний проекта.
                </span>
                <input
                  type="file"
                  multiple
                  accept={acceptedMedia}
                  disabled={pending || uploading}
                  onChange={async (e) => {
                    const files = Array.from(e.target.files || []);
                    e.target.value = "";
                    setUploading(true);
                    setError("");
                    try {
                      for (const file of files) {
                        const { node, version } = await uploadMediaVersion(
                          projectId,
                          null,
                          file,
                        );
                        setSources((previous) => [
                          ...previous,
                          {
                            id: version.id,
                            name: node.name,
                            version: version.version,
                            selected: true,
                          },
                        ]);
                      }
                    } catch (err) {
                      setError(
                        err instanceof Error
                          ? err.message
                          : "Не удалось загрузить файл",
                      );
                    } finally {
                      setUploading(false);
                    }
                  }}
                />
                {uploading && <span role="status">Загрузка файлов…</span>}
              </label>
              <fieldset className="rounded-xl border border-dashed border-line p-4">
                <legend className="px-1 font-bold">
                  Материалы из базы знаний
                </legend>
                <div className="grid max-h-60 gap-2 overflow-auto">
                  {sources.map((s) => (
                    <label className="flex gap-2" key={s.id}>
                      <input
                        name="sources"
                        type="checkbox"
                        value={s.id}
                        defaultChecked={s.selected}
                      />
                      {s.name} · v{s.version}
                    </label>
                  ))}
                </div>
                {!sources.length && (
                  <p className="text-muted">
                    В базе знаний пока нет сохранённых файлов.
                  </p>
                )}
                <Link
                  className="mt-2 inline-block text-accent"
                  href={`/projects/${projectId}/knowledge`}
                  target="_blank"
                >
                  Открыть базу знаний ↗
                </Link>
              </fieldset>
            </div>
          </div>
          <div hidden={step !== 1}>
            <div className="grid gap-4 sm:grid-cols-2">
              {(Object.keys(labels) as (keyof typeof labels)[]).map((k) => (
                <label className={fieldLabel} key={k}>
                  {labels[k]}
                  <select
                    className={field}
                    name={k}
                    defaultValue={k === "duration" ? 30 : undefined}
                    onChange={
                      k === "duration"
                        ? (e) => setDuration(Number(e.target.value))
                        : undefined
                    }
                  >
                    {data.options[k].map((v) => (
                      <option key={v} value={v}>
                        {v}
                        {k === "duration" ? " секунд" : ""}
                      </option>
                    ))}
                  </select>
                </label>
              ))}
              <label className={fieldLabel}>
                Соотношение сторон
                <input
                  className={field}
                  disabled
                  value="9:16 · вертикальный ролик"
                />
              </label>
            </div>
          </div>
          {step === 2 && (
            <div className="grid gap-3">
              <h2 className="font-bold">Проверка перед запуском</h2>
              {[
                ["Идея", title],
                ["Товар", review?.get("product") || "Не выбран"],
                [
                  "Формат",
                  review?.get("method") + " · " + review?.get("platform"),
                ],
                [
                  "Настройки",
                  duration +
                    " сек · " +
                    review?.get("voice") +
                    " · " +
                    review?.get("language"),
                ],
                ["Материалы", review?.getAll("sources").length + " файлов"],
              ].map(([k, v]) => (
                <p
                  key={String(k)}
                  className="flex justify-between gap-4 border-b border-line py-2"
                >
                  <span>{String(k)}</span>
                  <strong>{String(v)}</strong>
                </p>
              ))}
              <p className="text-muted">
                Демо-сборка подготовит сценарий и журнал. Видеофайл появится
                после подключения рендера.
              </p>
            </div>
          )}
          {error && <p role="alert">{error}</p>}
          <div className="mt-6 flex flex-wrap justify-between gap-2">
            {step ? (
              <button
                type="button"
                disabled={pending || uploading}
                className={secondaryButton}
                onClick={() => setStep(step - 1)}
              >
                ← Назад
              </button>
            ) : (
              <button
                disabled={pending || uploading}
                type="submit"
                value="draft"
                className={secondaryButton}
              >
                Сохранить черновик
              </button>
            )}
            <button
              className={primaryButton}
              disabled={pending || uploading}
              type="submit"
            >
              {pending
                ? "Сохранение…"
                : step === 2
                  ? "Показать демо-сборку"
                  : "Продолжить →"}
            </button>
          </div>
        </form>
        <aside className={workPanel + " text-center"}>
          <p className="mb-3 text-xs font-bold tracking-widest text-muted">
            ПРЕВЬЮ КОМПОЗИЦИИ
          </p>
          <Cover
            large
            project={data.project}
            duration={duration}
            title={title}
          />
          <p className="mt-2 text-xs text-muted">Обложка-заготовка · 9:16</p>
        </aside>
      </div>
    </>
  );
}
