import type { Translate } from "@/lib/interface-language";

export type SalesMode = "unassigned" | "saas" | "implementation";
export type ClientProject = {
  id: string; name: string; email: string; sales_mode: SalesMode;
  package_name: string; delivery_notes: string; video_style: string;
  video_duration: number; admin_revision: number; video_count: number;
};
export const modeLabels = (t: Translate) => ({
  saas: t("SaaS-подписка", "SaaS subscription"),
  implementation: t("Разовое внедрение", "One-time implementation"),
  unassigned: t("Не назначено", "Unassigned"),
});
