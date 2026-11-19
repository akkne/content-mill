import Link from "next/link";

const tile =
  "flex aspect-square w-full max-w-52 flex-col justify-between rounded-3xl border p-5 text-left sm:p-7";
export function LibraryTiles() {
  return (
    <div className="mt-7 grid max-w-[440px] grid-cols-2 gap-4">
      <Link
        href="/knowledge/voices"
        className={`${tile} border-line bg-tint text-accent hover:border-accent`}
      >
        <span aria-hidden className="flex h-12 items-center gap-1">
          {["h-3", "h-6", "h-10", "h-8", "h-5", "h-6", "h-2.5"].map(
            (height, i) => (
              <i
                key={i}
                className={`w-1.5 rounded-full bg-current ${height}`}
              />
            ),
          )}
        </span>
        <strong className="flex items-center justify-between text-xl">
          Голоса <span aria-hidden>↗</span>
        </strong>
      </Link>
      <button
        type="button"
        disabled
        title="Раздел в разработке"
        className={`${tile} border-line bg-surface text-muted`}
      >
        <span
          aria-hidden
          className="grid h-12 w-12 place-content-center justify-items-center gap-1"
        >
          <i className="size-5 rounded-full bg-current" />
          <i className="h-5 w-10 rounded-t-full bg-current" />
        </span>
        <strong className="text-xl">Аватары</strong>
      </button>
    </div>
  );
}
