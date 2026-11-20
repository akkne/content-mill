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

export type Translate = (ru: string, en: string) => string;

export function translator(language: InterfaceLanguage): Translate {
  return (ru, en) => language === "en" ? en : ru;
}
