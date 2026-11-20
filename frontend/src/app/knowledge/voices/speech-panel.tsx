"use client";

import { useEffect, useState, useTransition } from "react";
import {
  field,
  fieldLabel,
  primaryButton,
  secondaryButton,
} from "@/app/ui-styles";
import { speechHistory, speechResult, synthesize } from "./actions";

const labels: Record<string, string> = {
  submitting: "Отправляем заказ…",
  processing: "Lumean озвучивает текст…",
  failed: "Заказ завершился без готовой дорожки.",
  uncertain:
    "Ответ на отправку потерян. Перед повторной оплатой сверьте номер заказа в Lumean.",
  expired: "Срок хранения аудио в Lumean истёк.",
  completed: "Озвучка готова",
};

function Recording({ voice, id }: { voice: string; id: string }) {
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
        {error || (result ? labels[result.status] : "Проверяем заказ…")}
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
            Открыть аудиофайл
          </a>
        </>
      )}
      {(error || result?.url) && (
        <button
          className={secondaryButton}
          onClick={() => setAttempt(attempt + 1)}
        >
          Обновить результат
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
          Текст озвучки
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
          {text.length} / 4000 символов · Eleven Multilingual v2
        </small>
        <button
          className={primaryButton}
          disabled={pending || !text.trim() || text.length > 4000}
        >
          {pending ? "Отправляем…" : "Озвучить за счёт баланса Lumean"}
        </button>
      </form>
      {error && <p role="alert">{error}</p>}
      {ids.length > 0 && (
        <label className={fieldLabel}>
          Последние заказы
          <select
            className={field}
            value={selected}
            onChange={(e) => setSelected(e.target.value)}
          >
            <option value="">Выбрать заказ</option>
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
