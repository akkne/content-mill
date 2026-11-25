"use client";
import { useEffect, useRef, useState } from "react";
import type { MotionStyle } from "@/lib/motion";
import { useInterfaceLanguage, useTranslator } from "../interface-language";
import { secondaryButton } from "../ui-styles";

export function MotionPreview({
  style,
  origin,
}: {
  style: MotionStyle;
  origin: string;
}) {
  const frame = useRef<HTMLIFrameElement>(null);
  const [playing, play] = useState(false);
  const [ready, setReady] = useState(false);
  const [timedOut, setTimedOut] = useState(false);
  const [attempt, retry] = useState(0);
  const [time, seek] = useState(0);
  const at = useRef(0);
  const t = useTranslator();
  const lang = useInterfaceLanguage();
  useEffect(() => {
    function message(e: MessageEvent) {
      if (
        e.source === frame.current?.contentWindow &&
        e.data?.type === "motion-demo:ready"
      )
        setReady(true);
    }
    const timeout = window.setTimeout(() => setTimedOut(true), 12000);
    window.addEventListener("message", message);
    return () => {
      window.clearTimeout(timeout);
      window.removeEventListener("message", message);
    };
  }, [attempt]);
  useEffect(() => {
    if (!playing) return;
    let id = 0;
    const start = performance.now() - at.current * 1000;
    function tick(now: number) {
      const next = Math.min(style.duration, (now - start) / 1000);
      at.current = next;
      frame.current?.contentWindow?.postMessage(
        { type: "motion-demo:seek", time: next },
        "*",
      );
      seek(next);
      if (next < style.duration) id = requestAnimationFrame(tick);
      else play(false);
    }
    id = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(id);
  }, [playing, style.duration]);
  return (
    <div className="grid gap-2">
      <iframe
        key={attempt}
        ref={frame}
        title={style[lang].title}
        sandbox="allow-scripts"
        className="aspect-video w-full rounded-xl bg-black"
        src={`${origin}/api/template-source/${style.id}/demos/sequence.html`}
        onLoad={() =>
          frame.current?.contentWindow?.postMessage(
            { type: "motion-demo:init" },
            "*",
          )
        }
      />
      {!ready && (
        <div role="status" className="text-sm text-muted">
          {timedOut ? (
            <>
              <span>{t("Studio не ответила.", "Studio did not respond.")}</span>{" "}
              <button
                type="button"
                className="underline"
                onClick={() => {
                  setTimedOut(false);
                  retry((n) => n + 1);
                }}
              >
                {t("Повторить", "Retry")}
              </button>
            </>
          ) : (
            t("Загружаем анимацию…", "Loading animation…")
          )}
        </div>
      )}
      <div className="flex items-center gap-3">
        <button
          type="button"
          className={secondaryButton}
          disabled={!ready}
          onClick={() => {
            if (at.current >= style.duration) at.current = 0;
            play(!playing);
          }}
        >
          {playing ? t("Пауза", "Pause") : t("Воспроизвести", "Play")}
        </button>
        <input
          className="min-w-0 flex-1"
          aria-label={t("Позиция анимации", "Animation position")}
          type="range"
          disabled={!ready}
          min="0"
          max={style.duration}
          step=".05"
          value={time}
          onChange={(e) => {
            play(false);
            at.current = Number(e.target.value);
            seek(at.current);
            frame.current?.contentWindow?.postMessage(
              { type: "motion-demo:seek", time: at.current },
              "*",
            );
          }}
        />
        <span className="text-sm tabular-nums">
          {Math.floor(time)} / {Math.ceil(style.duration)} {t("с", "s")}
        </span>
      </div>
    </div>
  );
}
