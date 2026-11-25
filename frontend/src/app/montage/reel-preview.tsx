"use client";
import { useState } from "react";
import { useInterfaceLanguage, useTranslator } from "../interface-language";
import type { ReelFormat } from "@/lib/motion";

export function ReelPreview({ reel }: { reel: ReelFormat }) {
  const lang = useInterfaceLanguage(), t = useTranslator();
  const [error, setError] = useState(false);
  return (
    <div>
      <video key={reel.id + lang} playsInline controls preload="none"
        poster={`/reels/${reel.id}-${lang}.jpg`}
        className="aspect-[9/16] w-full rounded-xl object-cover"
        aria-label={t("Пример монтажа", "Sample reel") + " · " + reel[lang].title}
        src={`/reels/${reel.id}-${lang}.mp4`}
        onError={() => setError(true)} onLoadedData={() => setError(false)}
      />
      {error && (
        <p role="alert">
          {t(
            "Не удалось загрузить пример рилса.",
            "Could not load the sample reel.",
          )}
        </p>
      )}
    </div>
  );
}
