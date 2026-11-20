"use client";
import { useTranslator } from "@/app/interface-language";

import { useState, useTransition, useEffect } from "react";
import { useRouter } from "next/navigation";
import { field, fieldLabel, primaryButton, secondaryButton, workPanel } from "@/app/ui-styles";
import type { ScriptJob } from "@/lib/projects";
import { cancelScript, prepareScript } from "../actions";


export function ScriptPanel({ id, enabled, items }: { id: string; enabled: boolean; items: ScriptJob[] }) {
  const t = useTranslator();
  const labels = { queued: t("Ожидает запуска", "Queued"), running: t("Готовится", "In progress"), done: t("Готов", "Ready"), failed: t("Ошибка", "Failed"), cancelled: t("Отменён", "Cancelled") };
  const router = useRouter();
  const [brief, setBrief] = useState("");
  const [date, setDate] = useState("");
  const [notice, setNotice] = useState("");
  const [pending, start] = useTransition();
  const active = items.some(job => job.status === "queued" || job.status === "running");
  useEffect(() => {
    if (!active) return;
    const timer = setInterval(() => router.refresh(), 5000);
    return () => clearInterval(timer);
  }, [active, router]);
  return <section className={workPanel + " grid gap-4"}>
    <h2 className="text-xl font-bold">{t("Сценарии", "Scripts")}</h2>
    {enabled ? <form className="grid gap-3" onSubmit={event => {
      event.preventDefault();
      start(async () => {
        const error = await prepareScript(id, brief, date ? new Date(date).toISOString() : null);
        setNotice(error || t("Задание принято.", "Job accepted."));
        if (!error) { setBrief(""); setDate(""); router.refresh(); }
      });
    }}>
      <label className={fieldLabel}>{t("О чём ролик?", "What is the video about?")}
        <textarea className={field} rows={3} required maxLength={4000} value={brief} onChange={e => setBrief(e.target.value)} />
      </label>
      <label className={fieldLabel}>{t("Отложить запуск до (по местному времени)", "Schedule start time (local time)")}
        <input className={field} type="datetime-local" value={date} onChange={e => setDate(e.target.value)} />
      </label>
      <button className={primaryButton + " justify-self-start"} disabled={!brief.trim() || active || pending}>{date ? t("Запланировать сценарий", "Schedule script") : t("Подготовить сценарий", "Prepare script")}</button>
    </form> : <p className="text-muted">{t("Генерация сценариев пока недоступна.", "Script generation is currently unavailable.")}</p>}
    <p role="status">{notice}</p>
    {items.map(job => <details key={job.id} className="rounded-xl border border-line p-3">
      <summary className="cursor-pointer break-words">{labels[job.status]} · {job.brief}</summary>
      <p className="mt-2 text-sm text-muted">{job.model} · <time dateTime={job.run_at}>{new Date(job.run_at).toISOString().replace("T", " ").slice(0, 16)} UTC</time></p>
      {job.status === "queued" && <button className={secondaryButton} disabled={pending} onClick={() => start(async () => { setNotice(await cancelScript(id, job.id)); router.refresh(); })}>{t("Отменить запуск", "Cancel job")}</button>}
      {job.result && <p className="mt-3 whitespace-pre-wrap break-words">{job.result}</p>}
    </details>)}
  </section>;
}
