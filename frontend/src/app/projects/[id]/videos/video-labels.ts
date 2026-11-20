import type { Translate } from "@/lib/interface-language";

export const statuses = (t: Translate): Record<string, string> => ({
  all: t("Все", "All"),
  generating: t("В работе", "In progress"),
  ready: t("Готовы", "Ready"),
  planned: t("В плане", "Scheduled"),
  published: t("Опубликованы", "Published"),
  draft: t("Черновики", "Drafts"),
});

export const badge = (t: Translate): Record<string, string> => ({
  generating: t("В работе", "In progress"),
  ready: t("Готов", "Ready"),
  planned: t("В плане", "Scheduled"),
  published: t("Опубликован", "Published"),
  draft: t("Черновик", "Draft"),
});

const optionNames: Record<string, string> = {
  "Проблема → решение": "Problem → solution",
  "Доказательство": "Proof",
  "Обучение": "Tutorial",
  "Мнение": "Opinion",
  "История": "Story",
  "Оффер": "Offer",
  "VK Клипы": "VK Clips",
  "Русский": "Russian",
};

export function optionLabel(value: string | number, t: Translate) {
  if (value === "English") return t("Английский", "English");
  return t(String(value), optionNames[value] ?? String(value));
}
