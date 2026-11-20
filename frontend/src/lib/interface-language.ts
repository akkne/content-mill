export type InterfaceLanguage = "ru" | "en";
export const languageCookie = "mill_language";

export function isInterfaceLanguage(value: unknown): value is InterfaceLanguage {
  return value === "ru" || value === "en";
}

export const languageCookieOptions = {
  path: "/",
  sameSite: "lax",
  httpOnly: true,
  maxAge: 365 * 24 * 60 * 60,
} as const;
