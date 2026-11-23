"use client";

import { useActionState } from "react";
import { useTranslator } from "../interface-language";
import { field, fieldLabel, primaryButton } from "../ui-styles";
import { optionLabel } from "../projects/[id]/videos/video-labels";
import { saveClient } from "./actions";
import { type ClientProject, modeLabels } from "./types";

export function ClientEditor({ client, durations, styles }: {
  client: ClientProject; durations: number[]; styles: string[];
}) {
  const t = useTranslator();
  const [message, action, pending] = useActionState(saveClient.bind(null, client.id, client.admin_revision), "");
  return (
    <form action={action} className="grid gap-5 border-t border-line p-5 sm:p-6">
      <div className="grid gap-4 sm:grid-cols-2">
        <label className={fieldLabel}>{t("Модель продажи", "Sales model")}
          <select name="sales_mode" className={field} defaultValue={client.sales_mode}>
            {Object.entries(modeLabels(t)).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </label>
        <label className={fieldLabel}>{t("Тариф или пакет работ", "Plan or scope of work")}
          <input name="package_name" className={field} maxLength={160} defaultValue={client.package_name}/>
        </label>
      </div>
      <label className={fieldLabel}>{t("Договорённости с клиентом · видны только администратору", "Client agreements · admin only")}
        <textarea name="delivery_notes" className={field} rows={3} maxLength={3000} defaultValue={client.delivery_notes}/>
      </label>
      <fieldset className="grid gap-3 sm:grid-cols-2">
        <legend className="mb-3 font-bold">{t("По умолчанию для новых роликов", "Defaults for new videos")}</legend>
        <label className={fieldLabel}>{t("Длительность", "Duration")}
          <select className={field} name="video_duration" defaultValue={client.video_duration}>
            {durations.map(d => <option key={d} value={d}>{d} {t("сек", "sec")}</option>)}
          </select>
        </label>
        <label className={fieldLabel}>{t("Стиль монтажа", "Editing style")}
          <select className={field} name="video_style" defaultValue={client.video_style}>
            {styles.map(s => <option key={s} value={s}>{optionLabel(s,t)}</option>)}
          </select>
        </label>
      </fieldset>
      <div className="flex items-center gap-4">
        <button disabled={pending} className={primaryButton}>{pending ? t("Сохраняем…", "Saving…") : t("Сохранить настройки", "Save settings")}</button>
        <span aria-live="polite">{message}</span>
      </div>
    </form>
  );
}
