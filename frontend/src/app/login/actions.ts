"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { backendUrl, type TokenPair } from "@/lib/backend";
import { clearSession, refreshCookie, setSession } from "@/lib/session";

export async function loginAction(_: string, formData: FormData): Promise<string> {
  return authenticate("login", formData);
}

export async function registerAction(_: string, formData: FormData): Promise<string> {
  return authenticate("register", formData);
}

async function authenticate(mode: "login" | "register", formData: FormData): Promise<string> {
  const email = String(formData.get("email") ?? "").trim();
  const password = String(formData.get("password") ?? "");
  if (!email || !password) return "Введите почту и пароль";

  const displayName = mode === "register" ? String(formData.get("display_name") ?? "").trim() : undefined;
  if (mode === "register" && !displayName) return "Введите имя";

  let response: Response;
  try {
    response = await fetch(backendUrl(`/api/v1/auth/${mode}`), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, display_name: displayName }),
      cache: "no-store",
    });
  } catch {
    return "Сервер недоступен. Повторите попытку позже";
  }
  if (response.status === 429) return "Слишком много попыток. Повторите через 15 минут";
  if (response.status === 401) return "Неверная почта или пароль";
  if (response.status === 409) return "Не удалось зарегистрировать эту почту. Попробуйте войти";
  if (response.status === 422) return "Проверьте введённые данные";
  if (!response.ok) return "Сервер недоступен. Повторите попытку позже";
  await setSession(await response.json() as TokenPair);
  redirect("/");
}

export async function logoutAction(): Promise<string> {
  const refreshToken = (await cookies()).get(refreshCookie)?.value;
  if (refreshToken) {
    try {
      const response = await fetch(backendUrl("/api/v1/auth/logout"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
        cache: "no-store",
      });
      if (!response.ok) return "Не удалось завершить сессию. Повторите попытку";
    } catch {
      return "Сервер недоступен. Повторите выход позже";
    }
  }
  await clearSession();
  redirect("/login");
}
