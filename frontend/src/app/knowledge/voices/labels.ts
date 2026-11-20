import type { InterfaceLanguage } from "@/lib/interface-language";

const names = {
  ru: new Intl.DisplayNames(["ru"], { type: "language" }),
  en: new Intl.DisplayNames(["en"], { type: "language" }),
};
export function languageName(code: string, locale: InterfaceLanguage = "ru") {
  try {
    return names[locale].of(code) ?? code;
  } catch {
    return code;
  }
}
export function genderName(gender: string | null, locale: InterfaceLanguage = "ru") {
  if (locale === "en") return gender === "male" ? "Male" : gender === "female" ? "Female" : "—";
  return gender === "male" ? "Мужской" : gender === "female" ? "Женский" : "—";
}
export function languagesOf(voice: {
  voice_language: string | null;
  catalog_languages: string[] | null;
}) {
  return (
    [...new Set([voice.voice_language, ...(voice.catalog_languages ?? [])])]
      .filter((v): v is string => Boolean(v))
      .map(code => languageName(code))
      .join(", ") || "—"
  );
}
