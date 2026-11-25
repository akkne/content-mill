"use client";
import { useState } from "react";
import { useInterfaceLanguage, useTranslator } from "@/app/interface-language";
import { field, fieldLabel } from "@/app/ui-styles";
import { ReelPreview } from "@/app/montage/reel-preview";
import type { MotionStyle, ReelFormat } from "@/lib/motion";

export function MotionPicker({
  library,
  reel,
  onReel,
  styleId,
  onChange,
  outroId,
  onOutro,
  title,
  origin,
}: {
  library: { styles: MotionStyle[]; reels: ReelFormat[]; saved: string[] };
  reel: ReelFormat;
  onReel: (id: string) => void;
  outroId: string;
  onOutro: (id: string) => void;
  title: string;
  styleId: string;
  onChange: (id: string) => void;
  origin: string;
}) {
  const lang = useInterfaceLanguage(),
    t = useTranslator();
  const [layout, place] = useState("panel");
  const style = library.styles.find((s) => s.id === styleId);
  const outro = library.styles.find((s) => s.id === outroId);
  return (
    <fieldset className="rounded-2xl border border-line p-4">
      <legend className="px-2 font-bold">
        {t("Монтаж рилса", "Reel edit")}
      </legend>
      <div className="grid gap-5 md:grid-cols-[minmax(0,1fr)_minmax(130px,34%)]">
        <div className="grid content-start gap-4">
          <fieldset className="grid gap-2">
            <legend className="mb-2 font-semibold">
              {t("Формат монтажа", "Edit format")}
            </legend>
            {library.reels.map((r) => (
              <label
                key={r.id}
                className={
                  "flex cursor-pointer items-start gap-3 rounded-xl border p-3 " +
                  (r.id === reel.id ? "border-accent" : "border-line")
                }
              >
                <input
                  className="mt-1"
                  type="radio"
                  name="reel_format"
                  value={r.id}
                  checked={r.id === reel.id}
                  onChange={() => onReel(r.id)}
                />
                <span>
                  <strong>{r[lang].title}</strong> · {r[lang].pace}
                  <small className="block text-muted">{r[lang].beats}</small>
                </span>
              </label>
            ))}
          </fieldset>
          <details
            open={styleId || outroId ? true : undefined}
            className="rounded-xl border border-line p-3"
          >
            <summary className="cursor-pointer font-semibold">
              {t("Анимированная вставка", "Animated insert")} ·{" "}
              {[style?.[lang].title, outro?.[lang].title]
                .filter(Boolean)
                .join(" + ") || t("Без вставок", "None")}
            </summary>
            <div className="mt-3 grid gap-3">
              <InsertSelect
                library={library}
                value={styleId}
                change={onChange}
                label={t("Основная вставка", "Main insert")}
              />
              {style && (
                <label className={fieldLabel}>
                  {t("Где показать вставку", "Insert placement")}
                  <select
                    name="motion_layout"
                    className={field}
                    value={layout}
                    onChange={(e) => place(e.target.value)}
                  >
                    <option value="intro">
                      {t("В начале · заставка", "Opening · intro")}
                    </option>
                    <option value="panel">
                      {t("В середине · поверх кадра", "Middle · overlay")}
                    </option>
                    <option value="split">
                      {t(
                        "В середине · разделённый экран",
                        "Middle · split screen",
                      )}
                    </option>
                  </select>
                </label>
              )}
              <InsertSelect
                library={library}
                value={outroId}
                change={onOutro}
                label={t("Финальная вставка", "Closing insert")}
              />
            </div>
          </details>
          {outro && (
            <input type="hidden" name="outro_template" value={outro.id} />
          )}
          {style && (
            <input type="hidden" name="motion_template" value={style.id} />
          )}
        </div>
        <div>
          <ReelPreview
            key={reel.id}
            reel={reel}
            insert={style}
            outro={outro}
            title={title}
            layout={layout}
            origin={origin}
          />
          <p className="mt-2 text-center text-xs text-muted">
            {t("Пример на архивных кадрах", "Sample using archive footage")}
            {style && " · " + t("вставка до 3 сек", "insert up to 3 sec")}
          </p>
        </div>
      </div>
    </fieldset>
  );
}

function InsertSelect({
  library,
  value,
  change,
  label,
}: {
  library: { styles: MotionStyle[]; saved: string[] };
  value: string;
  change: (id: string) => void;
  label: string;
}) {
  const lang = useInterfaceLanguage(),
    t = useTranslator(),
    [query, search] = useState("");
  const matches = library.styles.filter(
    (s) =>
      s.id === value ||
      [s[lang].title, ...s[lang].tags, s.brand]
        .join(" ")
        .toLocaleLowerCase()
        .includes(query.toLocaleLowerCase().trim()),
  );
  return (
    <fieldset className="grid gap-2">
      <legend className="font-semibold">{label}</legend>
      <label className={fieldLabel}>
        {t("Поиск по названию или категории", "Search by title or category")}
        <input
          className={field}
          value={query}
          onChange={(e) => search(e.target.value)}
        />
      </label>
      <label className={fieldLabel}>
        {t("Анимация", "Animation")}
        <select
          className={field}
          value={value}
          onChange={(e) => change(e.target.value)}
        >
          <option value="">{t("Без вставки", "No insert")}</option>
          {[true, false].map((saved) => (
            <optgroup
              key={String(saved)}
              label={
                saved
                  ? t("База знаний", "Project library")
                  : t("Все вставки", "All inserts")
              }
            >
              {matches
                .filter((s) => library.saved.includes(s.id) === saved)
                .map((s) => (
                  <option key={s.id} value={s.id}>
                    {s[lang].title}
                  </option>
                ))}
            </optgroup>
          ))}
        </select>
      </label>
    </fieldset>
  );
}
