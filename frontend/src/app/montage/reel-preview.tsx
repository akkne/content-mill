"use client";
import { useEffect, useRef, useState } from "react";
import { useInterfaceLanguage, useTranslator } from "../interface-language";
import type { MotionStyle, ReelFormat } from "@/lib/motion";

export function ReelPreview({
  reel,
  insert,
  outro,
  title,
  layout = "panel",
  origin,
}: {
  reel: ReelFormat;
  insert?: MotionStyle;
  outro?: MotionStyle;
  title?: string;
  layout?: string;
  origin?: string;
}) {
  const lang = useInterfaceLanguage(),
    t = useTranslator();
  const video = useRef<HTMLVideoElement>(null);
  const frame = useRef<HTMLIFrameElement>(null);
  const endFrame = useRef<HTMLIFrameElement>(null);
  const [atEnd, setAtEnd] = useState(false);
  const [active, setActive] = useState(false);
  const [error, setError] = useState(false);
  const start = layout === "intro" ? 0 : reel.duration * 0.4;
  useEffect(() => {
    const player = video.current;
    if (!player) return;
    let raf = 0;
    function sync() {
      const elapsed = (player?.currentTime ?? 0) - start;
      const visible =
        !!insert && elapsed >= 0 && elapsed < Math.min(insert.duration, 3);
      const endLength = Math.min(outro?.duration ?? 0, 3),
        endTime = (player?.currentTime ?? 0) - (reel.duration - endLength);
      const endVisible = !!outro && endTime >= 0 && endTime <= endLength;
      setAtEnd(endVisible);
      if (endVisible)
        endFrame.current?.contentWindow?.postMessage(
          { type: "motion-demo:seek", time: endTime },
          "*",
        );
      setActive(visible);
      if (visible)
        frame.current?.contentWindow?.postMessage(
          { type: "motion-demo:seek", time: elapsed },
          "*",
        );
    }
    function tick() {
      sync();
      if (!player?.paused && !player?.ended) raf = requestAnimationFrame(tick);
    }
    function play() {
      cancelAnimationFrame(raf);
      tick();
    }
    function message(e: MessageEvent) {
      if (e.data?.type !== "motion-demo:ready") return;
      for (const [target, style] of [
        [frame.current, insert],
        [endFrame.current, outro],
      ] as const) {
        if (style && target?.contentWindow === e.source)
          target.contentWindow?.postMessage(
            {
              type: "motion-demo:params",
              values: {
                title: (title || reel[lang].title).slice(0, 60),
                accent: style.accent,
              },
            },
            "*",
          );
      }
      sync();
    }
    player.addEventListener("play", play);
    player.addEventListener("seeked", sync);
    player.addEventListener("loadedmetadata", sync);
    window.addEventListener("message", message);
    for (const target of [frame.current, endFrame.current])
      target?.contentWindow?.postMessage({ type: "motion-demo:init" }, "*");
    play();
    return () => {
      cancelAnimationFrame(raf);
      player.removeEventListener("play", play);
      player.removeEventListener("seeked", sync);
      player.removeEventListener("loadedmetadata", sync);
      window.removeEventListener("message", message);
    };
  }, [insert, outro, title, start, lang, reel]);
  const split = active && layout === "split";
  return (
    <div className="mx-auto w-full max-w-64">
      <div className="relative aspect-[9/16] overflow-hidden rounded-xl bg-black">
        <video
          key={reel.id + lang}
          ref={video}
          playsInline
          controls
          preload="none"
          poster={`/reels/${reel.id}-${lang}.jpg`}
          aria-label={
            t("Пример монтажа", "Sample reel") + " · " + reel[lang].title
          }
          className={
            "h-full w-full " + (split ? "object-contain" : "object-cover")
          }
          style={
            split
              ? {
                  objectFit: "cover",
                  objectPosition: "center",
                  paddingBottom: "78%",
                }
              : undefined
          }
          src={`/reels/${reel.id}-${lang}.mp4`}
          onError={() => setError(true)}
          onLoadedData={() => setError(false)}
        />
        {insert && (
          <iframe
            ref={frame}
            title={insert[lang].title}
            sandbox="allow-scripts"
            tabIndex={-1}
            aria-hidden="true"
            onLoad={() =>
              frame.current?.contentWindow?.postMessage(
                { type: "motion-demo:init" },
                "*",
              )
            }
            src={`${origin}/api/template-source/${insert.id}/demos/sequence.html`}
            className={
              "pointer-events-none absolute border-0 " +
              (!active ? "invisible " : "") +
              (layout === "intro"
                ? "inset-0 h-[90%] w-full bg-black"
                : layout === "split"
                  ? "top-[56%] h-[40%] w-full"
                  : "left-[5%] top-[54%] h-[32%] w-[90%] rounded-lg")
            }
          />
        )}
        {outro && (
          <iframe
            ref={endFrame}
            title={
              t("Финальная вставка", "Closing insert") +
              " · " +
              outro[lang].title
            }
            sandbox="allow-scripts"
            tabIndex={-1}
            aria-hidden="true"
            onLoad={() =>
              endFrame.current?.contentWindow?.postMessage(
                { type: "motion-demo:init" },
                "*",
              )
            }
            src={`${origin}/api/template-source/${outro.id}/demos/sequence.html`}
            className={
              "pointer-events-none absolute left-[5%] top-[47%] h-[32%] w-[90%] rounded-lg border-0 " +
              (atEnd ? "" : "invisible")
            }
          />
        )}
      </div>
      {(insert || outro) && (
        <div className="mt-2 flex flex-wrap justify-center gap-2 text-xs">
          {[
            [t("Начало", "Start"), 0],
            ...(insert ? [[t("Основная вставка", "Main insert"), start]] : []),
            ...(outro
              ? [
                  [
                    t("Финал", "Closing"),
                    reel.duration - Math.min(outro.duration, 3),
                  ],
                ]
              : []),
          ].map(([label, at]) => (
            <button
              type="button"
              key={label}
              className="rounded-full border border-line px-2 py-1"
              onClick={() => {
                const player = video.current;
                if (player) {
                  player.currentTime = Number(at) + 0.05;
                  void player.play().catch(() => {});
                }
              }}
            >
              {label} · 0:{String(Math.floor(Number(at))).padStart(2, "0")}
            </button>
          ))}
        </div>
      )}
      {error && (
        <p role="alert">
          {t(
            "Не удалось загрузить пример рилса.",
            "Could not load the sample reel.",
          )}
        </p>
      )}
    </div>
  );
}
