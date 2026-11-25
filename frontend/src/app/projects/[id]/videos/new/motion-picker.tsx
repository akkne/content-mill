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
}: {
  library: { styles: MotionStyle[]; reels: ReelFormat[]; saved: string[] };
  reel: ReelFormat;
  onReel: (id: string) => void;
  styleId: string;
  onChange: (id: string) => void;
}) {
  const lang = useInterfaceLanguage(),
    t = useTranslator();
  const style = library.styles.find((s) => s.id === styleId);
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
          <p className="text-sm text-muted">
            {t("GPT выберет реплики для иллюстраций. Для каждой модель создаст макет и прозрачную анимацию поверх спикера. В паузах останутся только спикер и субтитры.", "GPT chooses which lines to illustrate. Each gets its own design and transparent animation over the speaker. Breather moments keep just the speaker and captions.")}
          </p>
          <details className="rounded-xl border border-line p-3">
            <summary className="cursor-pointer font-semibold">
              {t("Визуальный референс", "Visual reference")} · {style?.[lang].title ?? t("Из материалов проекта", "Project branding")}
            </summary>
            <InsertSelect library={library} value={styleId} change={onChange} label={t("Стиль иллюстраций", "Illustration style")} />
          </details>
          {style && (
            <input type="hidden" name="motion_template" value={style.id} />
          )}
        </div>
        <div>
          <ReelPreview reel={reel} />
          <p className="mt-2 text-center text-xs text-muted">
            {t("Пример на архивных кадрах", "Sample using archive footage")}
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
        {t("Референс", "Reference")}
        <select
          className={field}
          value={value}
          onChange={(e) => change(e.target.value)}
        >
          <option value="">{t("Из материалов проекта", "Project branding")}</option>
          {[true, false].map((saved) => (
            <optgroup
              key={String(saved)}
              label={
                saved
                  ? t("База знаний", "Project library")
                  : t("Все референсы", "All references")
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
