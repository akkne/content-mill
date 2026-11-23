"use client";
import { useTranslator } from "@/app/interface-language";

import { field, formError, primaryButton } from "@/app/ui-styles";
import { useActionState } from "react";

import { loginAction, ownerSetupAction, registerAction } from "./actions";

export function LoginForm({ register, ownerSetup = false }: { register: boolean; ownerSetup?: boolean }) {
  const t = useTranslator();
  const newPassword = register || ownerSetup;
  async function submitOwner(_: string, data: FormData) {
    const token = window.location.hash.slice(1);
    if (!/^[A-Za-z0-9_-]{43}$/.test(token)) return t("Открой полную ссылку владельца.", "Open your complete owner setup link.");
    data.set("token", token);
    return ownerSetupAction(data);
  }
  const [error, action, pending] = useActionState(ownerSetup ? submitOwner : register ? registerAction : loginAction, "");

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
        autoComplete={newPassword ? "new-password" : "current-password"}
        minLength={newPassword ? 8 : undefined}
        maxLength={1024}
        aria-describedby={newPassword ? "password-hint" : undefined}
        id="password"
        name="password"
        required
        type="password"
      />
      {newPassword && <p className="text-sm text-muted" id="password-hint">{t("Минимум 8 символов", "At least 8 characters")}</p>}
      {error && (
        <p aria-live="polite" className={formError} role="alert">
          {error}
        </p>
      )}
      <button className={`${primaryButton} mt-[15px]`} disabled={pending} type="submit">
        {ownerSetup ? t("Сохранить и войти", "Save and sign in") : register ? (pending ? t("Создаём аккаунт…", "Creating account…") : t("Создать аккаунт", "Create account")) : (pending ? t("Входим…", "Signing in…") : t("Войти", "Sign in"))}
      </button>
    </form>
  );
}
