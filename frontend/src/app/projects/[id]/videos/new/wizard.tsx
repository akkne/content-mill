"use client";
import { optionLabel } from "../video-labels";
import { useTranslator } from "@/app/interface-language";
import { MaterialPicker, resolveMaterials } from "./material-picker";
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
import { CastPicker, type CastRow } from "./cast-picker";
import { Cover } from "../cover";
import { saveVideo } from "../actions";


export function Wizard({
  projectId,
  data,
}: {
  projectId: string;
  data: VideoOptions;
}) {
  const t = useTranslator();
  const labels = {
    method: t("Формат подачи", "Presentation style"),
    platform: t("Площадка", "Platform"),
    duration: t("Длительность", "Duration"),
    language: t("Язык", "Language"),
  };
  const [cast,setCast] = useState<CastRow[]>([]);
  const [sources, setSources] = useState(data.sources);
  const [manualSelection, setManualSelection] = useState(() => [
    ...data.folders.filter(f => !f.parent_id && ["Промпты", "Бренд", "Формулы роликов"].includes(f.name)).map(f => f.id),
    ...data.sources.filter(source => source.selected).map(source => source.id),
  ]);
  const [excludedCastFolders, setExcludedCastFolders] = useState<string[]>([]);
  const avatarFolders = new Set(cast.map(row => row.character_id).filter(Boolean));
  const castFolders = new Set(cast.flatMap(row => [row.character_id, row.voice_id].filter((id): id is string => !!id)));
  const selection = [...new Set([...manualSelection, ...Array.from(castFolders).filter(id => !excludedCastFolders.includes(id))])];

  function changeSelection(next: string[]) {
    setManualSelection(next.filter(id => !castFolders.has(id) || manualSelection.includes(id)));
    setExcludedCastFolders(Array.from(castFolders).filter(id => !next.includes(id)));
  }

  function changeCast(next: CastRow[]) {
    const retained = new Set(next.flatMap(row => [row.character_id, row.voice_id]));
    setExcludedCastFolders(previous => previous.filter(id => retained.has(id)));
    setCast(next);
  }
  const [uploading, setUploading] = useState(false);
  const [step, setStep] = useState(0);
  const [title, setTitle] = useState("");
  const [duration, setDuration] = useState(30);
  const [review, setReview] = useState<FormData>();
  const [error, setError] = useState("");
  const [pending, start] = useTransition();
  const selectedVersions = resolveMaterials(selection, data.folders, sources, avatarFolders);
  const attachments = sources.filter(source => selectedVersions.has(source.id));
  return (
    <>
      <h1 className={pageTitle}>{t("Создать ролик", "Create video")}</h1>
      <p className={pageLead}>
        {t("Ваши материалы, голос бренда и подходящий формат.", "Your materials, brand voice and preferred format.")}
      </p>
      <ol className="mb-5 flex flex-wrap gap-3">
        {[t("Материалы", "Materials"), t("Формат", "Format"), t("Запуск", "Launch")].map((s, i) => (
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
            if(cast.some(r=>!r.character_id)){setError(t("Выберите аватар в каждой строке.","Choose an avatar for each row."));setStep(0);return;}
            if (selectedVersions.size > 100) {
              setError(t("Выберите не более 100 файлов для ролика.", "Select up to 100 files for the video."));
              setStep(0);
              return;
            }
            setError("");
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
                  {t("Проект", "Project")}
                  <input className={field} disabled value={data.project} />
                </label>
                <label className={fieldLabel}>
                  {t("Товар или услуга", "Product or service")}
                  <select className={field} name="product">
                    <option value="">{t("Не выбран", "None selected")}</option>
                    {data.products.map((p) => (
                      <option key={p}>{p}</option>
                    ))}
                  </select>
                </label>
              </div>
              <label className={fieldLabel}>
                {t("Название или идея ролика", "Video title or idea")}
                <input
                  required
                  className={field}
                  name="title"
                  maxLength={180}
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  pattern=".*\S.*"
                  placeholder={t("Как подготовить ролик за один день", "How to prepare a video in one day")}
                />
              </label>
              <label className={fieldLabel}>
                {t("Что показать и какую мысль донести", "What to show and what message to convey")}
                <textarea
                  className={field}
                  name="brief"
                  rows={4}
                  placeholder={t("Персонаж 1 — Анна. Анна стоит на сцене и говорит…", "Character 1 — Anna. Anna stands on stage and says…")}
                  maxLength={2000}
                />
              </label>
              <CastPicker data={data} rows={cast} change={changeCast}/>
              <label className="grid gap-2 rounded-xl border border-dashed border-line p-4">
                <strong>{t("Свои кадры и фото товара", "Your footage and product photos")}</strong>
                <span className="text-muted">
                  {t("Файлы сохранятся в базе знаний проекта.", "Files will be saved to the project knowledge base.")}
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
                            node_id: node.id,
                            parent_id: node.parent_id,
                          },
                        ]);
                        setManualSelection(previous => [...previous, version.id]);
                      }
                    } catch (err) {
                      setError(
                        err instanceof Error
                          ? err.message
                          : t("Не удалось загрузить файл", "Could not upload file"),
                      );
                    } finally {
                      setUploading(false);
                    }
                  }}
                />
                {uploading && <span role="status">{t("Загрузка файлов…", "Uploading files…")}</span>}
              </label>
              <MaterialPicker project={data.project} folders={data.folders} sources={sources}
                selection={selection} avatarFolders={avatarFolders} onChange={changeSelection} disabled={pending || uploading} />
              {Array.from(selectedVersions, id => <input key={id} type="hidden" name="sources" value={id} />)}
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
                        {optionLabel(v, t)}
                        {k === "duration" ? t(" секунд", " seconds") : ""}
                      </option>
                    ))}
                  </select>
                </label>
              ))}

              <label className={fieldLabel}>
                {t("Соотношение сторон", "Aspect ratio")}
                <input
                  className={field}
                  disabled
                  value={t("9:16 · вертикальный ролик", "9:16 · vertical video")}
                />
              </label>
            </div>
          </div>
          {step === 2 && (
            <div className="grid gap-3">
              <h2 className="font-bold">{t("Проверка перед запуском", "Review before launch")}</h2>
              {[
                [t("Идея", "Idea"), title],
                [t("Товар", "Product"), review?.get("product") || t("Не выбран", "None selected")],
                [
                  t("Формат", "Format"),
                  optionLabel(String(review?.get("method") ?? ""), t) + " · " + optionLabel(String(review?.get("platform") ?? ""), t),
                ],
                [t("Настройки", "Settings"), duration + t(" сек · ", " sec · ") + optionLabel(String(review?.get("language") ?? ""), t)],
                [
                  t("Персонажи и голоса", "Characters and voices"),
                  cast.map(r=>(data.avatars.find(a=>a.id===r.character_id)?.name??"")+" · "+(data.cast_voices.find(v=>v.id===r.voice_id)?.name??t("Без реплик","No dialogue"))).join(", ") || t("Не выбраны","None selected"),
                ],
                [t("Материалы", "Materials"), attachments.length + t(" файлов", " files")],
              ].map(([k, v]) => (
                <p
                  key={String(k)}
                  className="flex justify-between gap-4 border-b border-line py-2"
                >
                  <span>{String(k)}</span>
                  <strong>{String(v)}</strong>
                </p>
              ))}
              {attachments.length>0 && <details><summary className="cursor-pointer font-bold">{t("Файлы для агента","Files for the agent")}</summary>
                <ul className="mt-2 grid max-h-52 gap-1 overflow-auto text-sm">{attachments.map(file=><li key={file.id}>{file.path??file.name} · v{file.version}</li>)}</ul>
              </details>}
              <p className="text-muted">
                {t("Nano Banana создаст кадры, Veo Fast — видео с речью персонажей. Для выбранных персонажей ElevenLabs озвучивает реплики. При сборке эта дорожка накладывается на видео Veo. Эти операции оплачиваются отдельно. Готовый MP4 появится в проекте.", "Nano Banana creates the frames and Veo Fast generates video with character dialogue. For selected characters, ElevenLabs generates dialogue. The resulting voice track is added to the Veo video. These are billed separately. The final MP4 will appear in your project.")}
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
                onClick={(event) => {
                  event.preventDefault();
                  setStep(step - 1);
                }}
              >
                {t("← Назад", "← Back")}
              </button>
            ) : (
              <button
                disabled={pending || uploading}
                type="submit"
                value="draft"
                className={secondaryButton}
              >
                {t("Сохранить черновик", "Save draft")}
              </button>
            )}
            <button
              className={primaryButton}
              disabled={pending || uploading}
              type="submit"
            >
              {pending
                ? t("Сохранение…", "Saving…")
                : step === 2
                  ? t("Собрать видео · платная генерация", "Generate video · paid")
                  : t("Продолжить →", "Continue →")}
            </button>
          </div>
        </form>
        <aside className={workPanel + " text-center"}>
          <p className="mb-3 text-xs font-bold tracking-widest text-muted">
            {t("ПРЕВЬЮ КОМПОЗИЦИИ", "COMPOSITION PREVIEW")}
          </p>
          <Cover
            large
            project={data.project}
            duration={duration}
            title={title}
          />
          <p className="mt-2 text-xs text-muted">{t("Обложка-заготовка · 9:16", "Cover template · 9:16")}</p>
        </aside>
      </div>
    </>
  );
}
