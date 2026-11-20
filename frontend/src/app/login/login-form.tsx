"use client";
import { useTranslator } from "@/app/interface-language";

import { field, formError, primaryButton } from "@/app/ui-styles";
import { useActionState } from "react";

import { loginAction, registerAction } from "./actions";

export function LoginForm({ register }: { register: boolean }) {
  const t = useTranslator();
  const [error, action, pending] = useActionState(register ? registerAction : loginAction, "");

  return (
    <form action={action} className="grid gap-2">
      {register && (
        <>
          <label className="mt-[9px] font-bold" htmlFor="display_name">{t("Ваше имя", "Your name")}</label>
          <input className={`${field} min-h-11`} autoComplete="name" id="display_name" name="display_name" maxLength={120} required />
        </>
      )}
      <label className="mt-[9px] font-bold" htmlFor="email">
        {t("Электронная почта", "Email address")}
      </label>
      <input
        className={`${field} min-h-11`}
        autoComplete="username"
        id="email"
        name="email"
        required
        type="email"
      />
      <label className="mt-[9px] font-bold" htmlFor="password">
        {t("Пароль", "Password")}
      </label>
      <input
        className={`${field} min-h-11`}
        autoComplete={register ? "new-password" : "current-password"}
        minLength={register ? 15 : undefined}
        maxLength={1024}
        aria-describedby={register ? "password-hint" : undefined}
        id="password"
        name="password"
        required
        type="password"
      />
      {register && <p className="text-sm text-muted" id="password-hint">{t("Минимум 15 символов", "At least 15 characters")}</p>}
      {error && (
        <p aria-live="polite" className={formError} role="alert">
          {error}
        </p>
      )}
      <button className={`${primaryButton} mt-[15px]`} disabled={pending} type="submit">
        {register ? (pending ? t("Создаём аккаунт…", "Creating account…") : t("Создать аккаунт", "Create account")) : (pending ? t("Входим…", "Signing in…") : t("Войти", "Sign in"))}
      </button>
    </form>
  );
}
