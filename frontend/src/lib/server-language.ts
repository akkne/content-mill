import { cookies } from "next/headers";
import { languageCookie, translator } from "./interface-language";

export async function getTranslator() {
  return translator((await cookies()).get(languageCookie)?.value === "en" ? "en" : "ru");
}
