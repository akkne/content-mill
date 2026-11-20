"use server";
import { getTranslator } from "@/lib/server-language";

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
  const t = await getTranslator();
  const email = String(formData.get("email") ?? "").trim();
  const password = String(formData.get("password") ?? "");
  if (!email || !password) return t("Введите почту и пароль", "Enter your email and password");

  const displayName = mode === "register" ? String(formData.get("display_name") ?? "").trim() : undefined;
  if (mode === "register" && !displayName) return t("Введите имя", "Enter your name");

  let response: Response;
  try {
    response = await fetch(backendUrl(`/api/v1/auth/${mode}`), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, display_name: displayName }),
      cache: "no-store",
    });
  } catch {
    return t("Сервер недоступен. Повторите попытку позже", "Server unavailable. Try again later");
  }
  if (response.status === 429) return t("Слишком много попыток. Повторите через 15 минут", "Too many attempts. Try again in 15 minutes");
  if (response.status === 401) return t("Неверная почта или пароль", "Incorrect email or password");
  if (response.status === 409) return t("Не удалось зарегистрировать эту почту. Попробуйте войти", "Could not register this email. Try signing in");
  if (response.status === 422) return t("Проверьте введённые данные", "Check the information you entered");
  if (!response.ok) return t("Сервер недоступен. Повторите попытку позже", "Server unavailable. Try again later");
  await setSession(await response.json() as TokenPair);
  redirect("/");
}

export async function logoutAction(): Promise<string> {
  const t = await getTranslator();
  const refreshToken = (await cookies()).get(refreshCookie)?.value;
  if (refreshToken) {
    try {
      const response = await fetch(backendUrl("/api/v1/auth/logout"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
        cache: "no-store",
      });
      if (!response.ok) return t("Не удалось завершить сессию. Повторите попытку", "Could not end the session. Try again");
    } catch {
      return t("Сервер недоступен. Повторите выход позже", "Server unavailable. Try signing out later");
    }
  }
  await clearSession();
  redirect("/login");
}
