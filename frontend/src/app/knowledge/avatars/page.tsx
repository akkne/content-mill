import { getTranslator } from "@/lib/server-language";
import { LibraryIllustration } from "../library-illustration";
import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { AppShell } from "@/app/app-shell";
import { backLink, content } from "@/app/ui-styles";
import { fetchCurrentUser } from "@/lib/backend";
import { accessCookie } from "@/lib/session";

export default async function AvatarsPage() {
  const t = await getTranslator();
  const token = (await cookies()).get(accessCookie)?.value;
  const user = token && await fetchCurrentUser(token);
  if (!user) redirect("/login");

  return (
    <AppShell userName={user.display_name} section="База знаний">
      <main className={content} id="main-content">
        <Link className={backLink} href="/knowledge">{t("← База знаний", "← Knowledge base")}</Link>
        <header className="flex items-center justify-between gap-4 overflow-hidden rounded-[22px] border border-line bg-hero px-6 py-8 shadow-panel sm:px-9">
          <div>
            <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">{t("Аватары", "Avatars")}</h1>
            <p className="mt-3 text-sm leading-relaxed text-muted">{t("Личная библиотека аватаров в разработке.", "Your avatar library is in development.")}</p>
          </div>
          <LibraryIllustration kind="avatar" />
        </header>
      </main>
    </AppShell>
  );
}
