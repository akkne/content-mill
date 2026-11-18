"use client";

import { useEffect, useRef } from "react";

const eyes = [
  { x: 533, y: 565, rx: 82 },
  { x: 716, y: 562, rx: 80 },
];

export function OverviewMascot() {
  const svg = useRef<SVGSVGElement>(null);
  useEffect(() => {
    if (!svg.current) return;
    const element = svg.current;
    const pupils = Array.from(element.querySelectorAll("[data-pupil]"));
    const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const current = eyes.map(() => ({ x: 10, y: -10 }));
    let point: { x: number; y: number } | null = null;
    let visible = true,
      active = false,
      disposed = false;
    let frame = 0,
      previousTime = 0,
      blinkTimer = 0,
      openTimer = 0,
      touchTimer = 0;

    function paint() {
      pupils.forEach((pupil, i) =>
        pupil.setAttribute(
          "transform",
          `translate(${current[i].x.toFixed(2)} ${current[i].y.toFixed(2)})`,
        ),
      );
    }

    function stopFrame() {
      cancelAnimationFrame(frame);
      frame = 0;
      previousTime = 0;
    }

    function neutral() {
      point = null;
      if (active) requestFrame();
    }

    function tick(time: number) {
      frame = 0;
      if (!active || disposed) return;
      const rect = element.getBoundingClientRect();
      const blend =
        1 -
        Math.exp(-Math.min(previousTime ? time - previousTime : 16, 48) / 75);
      previousTime = time;
      let unsettled = false;
      eyes.forEach((eye, i) => {
        let target = { x: 10, y: -10 };
        if (point && rect.width && rect.height) {
          const dx = point.x - (rect.left + (eye.x / 1254) * rect.width);
          const dy = point.y - (rect.top + (eye.y / 1254) * rect.height);
          const distance = Math.hypot(dx, dy);
          const strength = Math.min(1, distance / 240);
          target = distance
            ? {
                x: (dx / distance) * 28 * strength,
                y: (dy / distance) * 37 * strength,
              }
            : { x: 0, y: 0 };
        }
        current[i].x += (target.x - current[i].x) * blend;
        current[i].y += (target.y - current[i].y) * blend;
        unsettled ||=
          Math.abs(target.x - current[i].x) +
            Math.abs(target.y - current[i].y) >
          0.08;
      });
      paint();
      if (unsettled) requestFrame();
      else previousTime = 0;
    }

    function requestFrame() {
      if (!frame && active && !disposed) frame = requestAnimationFrame(tick);
    }

    function scheduleBlink(first = false) {
      clearTimeout(blinkTimer);
      blinkTimer = window.setTimeout(
        () => {
          if (!active || disposed) return;
          element.classList.add("is-blinking");
          openTimer = window.setTimeout(() => {
            element.classList.remove("is-blinking");
            if (active) scheduleBlink();
          }, 220);
        },
        first ? 1600 + Math.random() * 1400 : 3200 + Math.random() * 3200,
      );
    }

    function sync() {
      const next = visible && !document.hidden && !motion.matches && !disposed;
      if (next === active) return;
      active = next;
      if (active) {
        scheduleBlink(true);
        requestFrame();
      } else {
        stopFrame();
        clearTimeout(blinkTimer);
        clearTimeout(openTimer);
        clearTimeout(touchTimer);
        element.classList.remove("is-blinking");
        point = null;
        current.forEach((p) => {
          p.x = 10;
          p.y = -10;
        });
        paint();
      }
    }

    function follow(event: PointerEvent) {
      if (!active || event.pointerType === "touch") return;
      point = { x: event.clientX, y: event.clientY };
      requestFrame();
    }

    function touch(event: PointerEvent) {
      if (!active || event.pointerType !== "touch") return;
      clearTimeout(touchTimer);
      point = { x: event.clientX, y: event.clientY };
      requestFrame();
      touchTimer = window.setTimeout(neutral, 1600);
    }

    function leave(event: PointerEvent) {
      if (event.pointerType !== "touch" && !event.relatedTarget) neutral();
    }
    const observer = new IntersectionObserver((entries) => {
      visible = entries[0].isIntersecting;
      sync();
    });
    observer.observe(element);
    document.addEventListener("pointermove", follow, { passive: true });
    document.addEventListener("pointerdown", touch, { passive: true });
    document.addEventListener("pointerout", leave, { passive: true });
    document.addEventListener("visibilitychange", sync);
    window.addEventListener("blur", neutral);
    motion.addEventListener("change", sync);
    sync();

    return () => {
      disposed = true;
      active = false;
      stopFrame();
      clearTimeout(blinkTimer);
      clearTimeout(openTimer);
      clearTimeout(touchTimer);
      observer.disconnect();
      document.removeEventListener("pointermove", follow);
      document.removeEventListener("pointerdown", touch);
      document.removeEventListener("pointerout", leave);
      document.removeEventListener("visibilitychange", sync);
      window.removeEventListener("blur", neutral);
      motion.removeEventListener("change", sync);
    };
  }, []);

  return (
    <svg
      ref={svg}
      aria-hidden="true"
      viewBox="0 0 1254 1254"
      className="group absolute -top-2 left-[34px] size-[240px] max-sm:left-1/2 max-sm:size-[230px] max-sm:-translate-x-1/2"
    >
      <defs>
        <mask
          id="flower-shape"
          maskUnits="userSpaceOnUse"
          width="1254"
          height="1254"
          style={{ maskType: "alpha" }}
        >
          <image href="/mill-mascot.png" width="1254" height="1254" />
        </mask>
        <linearGradient id="flower-blue" x2="1" y2="1">
          <stop stopColor="#2563eb" />
          <stop offset="1" stopColor="#2452e8" />
        </linearGradient>
      </defs>
      <rect
        width="1254"
        height="1254"
        mask="url(#flower-shape)"
        fill="url(#flower-blue)"
      />
      {eyes.map(({ x, y, rx }) => (
        <g key={x}>
          <g className="origin-center [transform-box:fill-box] motion-safe:group-[.is-blinking]:animate-[flower-blink_220ms_ease-in-out_both]">
            <ellipse cx={x} cy={y} rx={rx} ry="99" fill="white" />
            <g data-pupil="" transform="translate(10 -10)">
              <ellipse cx={x} cy={y} rx="37" ry="43" fill="#102650" />
            </g>
          </g>
          <path
            d={`M${x - 60} ${y} Q${x} ${y + 24} ${x + 60} ${y}`}
            fill="none"
            stroke="#102650"
            strokeWidth="10"
            strokeLinecap="round"
            className="opacity-0 motion-safe:group-[.is-blinking]:animate-[flower-close_220ms_ease-in-out_both]"
          />
        </g>
      ))}
    </svg>
  );
}
