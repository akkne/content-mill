import Link from "next/link";
import { cookies } from "next/headers";
import { notFound, redirect } from "next/navigation";
import { AppShell } from "../app-shell";
import { content, field, pageTitle, pageLead, secondaryButton } from "../ui-styles";
import { fetchCurrentUser } from "@/lib/backend";
import { projectRequest } from "@/lib/projects";
import { getTranslator } from "@/lib/server-language";
import { accessCookie } from "@/lib/session";
import { ClientEditor } from "./client-editor";
import { type ClientProject, type SalesMode, modeLabels } from "./types";

type Result = { items: ClientProject[]; totals: Partial<Record<SalesMode, number>>; durations: number[]; styles: string[] };

export default async function AdminPage({searchParams}: {
  searchParams: Promise<{ q?: string; mode?: string; page?: string }>;
}) {
  const token = (await cookies()).get(accessCookie)?.value;
  const user = token && await fetchCurrentUser(token);
  if (!user) redirect("/login");
  if (!user.is_admin) notFound();
  const t = await getTranslator();
  const labels = modeLabels(t);
  const params = await searchParams;
  const q = String(params.q ?? "").trim().slice(0,160);
  const mode = Object.hasOwn(labels, String(params.mode)) ? params.mode as SalesMode : "";
  const page = Math.min(1000000, Math.max(1, Math.floor(Number(params.page)) || 1));
  const size = 20;
  const query = new URLSearchParams({q, offset:String((page-1)*size), limit:String(size)});
  if (mode) query.set("mode",mode);
  const response = await projectRequest("/api/v1/admin/clients?" + query);
  if (response.status === 403) notFound();
  if (!response.ok) throw new Error(t("Не удалось загрузить клиентов","Could not load clients"));
  const {items, totals, durations, styles}: Result = await response.json();
  const count = Object.values(totals).reduce((sum,n) => sum+n,0);
  const available = mode ? totals[mode] ?? 0 : count;
  function href(filter: string, n = 1) {
    const search = new URLSearchParams();
    if(q) search.set("q",q);
    if(filter) search.set("mode",filter);
    if(n>1) search.set("page",String(n));
    return "/admin" + (search.size ? "?" + search : "");
  }
  return <AppShell userName={user.display_name} isAdmin section="Админ-панель">
    <main className={content} id="main-content">
      <h1 className={pageTitle}>{t("Клиентские проекты","Client projects")}</h1>
      <p className={pageLead}>{t("Условия сотрудничества и настройки производства по каждому проекту.", "Manage client agreements and video defaults for each project.")}</p>
      <form action="/admin" className="mb-4 flex max-w-xl gap-2">
        {mode && <input type="hidden" name="mode" value={mode}/>}
        <input name="q" type="search" className={field} maxLength={160} defaultValue={q} aria-label={t("Поиск по проекту или почте","Search by project or email")} placeholder={t("Название проекта или почта владельца","Project name or owner email")}/>
        <button className={secondaryButton}>{t("Найти","Search")}</button>
      </form>
      <nav className="mb-5 flex flex-wrap gap-2" aria-label={t("Модель продажи","Sales model")}>
        {Object.entries({"":t("Все проекты","All projects"),...labels}).map(([key,label])=><Link key={key} href={href(key)} aria-current={mode===key?"page":undefined}
          className={mode===key?"rounded-lg bg-action px-3 py-2 font-bold text-white":secondaryButton}>
          {label} · {key ? totals[key as SalesMode] ?? 0 : count}
        </Link>)}
      </nav>
      <div className="grid gap-3">
        {items.map(client=><details key={client.id} className="overflow-hidden rounded-2xl border border-line bg-surface shadow-panel">
          <summary className="flex cursor-pointer list-none flex-wrap items-center gap-4 px-5 py-4 sm:px-6">
            <span aria-hidden="true" className="grid size-10 place-items-center rounded-xl bg-tint font-extrabold text-accent">{client.name.slice(0,1).toUpperCase()}</span>
            <span className="min-w-0 grow"><strong className="block break-words text-base">{client.name}</strong><span className="break-all text-sm text-muted">{client.email}</span></span>
            <span className="rounded-lg bg-control px-2.5 py-1 text-sm">{labels[client.sales_mode]}</span>
            <span className="text-sm text-muted">{t("Ролики","Videos")} · {client.video_count}</span>
            <span aria-hidden="true" className="text-accent">⌄</span>
          </summary>
          <ClientEditor client={client} durations={durations} styles={styles}/>
        </details>)}
        {items.length===0 && <p className="rounded-xl border border-dashed border-line p-6 text-muted">{t("Проекты не найдены.","No matching projects.")}</p>}
      </div>
      <div className="mt-5 flex gap-3">
        {page>1 && <Link href={href(mode,page-1)} className={secondaryButton}>{t("← Назад","← Previous")}</Link>}
        {page*size<available && <Link href={href(mode,page+1)} className={secondaryButton}>{t("Дальше →","Next →")}</Link>}
      </div>
    </main>
  </AppShell>;
}
