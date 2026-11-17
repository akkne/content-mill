"use client";

import { useActionState } from "react";

import { loginAction } from "./actions";

export function LoginForm() {
  const [error, action, pending] = useActionState(loginAction, "");

  return (
    <form action={action} className="login-form">
      <label htmlFor="email">Электронная почта</label>
      <input autoComplete="username" id="email" name="email" required type="email" />
      <label htmlFor="password">Пароль</label>
      <input autoComplete="current-password" id="password" name="password" required type="password" />
      {error && <p aria-live="polite" className="form-error" role="alert">{error}</p>}
      <button className="primary-button" disabled={pending} type="submit">
        {pending ? "Входим…" : "Войти"}
      </button>
    </form>
  );
}
