import { getTranslator } from "@/lib/server-language";
import { LibraryIllustration } from "./library-illustration";
import Link from "next/link";


export async function LibraryTiles() {
  const t = await getTranslator();
  const libraries = [
    { name: t("Монтаж", "Editing"), href: "/montage", description: t("Шаблоны, анимации и референсы", "Templates, animations and references"), kind: "motion" },
    { name: t("Голоса", "Voices"), href: "/knowledge/voices", description: t("Мои голоса и каталог ElevenLabs", "My voices and the ElevenLabs catalog"), kind: "voice" },
    { name: t("Аватары", "Avatars"), href: "/knowledge/avatars", description: t("Персонажи, фотографии и одежда", "Characters, photos and wardrobe"), kind: "avatar" },
  ] as const;
  return (
    <section className="mt-8" aria-labelledby="library-title">
      <h2 id="library-title" className="mb-3.5 text-lg font-bold tracking-tight">{t("Личные библиотеки", "Personal libraries")}</h2>
      <div className="grid gap-4 lg:grid-cols-3">
        {libraries.map(({ name, href, description, kind }) => (
          <Link key={href} href={href} className="group grid min-h-36 grid-cols-[minmax(0,1fr)_36%] overflow-hidden rounded-[18px] border border-line bg-surface shadow-panel hover:border-accent/50 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-accent motion-safe:transition-colors">
            <div className="flex flex-col items-start p-5 sm:p-6">
              <h3 className="text-xl font-bold tracking-tight">{name}</h3>
              <p className="mt-1 text-xs leading-relaxed text-muted">{description}</p>
              <span aria-hidden="true" className="mt-auto inline-flex size-8 items-center justify-center rounded-full bg-tint text-lg text-accent group-hover:bg-action group-hover:text-white">→</span>
            </div>
            <div className="flex items-center justify-center bg-hero">
              {kind==="motion"?<span aria-hidden="true" className="text-5xl text-accent">▶</span>:<LibraryIllustration kind={kind} />}
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}
