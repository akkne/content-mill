const names = new Intl.DisplayNames(["ru"], { type: "language" });
export function languageName(code: string) {
  try {
    return names.of(code) ?? code;
  } catch {
    return code;
  }
}
export function genderName(gender: string | null) {
  return gender === "male" ? "Мужской" : gender === "female" ? "Женский" : "—";
}
export function languagesOf(voice: {
  voice_language: string | null;
  catalog_languages: string[] | null;
}) {
  return (
    [...new Set([voice.voice_language, ...(voice.catalog_languages ?? [])])]
      .filter((v): v is string => Boolean(v))
      .map(languageName)
      .join(", ") || "—"
  );
}
