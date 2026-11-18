"use client";

import { field, formError, primaryButton } from "@/app/ui-styles";
import { useActionState } from "react";

import { loginAction } from "./actions";

export function LoginForm() {
  const [error, action, pending] = useActionState(loginAction, "");

  return (
    <form action={action} className="grid gap-2">
      <label className="mt-[9px] font-bold" htmlFor="email">
        Электронная почта
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
        Пароль
      </label>
      <input
        className={`${field} min-h-11`}
        autoComplete="current-password"
        id="password"
        name="password"
        required
        type="password"
      />
      {error && (
        <p aria-live="polite" className={formError} role="alert">
          {error}
        </p>
      )}
      <button className={`${primaryButton} mt-[15px]`} disabled={pending} type="submit">
        {pending ? "Входим…" : "Войти"}
      </button>
    </form>
  );
}
