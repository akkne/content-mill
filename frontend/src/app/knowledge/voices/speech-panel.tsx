"use client";
import { useTranslator } from "@/app/interface-language";

import { useEffect, useState, useTransition } from "react";
import {
  field,
  fieldLabel,
  primaryButton,
  secondaryButton,
} from "@/app/ui-styles";
import { speechHistory, speechResult, synthesize } from "./actions";


function Recording({ voice, id }: { voice: string; id: string }) {
  const t = useTranslator();
  const labels: Record<string, string> = {
    submitting: t("Отправляем заказ…", "Submitting order…"),
    processing: t("Lumean озвучивает текст…", "Lumean is generating speech…"),
    failed: t("Заказ завершился без готовой дорожки.", "The order ended without an audio track."),
    uncertain:
      t("Ответ на отправку потерян. Перед повторной оплатой сверьте номер заказа в Lumean.", "No confirmation received. Check the order number in Lumean before paying again."),
    expired: t("Срок хранения аудио в Lumean истёк.", "The audio has expired in Lumean."),
    completed: t("Озвучка готова", "Audio ready"),
  };
  const [result, setResult] = useState<{
    status: string;
    url: string | null;
  }>();
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    let timer: number;
    async function check() {
      const reply = await speechResult(voice, id);
      if (!active) return;
      if (!reply.data) {
        setError(reply.error);
        return;
      }
      setError("");
      setResult(reply.data);
      if (["submitting", "processing"].includes(reply.data.status))
        timer = window.setTimeout(check, 5000);
    }
    void check();
    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [voice, id, attempt]);
  return (
    <div className="grid gap-2">
      <p role="status">
        {error || (result ? labels[result.status] : t("Проверяем заказ…", "Checking order…"))}
      </p>
      {result?.url && (
        <>
          <audio controls src={result.url} className="max-w-full" />
          <a
            className="text-accent underline"
            href={result.url}
            target="_blank"
            rel="noreferrer"
          >
            {t("Открыть аудиофайл", "Open audio file")}
          </a>
        </>
      )}
      {(error || result?.url) && (
        <button
          className={secondaryButton}
          onClick={() => setAttempt(attempt + 1)}
        >
          {t("Обновить результат", "Refresh result")}
        </button>
      )}
    </div>
  );
}

export function SpeechPanel({
  voice,
  initialText = "",
}: {
  voice: string;
  initialText?: string;
}) {
  const t = useTranslator();
  const [text, setText] = useState(initialText);
  const [ids, setIds] = useState<string[]>([]);
  const [retry, setRetry] = useState<{ text: string; id: string }>();
  const [selected, setSelected] = useState("");
  const [error, setError] = useState("");
  const [pending, start] = useTransition();
  useEffect(() => {
    let active = true;
    void speechHistory(voice).then((reply) => {
      if (!active) return;
      const history = reply.data;
      if (history)
        setIds((current) => Array.from(new Set([...current, ...history])));
      else setError(reply.error);
    });
    return () => {
      active = false;
    };
  }, [voice]);
  return (
    <section className="mt-4 grid gap-3 rounded-xl border border-line p-4">
      <form
        className="grid gap-3"
        onSubmit={(e) => {
          e.preventDefault();
          if (pending || !text.trim() || text.length > 4000) return;
          const id = retry?.text === text ? retry.id : crypto.randomUUID();
          setRetry({ text, id });
          setError("");
          start(async () => {
            const reply = await synthesize(voice, text.trim(), id);
            if (!reply.data) {
              setError(reply.error);
              const history = await speechHistory(voice);
              if (history.data) {
                setIds(history.data);
                if (history.data.includes(id)) {
                  setSelected(id);
                  setRetry(undefined);
                }
              }
              return;
            }
            setRetry(undefined);
            setIds((previous) => [
              id,
              ...previous.filter((item) => item !== id),
            ]);
            setSelected(id);
          });
        }}
      >
        <label className={fieldLabel}>
          {t("Текст озвучки", "Text to narrate")}
          <textarea
            className={field}
            rows={4}
            maxLength={4000}
            required
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
        </label>
        <small className="text-muted">
          {text.length} {t("/ 4000 символов · Eleven Multilingual v2", "/ 4000 characters · Eleven Multilingual v2")}
        </small>
        <button
          className={primaryButton}
          disabled={pending || !text.trim() || text.length > 4000}
        >
          {pending ? t("Отправляем…", "Sending…") : t("Озвучить за счёт баланса Lumean", "Generate speech using Lumean credit")}
        </button>
      </form>
      {error && <p role="alert">{error}</p>}
      {ids.length > 0 && (
        <label className={fieldLabel}>
          {t("Последние заказы", "Recent orders")}
          <select
            className={field}
            value={selected}
            onChange={(e) => setSelected(e.target.value)}
          >
            <option value="">{t("Выбрать заказ", "Select order")}</option>
            {ids.map((id) => (
              <option key={id} value={id}>
                {id}
              </option>
            ))}
          </select>
        </label>
      )}
      {selected && <Recording key={selected} voice={voice} id={selected} />}
    </section>
  );
}
