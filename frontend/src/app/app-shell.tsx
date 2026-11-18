"use client";

import { formError } from "@/app/ui-styles";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useEffect, useState, useSyncExternalStore, useTransition } from "react";

import { logoutAction } from "./login/actions";

const themeKey = "sazi-content-theme";
const themeEvent = "mill-theme-change";

function subscribeToTheme(callback: () => void) {
  window.addEventListener(themeEvent, callback);
  window.addEventListener("storage", callback);
  return () => {
    window.removeEventListener(themeEvent, callback);
    window.removeEventListener("storage", callback);
  };
}

function getTheme(): "light" | "dark" {
  return localStorage.getItem(themeKey) === "dark" ? "dark" : "light";
}

const navigation = [
  { label: "Главная", icon: "home", href: "/" },
  { label: "Проекты", icon: "brand", href: "/projects" },
  { label: "База знаний", icon: "brand", href: "/knowledge" },
  { label: "Контент", icon: "videos", href: null },
] as const;

export function AppShell({ children, userName, section = "Главная" }: { children: React.ReactNode; userName: string; section?: string }) {
  const projectId = useParams().id;
  const theme = useSyncExternalStore(subscribeToTheme, getTheme, () => "light");
  const [menuOpen, setMenuOpen] = useState(false);
  const [logoutError, setLogoutError] = useState("");
  const [logoutPending, startLogout] = useTransition();

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  function toggleTheme() {
    const nextTheme = theme === "light" ? "dark" : "light";
    document.documentElement.dataset.theme = nextTheme;
    localStorage.setItem(themeKey, nextTheme);
    window.dispatchEvent(new Event(themeEvent));
  }

  return (
    <div className="min-h-screen">
      <a
        className="fixed -top-[60px] left-3 z-30 rounded-lg bg-surface px-3 py-[9px] text-ink focus:top-3"
        href="#main-content"
      >
        Перейти к содержимому
      </a>
      {menuOpen && (
        <button
          aria-label="Закрыть меню"
          className="fixed inset-0 z-10 hidden bg-[#08152885] max-[761px]:block"
          onClick={() => setMenuOpen(false)}
          type="button"
        />
      )}
      <aside
        aria-label="Основная навигация"
        className={`fixed inset-y-0 left-0 z-20 flex w-[226px] flex-col border-r border-line bg-sidebar px-[18px] py-[26px] max-[761px]:w-[260px] max-[761px]:transition-[transform,visibility] max-[761px]:duration-200 motion-reduce:transition-none ${menuOpen ? "" : "max-[761px]:invisible max-[761px]:-translate-x-full"}`}
        id="main-navigation"
        onKeyDown={(event) => {
          if (event.key === "Escape") setMenuOpen(false);
        }}
      >
        <Link
          className="mx-[9px] flex w-fit items-center gap-2.5 text-[28px] leading-none font-extrabold tracking-[-.06em]"
          href="/"
          onClick={() => setMenuOpen(false)}
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img alt="" height="33" src="/mill-logo.png" width="33" />
          <span>
            mill<small className="ml-1 text-[13px] font-medium tracking-normal text-muted">studio</small>
          </span>
        </Link>
        <p className="mx-[11px] mt-9 mb-[13px] text-[10px] font-bold tracking-[.1em] text-faint uppercase">
          Рабочее пространство
        </p>
        <nav className="grid gap-[5px]" aria-label="Разделы">
          {navigation.map(({ label, icon, href }) => {
            const content = (
              <>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img alt="" height="26" src={`/icons/${icon}.png`} width="26" />
                <span>{label}</span>
                {!href && <small className="ml-auto text-[9px] font-medium text-faint">Скоро</small>}
              </>
            );
            return href ? (
              <Link
                aria-current={section === label ? "page" : undefined}
                className="flex min-h-11 items-center gap-[11px] rounded-[10px] px-[11px] py-2 font-semibold text-muted aria-[current=page]:bg-selected aria-[current=page]:text-selected-ink aria-[current=page]:[&_img]:brightness-0 aria-[current=page]:[&_img]:invert [&:not([aria-current]):hover]:bg-control [&:not([aria-current]):hover]:text-ink"
                href={href === "/knowledge" && projectId ? `/projects/${projectId}/knowledge` : href}
                key={label}
                onClick={() => setMenuOpen(false)}
              >
                {content}
              </Link>
            ) : (
              <span
                className="flex min-h-11 items-center gap-[11px] rounded-[10px] px-[11px] py-2 font-semibold text-muted cursor-default opacity-[.66]"
                key={label}
              >
                {content}
              </span>
            );
          })}
        </nav>
        <div className="mt-auto border-t border-line px-[11px] pt-4 text-[11px] text-faint">
          <span className="block truncate font-bold text-ink">{userName}</span>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              startLogout(async () => setLogoutError(await logoutAction()));
            }}
          >
            <button className="mt-[9px] py-1 font-bold text-accent" disabled={logoutPending} type="submit">
              {logoutPending ? "Выходим…" : "Выйти"}
            </button>
          </form>
          {logoutError && (
            <p aria-live="polite" className={formError} role="alert">
              {logoutError}
            </p>
          )}
        </div>
      </aside>
      <div className="ml-[226px] min-h-screen max-[761px]:ml-0">
        <header className="flex min-h-[73px] items-center justify-between gap-4 border-b border-line px-[38px] max-[761px]:px-5">
          <div className="flex items-center gap-3">
            <button
              aria-controls="main-navigation"
              aria-expanded={menuOpen}
              className="hidden max-[761px]:inline-flex items-center justify-center min-h-[38px] gap-[7px] px-[11px] py-1.5 rounded-[9px] border border-line bg-control text-ink text-[11px] font-bold hover:bg-subtle"
              onClick={() => setMenuOpen(!menuOpen)}
              type="button"
            >
              Меню
            </button>
            <span className="text-xs text-muted">
              mill <span aria-hidden="true">/</span> <strong className="text-ink">{section}</strong>
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span className="rounded-[7px] border border-line px-[9px] py-[5px] text-[10px] whitespace-nowrap text-muted max-[561px]:hidden">
              Разработка первого этапа
            </span>
            <button
              aria-label={theme === "light" ? "Включить тёмную тему" : "Включить светлую тему"}
              aria-pressed={theme === "dark"}
              className="inline-flex items-center justify-center min-h-[38px] gap-[7px] px-[11px] py-1.5 rounded-[9px] border border-line bg-control text-ink text-[11px] font-bold hover:bg-subtle"
              onClick={toggleTheme}
              type="button"
            >
              {theme === "light" ? "☾ Тёмная" : "☀ Светлая"}
            </button>
          </div>
        </header>
        {children}
      </div>
    </div>
  );
}
