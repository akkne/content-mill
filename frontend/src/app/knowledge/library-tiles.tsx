import Image from "next/image";
import Link from "next/link";

const libraries = [
  { name: "Голоса", href: "/knowledge/voices", description: "Мои голоса и каталог ElevenLabs", photo: "recording" },
  { name: "Аватары", href: "/knowledge/avatars", description: "Библиотека в разработке", photo: "portrait" },
];

export function LibraryTiles() {
  return (
    <section className="mt-8" aria-labelledby="library-title">
      <h2 id="library-title" className="mb-3.5 text-lg font-bold tracking-tight">Личные библиотеки</h2>
      <div className="grid gap-4 lg:grid-cols-2">
        {libraries.map(({ name, href, description, photo }) => (
          <Link key={href} href={href} className="group grid min-h-36 grid-cols-[minmax(0,1fr)_36%] overflow-hidden rounded-[18px] border border-line bg-surface shadow-panel hover:border-accent/50 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-accent motion-safe:transition-colors">
            <div className="flex flex-col items-start p-5 sm:p-6">
              <h3 className="text-xl font-bold tracking-tight">{name}</h3>
              <p className="mt-1 text-xs leading-relaxed text-muted">{description}</p>
              <span aria-hidden="true" className="mt-auto inline-flex size-8 items-center justify-center rounded-full bg-tint text-lg text-accent group-hover:bg-action group-hover:text-white">→</span>
            </div>
            <div aria-hidden="true" className="relative isolate overflow-hidden">
              <Image src={`/library/${photo}.jpg`} alt="" fill sizes="(min-width: 1024px) 200px, 35vw" className="object-cover motion-safe:transition-transform motion-safe:duration-500 motion-safe:group-hover:scale-105 motion-safe:group-focus-visible:scale-105" />
              {photo === "portrait" ? (
                <div className="absolute inset-4 border border-white/60" />
              ) : (
                <div className="absolute inset-x-0 bottom-3 flex items-center justify-center gap-1">
                  {["h-2", "h-4", "h-3", "h-6", "h-8", "h-4", "h-6", "h-3", "h-2"].map((height, index) => (
                    <span key={index} className={`w-1 rounded-full bg-white/90 ${height}`} />
                  ))}
                </div>
              )}
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}
