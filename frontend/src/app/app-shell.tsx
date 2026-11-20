"use client";

import { formError } from "@/app/ui-styles";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  useEffect,
  useState,
  useSyncExternalStore,
  useTransition,
} from "react";

import { WorkspaceIcon } from "./workspace-icon";
import { useInterfaceLanguage } from "./interface-language";
import { selectInterfaceLanguage } from "./language-action";
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
  ["Главная", "Home", "home", "/"],
  ["Проекты", "Projects", "brand", "/projects"],
  ["База знаний", "Knowledge base", "brand", "/knowledge"],
  ["Ролики", "Videos", "videos", "/videos"],
  ["План и автопилот", "Plan and autopilot", "plan", null],
  ["Аналитика", "Analytics", "analytics", null],
  ["Агент-маркетолог", "Marketing agent", "agent", null],
  ["Анализ ниши", "Niche analysis", "niche", null],
  ["Instagram-студия", "Instagram studio", "studio", null],
  ["Каналы и API", "Channels and API", "channels", null],
  ["Заявки (команда)", "Team leads", "leads", null],
  ["Проверка API", "API checks", "checks", null],
] as const;

export function AppShell({
  children,
  userName,
  section = "Главная",
}: {
  children: React.ReactNode;
  userName: string;
  section?: string;
}) {
  const language = useInterfaceLanguage();
  const english = language === "en";
  const [changingLanguage, startLanguageChange] = useTransition();
  const t = (ru: string, en: string) => (english ? en : ru);
  const pending = t("Ещё не реализовано", "Not yet implemented");
  const home = section === "Главная";
  const projectId = useParams().id;
  const theme = useSyncExternalStore(subscribeToTheme, getTheme, () => "light");
  const [menuOpen, setMenuOpen] = useState(false);
  const [logoutError, setLogoutError] = useState("");
  const [logoutPending, startLogout] = useTransition();

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  function chooseTheme(nextTheme: "light" | "dark") {
    localStorage.setItem(themeKey, nextTheme);
    window.dispatchEvent(new Event(themeEvent));
  }

  return (
    <div lang={english ? "en" : "ru"} className="min-h-screen">
      <a
        className="fixed -top-[60px] left-3 z-30 rounded-lg bg-surface px-3 py-[9px] text-ink focus:top-3"
        href="#main-content"
      >
        {t("Перейти к содержимому", "Skip to content")}
      </a>
      {menuOpen && (
        <button
          aria-label={t("Закрыть меню", "Close menu")}
          className="fixed inset-0 z-10 hidden bg-[#08152885] max-[761px]:block"
          onClick={() => setMenuOpen(false)}
          type="button"
        />
      )}
      <aside
        aria-label={t("Основная навигация", "Main navigation")}
        className={`fixed inset-y-0 left-0 z-20 flex w-[242px] max-[1150px]:w-[224px] flex-col border-r border-line bg-sidebar px-[18px] pt-5 pb-3 max-[761px]:w-[246px] max-[761px]:transition-[transform,visibility] max-[761px]:duration-200 motion-reduce:transition-none ${menuOpen ? "" : "max-[761px]:invisible max-[761px]:-translate-x-full"}`}
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
          <img alt="" height="54" src="/mill-logo.png" width="54" />
          mill
        </Link>
        <p className="mx-[11px] mt-3 text-[10px] font-bold tracking-widest text-faint">
          {t("КОНТЕНТ-ЗАВОД", "CONTENT FACTORY")}
        </p>
        <Link
          href={projectId ? `/projects/${projectId}/videos/new` : "/videos?create=1"}
          className="mt-4 rounded-[10px] bg-action px-3 py-2 font-bold text-white"
        >
          ＋ {t("Создать ролик", "Create video")}
        </Link>
        <p className="mx-[11px] mt-5 mb-2 text-[10px] font-bold tracking-[.1em] text-faint uppercase">
          {t("Рабочее пространство", "Workspace")}
        </p>
        <nav
          className="grid min-h-0 content-start gap-0.5 overflow-y-auto"
          aria-label={t("Разделы", "Sections")}
        >
          {navigation.map(([label, en, icon, href]) => {
            const content = (
              <>
                <WorkspaceIcon
                  name={icon}
                  className={`size-[29px] ${section === label ? "rounded-lg bg-white" : ""}`}
                />
                <span>
                  {t(label, en)}
                  {!href && (
                    <small className="block text-[10px] font-medium text-muted">
                      {pending}
                    </small>
                  )}
                </span>
              </>
            );
            return href ? (
              <Link
                aria-current={section === label ? "page" : undefined}
                className="flex min-h-11 items-center gap-[11px] rounded-[10px] px-[11px] py-2 font-semibold text-muted aria-[current=page]:bg-selected aria-[current=page]:text-selected-ink [&:not([aria-current]):hover]:bg-control [&:not([aria-current]):hover]:text-ink"
                href={
                  (href === "/knowledge" || href === "/videos") && projectId
                    ? `/projects/${projectId}${href}`
                    : href
                }
                key={label}
                onClick={() => setMenuOpen(false)}
              >
                {content}
              </Link>
            ) : (
              <button
                disabled
                className="text-left disabled:cursor-default flex min-h-11 items-center gap-[11px] rounded-[10px] px-[11px] py-1 text-xs font-semibold text-muted"
                key={label}
              >
                {content}
              </button>
            );
          })}
        </nav>
        <div className="mt-auto shrink-0 border-t border-line pt-2 text-[11px] text-muted">
          <button
            disabled
            className="mb-2 flex w-full justify-between gap-2 border-b border-line px-2 pb-2 text-left disabled:cursor-default"
          >
            {t("Дизайн-система", "Design system")}
            <small>{pending}</small>
          </button>
          <div className="flex items-center gap-2 px-2">
            <span
              aria-hidden="true"
              className="grid size-8 shrink-0 place-items-center rounded-full bg-tint font-bold text-accent"
            >
              {userName.slice(0, 1)}
            </span>
            <strong className="mr-auto truncate text-ink">{userName}</strong>
            <form
              onSubmit={(event) => {
                event.preventDefault();
                startLogout(async () => setLogoutError(await logoutAction()));
              }}
            >
              <button
                className="mt-[9px] py-1 font-bold text-accent"
                disabled={logoutPending}
                type="submit"
              >
                {logoutPending
                  ? t("Выходим…", "Signing out…")
                  : t("Выйти", "Sign out")}
              </button>
            </form>
          </div>
          {logoutError && (
            <p aria-live="polite" className={formError} role="alert">
              {logoutError}
            </p>
          )}
        </div>
      </aside>
      <div className="ml-[242px] max-[1150px]:ml-[224px] flex min-h-screen flex-col max-[761px]:ml-0">
        <header className="flex min-h-[73px] items-center justify-between gap-4 border-b border-line px-[38px] max-[761px]:px-5">
          <div className="flex items-center gap-3">
            <button
              aria-controls="main-navigation"
              aria-expanded={menuOpen}
              className="hidden max-[761px]:inline-flex items-center justify-center min-h-[38px] gap-[7px] px-[11px] py-1.5 rounded-[9px] border border-line bg-control text-ink text-[11px] font-bold hover:bg-subtle"
              onClick={() => setMenuOpen(!menuOpen)}
              type="button"
            >
              {t("Меню", "Menu")}
            </button>
            <span className="text-xs text-muted">
              mill <span aria-hidden="true">/</span>{" "}
              <strong className="text-ink">
                {home ? t("Главная", "Home") : section}
              </strong>
            </span>
          </div>
          <div className="flex items-center gap-3">
            <div role="group" aria-label={t("Язык интерфейса", "Interface language")} className="flex gap-1 rounded-[9px] border border-line bg-control p-1">
              {(["ru", "en"] as const).map(choice => (
                <button
                  key={choice}
                  type="button"
                  aria-pressed={language === choice}
                  disabled={changingLanguage}
                  onClick={() => startLanguageChange(() => selectInterfaceLanguage(choice))}
                  className="rounded-md px-2 py-1 text-[11px] font-bold text-muted aria-pressed:bg-surface aria-pressed:text-ink"
                >
                  {choice.toUpperCase()}
                </button>
              ))}
            </div>
            <div className="flex rounded-[9px] border border-line bg-control p-1">
              {(["light", "dark"] as const).map((choice) => {
                const label =
                  choice === "light"
                    ? t("Светлая", "Light")
                    : t("Тёмная", "Dark");
                return (
                  <button
                    key={choice}
                    type="button"
                    aria-label={label}
                    aria-pressed={theme === choice}
                    onClick={() => chooseTheme(choice)}
                    className="rounded-md px-2 py-1 text-xs font-semibold text-muted aria-pressed:bg-surface aria-pressed:text-ink"
                  >
                    {choice === "light" ? "☀" : "☾"}{" "}
                    <span className="max-[761px]:hidden">{label}</span>
                  </button>
                );
              })}
            </div>
            <span className="text-xs text-muted max-[1150px]:hidden">
              {new Intl.DateTimeFormat(english ? "en-GB" : "ru", {
                weekday: "long",
                month: "long",
                day: "numeric",
                timeZone: "Europe/Moscow",
              }).format(new Date())}
            </span>
            <span
              aria-hidden="true"
              className="grid size-8 place-items-center rounded-full bg-tint font-bold text-accent max-[761px]:hidden"
            >
              {userName.slice(0, 1)}
            </span>
          </div>
        </header>
        {children}
      </div>
    </div>
  );
}
