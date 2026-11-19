import Link from "next/link";
import {
  pageTitle,
  pageLead,
  primaryButton,
  field,
  workPanel,
} from "@/app/ui-styles";
import { loadVideos, type VideoCard } from "@/lib/videos";
import { Cover, statuses, badge } from "./cover";

export default async function Library({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ q?: string; status?: string }>;
}) {
  const { id } = await params;
  const query = await searchParams;
  const status = Object.hasOwn(statuses, query.status ?? "")
    ? query.status!
    : "all";
  const q = (query.q ?? "").slice(0, 180);
  const base = `/projects/${id}/videos`;
  const { project, items } = await loadVideos<{
    project: string;
    items: VideoCard[];
  }>(id, "?" + new URLSearchParams({ status, q }));
  return (
    <>
      <Link className="text-sm text-accent" href="/videos">
        {project} · Сменить проект
      </Link>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className={pageTitle}>Ролики</h1>
        <Link className={primaryButton} href={base + "/new"}>
          ＋ Создать ролик
        </Link>
      </div>
      <p className={pageLead}>
        Здесь собраны черновики, ролики в работе и готовые публикации.
      </p>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <nav
          aria-label="Статус ролика"
          className="flex flex-wrap gap-1 rounded-xl border border-line bg-surface p-1"
        >
          {Object.entries(statuses).map(([key, label]) => (
            <Link
              key={key}
              aria-current={status === key ? "page" : undefined}
              className="rounded-lg px-3 py-2 font-semibold text-muted aria-current:bg-selected aria-current:text-selected-ink"
              href={base + "?" + new URLSearchParams({ status: key, q })}
            >
              {label}
            </Link>
          ))}
        </nav>
        <form className="flex items-center gap-2">
          <input type="hidden" name="status" value={status} />
          <input
            key={q}
            className={field}
            type="search"
            name="q"
            maxLength={180}
            defaultValue={q}
            placeholder="Найти ролик"
            aria-label="Найти ролик"
          />
          <button className="text-accent">Найти</button>
        </form>
      </div>
      {items.length ? (
        <div className="grid grid-cols-2 gap-x-4 gap-y-6 max-[420px]:grid-cols-1 lg:grid-cols-3 xl:grid-cols-4">
          {items.map((v) => (
            <Link key={v.id} href={base + "/" + v.id} className="group min-w-0">
              <Cover project={project} title={v.title} duration={v.duration} />
              <h2 className="mt-3 truncate font-bold group-hover:text-accent">
                {v.title}
              </h2>
              <p className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted">
                <span className="rounded-full bg-selected px-2 py-1 text-selected-ink">
                  {badge[v.status]}
                </span>
                {v.platform} ·{" "}
                {new Date(v.created_at).toLocaleDateString("ru", {
                  day: "numeric",
                  month: "short",
                  timeZone: "Europe/Moscow",
                })}
              </p>
            </Link>
          ))}
        </div>
      ) : (
        <p className={workPanel + " text-center text-muted"}>
          Пока нет роликов с такими параметрами. Измените фильтр или создайте
          новый.
        </p>
      )}
    </>
  );
}
