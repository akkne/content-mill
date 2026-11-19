import Image from "next/image";

export function LibraryIllustration({ kind }: { kind: "voice" | "avatar" }) {
  if (kind === "avatar") {
    return (
      <span aria-hidden="true" className="relative grid h-28 w-24 shrink-0 place-items-center">
        <span className="absolute h-[86px] w-[70px] translate-x-1.5 -rotate-12 rounded-xl border border-accent/25 bg-tint" />
        <span className="relative flex h-[90px] w-[72px] rotate-6 flex-col items-center justify-center rounded-xl border border-accent/25 bg-surface shadow-panel motion-safe:transition-transform motion-safe:duration-300 motion-safe:group-hover:rotate-0 motion-safe:group-focus-visible:rotate-0">
          <Image src="/mill-mascot.png" alt="" width={64} height={64} />
          <span className="mt-1 h-1 w-6 rounded-full bg-accent/40" />
        </span>
      </span>
    );
  }

  return (
    <span aria-hidden="true" className="relative grid h-28 w-24 shrink-0 place-items-center">
      <span className="relative block h-20 w-16 -rotate-6 motion-safe:transition-transform motion-safe:duration-300 motion-safe:group-hover:rotate-6 motion-safe:group-focus-visible:rotate-6">
        <span className="absolute inset-x-[11px] top-0 flex h-[55px] flex-col items-center rounded-full bg-action pt-2">
          <span className="h-1 w-4 rounded-full bg-white/55" />
          <span className="mt-2 flex gap-0.5">
            {[0, 1].map((eye) => (
              <span key={eye} className="flex h-4 w-3 items-start justify-end rounded-full bg-white p-0.5">
                <span className="size-1.5 rounded-full bg-slate-900" />
              </span>
            ))}
          </span>
        </span>
        <span className="absolute inset-x-1 top-[38px] h-7 rounded-b-full border-x-4 border-b-4 border-accent" />
        <span className="absolute inset-x-[30px] top-[65px] h-3 bg-accent" />
        <span className="absolute inset-x-5 bottom-0 h-1 rounded-full bg-accent" />
      </span>
    </span>
  );
}
