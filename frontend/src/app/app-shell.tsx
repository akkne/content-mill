"use client";

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
    <div className="app-shell">
      <a className="skip-link" href="#main-content">Перейти к содержимому</a>
      {menuOpen && (
        <button
          aria-label="Закрыть меню"
          className="menu-backdrop"
          onClick={() => setMenuOpen(false)}
          type="button"
        />
      )}
      <aside aria-label="Основная навигация" className={`sidebar ${menuOpen ? "sidebar-open" : ""}`} id="main-navigation" onKeyDown={(event) => { if (event.key === "Escape") setMenuOpen(false); }}>
        <Link className="brand" href="/" onClick={() => setMenuOpen(false)}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img alt="" height="33" src="/mill-logo.png" width="33" />
          <span>mill<small>studio</small></span>
        </Link>
        <p className="workspace-label">Рабочее пространство</p>
        <nav aria-label="Разделы">
          {navigation.map(({ label, icon, href }) => {
            const content = (
              <>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img alt="" height="26" src={`/icons/${icon}.png`} width="26" />
                <span>{label}</span>
                {!href && <small>Скоро</small>}
              </>
            );
            return href ? (
              <Link aria-current={section === label ? "page" : undefined} className="nav-item" href={href === "/knowledge" && projectId ? `/projects/${projectId}/knowledge` : href} key={label} onClick={() => setMenuOpen(false)}>{content}</Link>
            ) : (
              <span className="nav-item nav-item-disabled" key={label}>{content}</span>
            );
          })}
        </nav>
        <div className="sidebar-foot">
          <span>{userName}</span>
          <form onSubmit={(event) => {
            event.preventDefault();
            startLogout(async () => setLogoutError(await logoutAction()));
          }}>
            <button className="logout-button" disabled={logoutPending} type="submit">{logoutPending ? "Выходим…" : "Выйти"}</button>
          </form>
          {logoutError && <p aria-live="polite" className="form-error" role="alert">{logoutError}</p>}
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="topbar-actions">
            <button
              aria-controls="main-navigation"
              aria-expanded={menuOpen}
              className="menu-button"
              onClick={() => setMenuOpen(!menuOpen)}
              type="button"
            >
              Меню
            </button>
            <span className="topbar-title">mill <span aria-hidden="true">/</span> <strong>{section}</strong></span>
          </div>
          <div className="topbar-actions">
            <span className="stage-badge">Разработка первого этапа</span>
            <button
              aria-label={theme === "light" ? "Включить тёмную тему" : "Включить светлую тему"}
              aria-pressed={theme === "dark"}
              className="theme-button"
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
