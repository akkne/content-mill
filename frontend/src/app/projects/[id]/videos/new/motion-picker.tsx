"use client";
import { useState } from "react";
import { useInterfaceLanguage, useTranslator } from "@/app/interface-language";
import { field, fieldLabel, secondaryButton } from "@/app/ui-styles";
import { MotionPreview } from "@/app/montage/preview";
import type { MotionStyle } from "@/lib/motion";

export function MotionPicker({
  library,
  styleId,
  onChange,
  origin,
}: {
  library: { styles: MotionStyle[]; saved: string[] };
  styleId: string;
  onChange: (id: string) => void;
  origin: string;
}) {
  const t = useTranslator();
  const lang = useInterfaceLanguage();
  const [showPreview, setPreview] = useState(false);
  const style = library.styles.find((s) => s.id === styleId);
  return (
    <fieldset className="grid gap-3 rounded-xl border border-line p-4">
      <legend className="px-1 font-bold">{t("Монтаж", "Editing")}</legend>
      <label className={fieldLabel}>
        {t("Стиль монтажа", "Editing style")}
        <select
          name="motion_template"
          className={field}
          value={styleId}
          onChange={(e) => onChange(e.target.value)}
        >
          {[true, false].map((saved) => (
            <optgroup
              key={String(saved)}
              label={
                saved
                  ? t("Из базы знаний", "Project library")
                  : t("Каталог OpenMotion", "OpenMotion catalog")
              }
            >
              {library.styles
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
      <label className={fieldLabel}>
        {t("Размещение анимации", "Animation placement")}
        <select className={field} name="motion_layout">
          <option value="panel">{t("Поверх съёмки", "Overlay footage")}</option>
          <option value="split">
            {t("Разделённый экран", "Split screen")}
          </option>
          <option value="intro">
            {t("Заставка до 4 секунд", "Intro up to 4 seconds")}
          </option>
        </select>
      </label>
      <button
        type="button"
        className={secondaryButton}
        onClick={() => setPreview(!showPreview)}
      >
        {showPreview
          ? t("Скрыть анимацию", "Hide animation")
          : t("Посмотреть анимацию", "Preview animation")}
      </button>
      {showPreview && style && (
        <MotionPreview key={style.id} style={style} origin={origin} />
      )}
    </fieldset>
  );
}
