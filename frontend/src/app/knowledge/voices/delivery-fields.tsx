"use client";

import { useTranslator } from "@/app/interface-language";
import { field, fieldLabel } from "@/app/ui-styles";

export function DeliveryFields({ speed = 1.1, style = 0.4 }: { speed?: number; style?: number }) {
  const t = useTranslator();
  return <>
    <label className={fieldLabel}>
      {t("Скорость речи (×)", "Speech speed (×)")}
      <input className={field} type="number" name="voice_speed" required min={0.7} max={1.2} step={0.01} defaultValue={speed} />
    </label>
    <label className={fieldLabel}>
      {t("Выразительность (0–1)", "Expressiveness (0–1)")}
      <input className={field} type="number" name="voice_style" required min={0} max={1} step={0.01} defaultValue={style} />
    </label>
  </>;
}
