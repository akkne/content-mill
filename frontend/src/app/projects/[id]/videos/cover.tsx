export const statuses: Record<string, string> = {
  all: "Все",
  generating: "В работе",
  ready: "Готовы",
  planned: "В плане",
  published: "Опубликованы",
  draft: "Черновики",
};

export const badge: Record<string, string> = {
  generating: "В работе",
  ready: "Готов",
  planned: "В плане",
  published: "Опубликован",
  draft: "Черновик",
};

export function Cover({
  title,
  project,
  duration,
  large = false,
}: {
  title: string;
  project: string;
  duration: number;
  large?: boolean;
}) {
  return (
    <div
      aria-hidden="true"
      className={`relative isolate flex flex-col justify-between overflow-hidden rounded-xl bg-linear-to-br from-[#1d3761] to-[#2455a2] p-5 text-[#edf5ff] ${large ? "mx-auto aspect-[9/16] w-full max-w-80" : "h-[260px] max-sm:h-48 min-[1500px]:h-[330px]"}`}
    >
      <div className="flex justify-between gap-2 text-xs">
        <b className="truncate lowercase">{project}.</b>
        <span className="rounded bg-black/30 px-2">
          {Math.floor(duration / 60)}:{String(duration % 60).padStart(2, "0")}
        </span>
      </div>
      <div className="absolute -right-14 top-1/3 -z-10 size-40 rounded-full border-[24px] border-white/10" />
      <strong className="mt-auto mb-5 line-clamp-5 text-2xl leading-tight break-words">
        {title || "Новый ролик"}
      </strong>
      <div className="flex items-center justify-between gap-2 text-[9px] tracking-widest">
        СЦЕНАРИЙ · РОЛИК · ПУБЛИКАЦИЯ{" "}
        <span className="rounded-full bg-white/15 p-2">▶</span>
      </div>
    </div>
  );
}
