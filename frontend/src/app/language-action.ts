"use server";

import { cookies } from "next/headers";
import { isInterfaceLanguage, languageCookie, languageCookieOptions, type InterfaceLanguage } from "@/lib/interface-language";

export async function selectInterfaceLanguage(language: InterfaceLanguage) {
  if (!isInterfaceLanguage(language)) throw new Error("Unsupported interface language");
  (await cookies()).set(languageCookie, language, languageCookieOptions);
}
