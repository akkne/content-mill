"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import type { MotionStyle, ReelFormat } from "@/lib/motion";
import type { Project } from "@/lib/projects";
import { useInterfaceLanguage, useTranslator } from "../interface-language";
import {
  field,
  fieldLabel,
  pageTitle,
  primaryButton,
  secondaryButton,
} from "../ui-styles";
import { MotionPreview } from "./preview";
import { ReelPreview } from "./reel-preview";
import { assignStyle } from "./actions";

export function Catalog({
  styles,
  reels,
  saved,
  project,
  projects,
  origin,
}: {
  reels: ReelFormat[];
  styles: MotionStyle[];
  saved: string[];
  project: string;
  projects: Project[];
  origin: string;
}) {
  const lang = useInterfaceLanguage(),
    t = useTranslator(),
    router = useRouter();
  const [mine, setMine] = useState(saved),
    [onlyMine, filterMine] = useState(false);
  const [q, search] = useState(""),
    [tag, category] = useState(""),
    [sort, order] = useState("catalog"),
    [limit, more] = useState(12);
  const [preview, inspect] = useState(""),
    [error, setError] = useState(""),
    [pending, start] = useTransition();
  const [tab, setTab] = useState<"reels" | "inserts">("reels");
  const tags = new Map<string, string>();
  for (const style of styles) {
    style.en.tags.forEach((key, index) =>
      tags.set(key, style[lang].tags[index] ?? key),
    );
  }
  const items = styles.filter(
    (s) =>
      (!onlyMine || mine.includes(s.id)) &&
      (!tag || s.en.tags.includes(tag)) &&
      [s[lang].title, s.brand, s[lang].use, s[lang].description]
        .join(" ")
        .toLocaleLowerCase()
        .includes(q.trim().toLocaleLowerCase()),
  );
  if (sort === "name")
    items.sort((a, b) => a[lang].title.localeCompare(b[lang].title, lang));
  if (sort === "duration") items.sort((a, b) => a.duration - b.duration);
  const reelItems = reels.filter(
    (r) =>
      (!onlyMine || mine.includes(r.id)) &&
      Object.values(r[lang])
        .join(" ")
        .toLocaleLowerCase()
        .includes(q.trim().toLocaleLowerCase()),
  );
  if (sort === "name")
    reelItems.sort((a, b) => a[lang].title.localeCompare(b[lang].title, lang));
  if (sort === "duration") reelItems.sort((a, b) => a.duration - b.duration);
  function save(id: string) {
    start(async () => {
      setError("");
      try {
        if (!(await assignStyle(project, id))) throw Error();
        setMine((prev) => [...prev, id]);
      } catch {
        setError(t("Не удалось сохранить стиль.", "Could not save the style."));
      }
    });
  }
  return (
    <>
      <h1 className={pageTitle}>{t("Монтаж", "Editing")}</h1>
      <div
        className="my-4 flex flex-wrap gap-2"
        role="group"
        aria-label={t("Библиотека монтажа", "Editing library")}
      >
        <button
          type="button"
          aria-pressed={tab === "reels"}
          className={tab === "reels" ? primaryButton : secondaryButton}
          onClick={() => {
            setTab("reels");
            search("");
            category("");
          }}
        >
          {t("Монтаж рилсов", "Reel edits")} · {reels.length}
        </button>
        <button
          type="button"
          aria-pressed={tab === "inserts"}
          className={tab === "inserts" ? primaryButton : secondaryButton}
          onClick={() => {
            setTab("inserts");
            search("");
            category("");
          }}
        >
          {t("Референсы анимации", "Animation references")} · {styles.length}
        </button>
      </div>
      <div className="my-5 grid gap-3 rounded-2xl border border-line bg-surface p-4 sm:grid-cols-2 xl:grid-cols-4">
        <label className={fieldLabel}>
          {t("Найти стиль", "Find a style")}
          <input
            className={field}
            value={q}
            placeholder={t("Название, бренд, приём", "Title, brand, technique")}
            onChange={(e) => {
              search(e.target.value);
              more(12);
            }}
          />
        </label>
        {tab === "inserts" && (
          <label className={fieldLabel}>
            {t("Категория", "Category")}
            <select
              className={field}
              value={tag}
              onChange={(e) => {
                category(e.target.value);
                more(12);
              }}
            >
              <option value="">{t("Все категории", "All categories")}</option>
              {Array.from(tags)
                .sort((a, b) => a[1].localeCompare(b[1], lang))
                .map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
            </select>
          </label>
        )}
        <label className={fieldLabel}>
          {t("Порядок", "Sort by")}
          <select
            className={field}
            value={sort}
            onChange={(e) => order(e.target.value)}
          >
            <option value="catalog">{t("По каталогу", "Catalog order")}</option>
            <option value="name">{t("По названию", "Title")}</option>
            <option value="duration">
              {t("Сначала короткие", "Shortest first")}
            </option>
          </select>
        </label>
        <label className={fieldLabel}>
          {t("База знаний проекта", "Project knowledge base")}
          <select
            className={field}
            value={project}
            onChange={(e) => router.push("/montage?project=" + e.target.value)}
          >
            {!projects.length && (
              <option>{t("Нет проектов", "No projects")}</option>
            )}
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div className="mb-4 flex justify-between gap-4 text-sm">
        <label>
          <input
            type="checkbox"
            checked={onlyMine}
            onChange={(e) => {
              filterMine(e.target.checked);
              more(12);
            }}
          />{" "}
          {t("Сохранённые в проекте", "Saved to project")} (
          {
            mine.filter((id) =>
              tab === "reels"
                ? reels.some((r) => r.id === id)
                : styles.some((s) => s.id === id),
            ).length
          }
          )
        </label>
        <span>
          {t("Найдено", "Results")} ·{" "}
          {tab === "reels" ? reelItems.length : items.length}
        </span>
      </div>
      {error && <p role="alert">{error}</p>}
      {!(tab === "reels" ? reelItems : items).length && (
        <p>{t("Подходящих стилей пока нет.", "No matching styles.")}</p>
      )}
      {tab === "reels" ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {reelItems.map((r) => (
            <article
              key={r.id}
              className="grid content-start gap-3 rounded-2xl border border-line bg-surface p-4"
            >
              <ReelPreview reel={r} />
              <div>
                <p className="text-xs text-muted">
                  {r[lang].pace} · {r.duration} {t("сек", "sec")}
                </p>
                <h2 className="text-xl font-bold">{r[lang].title}</h2>
              </div>
              <p className="text-sm font-semibold">{r[lang].beats}</p>
              <div className="flex flex-wrap gap-2">
                {project && (
                  <>
                    <Link
                      className={primaryButton}
                      href={`/projects/${project}/videos/new?reel=${r.id}`}
                    >
                      {t("Использовать формат", "Use format")}
                    </Link>
                    <button
                      type="button"
                      className={secondaryButton}
                      disabled={pending || mine.includes(r.id)}
                      onClick={() => save(r.id)}
                    >
                      {mine.includes(r.id)
                        ? t("В базе знаний", "Saved")
                        : t("+ В базу знаний", "+ Save to project")}
                    </button>
                  </>
                )}
              </div>
            </article>
          ))}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 2xl:grid-cols-3">
          {items.slice(0, limit).map((s) => (
            <article
              key={s.id}
              className="flex flex-col gap-3 overflow-hidden rounded-2xl border border-line bg-surface p-4 shadow-panel"
            >
              {preview === s.id ? (
                <MotionPreview key={s.id} style={s} origin={origin} />
              ) : (
                <button
                  type="button"
                  className="relative aspect-video overflow-hidden rounded-xl bg-black text-white"
                  onClick={() => inspect(s.id)}
                  aria-label={
                    t("Смотреть анимацию", "Preview animation") +
                    " · " +
                    s[lang].title
                  }
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    loading="lazy"
                    alt=""
                    src={s.poster}
                    className="size-full object-cover"
                  />
                  <span className="absolute bottom-2 left-2 rounded-full bg-black/80 px-3 py-1 text-xs">
                    ▶ {t("Анимация", "Animation")} · {Math.round(s.duration)} s
                  </span>
                </button>
              )}
              <div>
                <p className="text-xs font-bold uppercase text-muted">
                  {s[lang].tags.join(" · ")}
                </p>
                <h2 className="mt-1 text-lg font-bold leading-tight">
                  {s[lang].title}
                </h2>
              </div>
              <p className="line-clamp-3 text-sm text-muted">
                {s[lang].description}
              </p>
              <div className="mt-auto flex flex-wrap items-center gap-2">
                <a
                  href={s.reference}
                  target="_blank"
                  rel="noreferrer"
                  className={secondaryButton}
                >
                  {t("Референс ↗", "Reference ↗")}
                </a>
                {project && (
                  <>
                    <button
                      disabled={pending || mine.includes(s.id)}
                      type="button"
                      className={secondaryButton}
                      onClick={() => save(s.id)}
                    >
                      {mine.includes(s.id)
                        ? t("В базе знаний", "Saved")
                        : t("+ В базу знаний", "+ Save to project")}
                    </button>
                    <Link
                      className={primaryButton}
                      href={`/projects/${project}/videos/new?style=${s.id}`}
                    >
                      {t("Создать ролик", "Create video")}
                    </Link>
                  </>
                )}
              </div>
            </article>
          ))}
        </div>
      )}
      {tab === "reels" && (
        <div className="mt-5 flex flex-wrap justify-between gap-3 text-sm text-muted">
          <a
            href="https://images.nasa.gov/details/KSC-19690716-MH-NAS01-0001-Apollo_11_Breakfast_C7Exit_Convoy_WhiteRmHatchClosing_Launch-HM_0083"
            target="_blank"
            rel="noreferrer"
            className="underline"
          >
            {t(
              "Архивные кадры · NASA Kennedy Space Center",
              "Archive footage · NASA Kennedy Space Center",
            )}
          </a>
          <a className="underline" target="_blank" rel="noreferrer"
            href="https://images.nasa.gov/details/GSFC_20150916_AACS_m11991_Thinning_Ice">
            {t("Келли Брант о полярном льде · NASA", "Kelly Brunt on thinning ice · NASA")}
          </a>
          {project && (
            <Link
              href={`/projects/${project}/videos?status=ready`}
              className="underline"
            >
              {t("Готовые ролики проекта", "Finished project videos")} →
            </Link>
          )}
        </div>
      )}
      {tab === "inserts" && items.length > limit && (
        <button
          type="button"
          className={secondaryButton + " mt-5"}
          onClick={() => more(limit + 12)}
        >
          {t("Показать ещё", "Show more")}
        </button>
      )}
    </>
  );
}
