import { useTranslator } from "@/app/interface-language";
import type { KnowledgeNode } from "@/lib/knowledge";
import { mediaPreview } from "./media-actions";
import { useRef, useState } from "react";

export function DocumentEditor({ draft, markdown, setDraft, project, images }: {
  project: string; images: KnowledgeNode[]; draft: string; markdown: boolean; setDraft: (value: string) => void;
}) {
  const t = useTranslator();
  const editor = useRef<HTMLTextAreaElement>(null);
  const [imageError, setImageError] = useState("");
  function insert(prefix: string, placeholder: string, suffix = "") {
    const el = editor.current;
    if (!el) return;
    const { selectionStart: start, selectionEnd: end } = el;
    const current = el.value;
    const text = current.slice(start, end) || placeholder;
    const next = current.slice(0, start) + prefix + text + suffix + current.slice(end);
    if (next.length > 1000000) return;
    setDraft(next);
    requestAnimationFrame(() => { el.focus(); el.setSelectionRange(start + prefix.length, start + prefix.length + text.length); });
  }
  return (
    <>
      {markdown && (
        <div
          className="flex flex-wrap gap-2 px-5 pt-3.5 [&_button]:text-[.85rem] [&_button]:text-accent"
          role="group"
          aria-label={t("Форматирование документа", "Document formatting")}
        >
          <button type="button" onClick={() => insert("\n## ", t("Заголовок", "Heading"))}>
            {t("Заголовок", "Heading")}
          </button>
          <button type="button" onClick={() => insert("\n- ", t("Пункт", "Item"))}>
            {t("Список", "List")}
          </button>
          <button type="button" onClick={() => insert("[", t("Текст ссылки", "Link text"), "](https://)")}>
            {t("Ссылка", "Link")}
          </button>
          <button type="button" onClick={() => insert("![", t("Описание изображения", "Image description"), "](https://)")}>
            {t("Изображение", "Image")}
          </button>
          {images.length > 0 && (
            <select
              aria-label={t("Изображение из базы знаний", "Image from knowledge base")}
              value=""
              onChange={async (event) => {
                const image = images.find((item) => item.id === event.target.value);
                if (!image) return;
                const result = await mediaPreview(project, image.id);
                if (!result.data) {
                  setImageError(result.error || t("Не удалось открыть изображение.", "Could not open the image."));
                  return;
                }
                setImageError("");
                insert(
                  "![",
                  image.name.replaceAll("[", "").replaceAll("]", ""),
                  `](/projects/${project}/knowledge/files/${image.id}/${result.data.version.version})`,
                );
              }}
            >
              <option value="">{t("Из базы знаний…", "From knowledge base…")}</option>
              {images.map((image) => (
                <option key={image.id} value={image.id}>
                  {image.name}
                </option>
              ))}
            </select>
          )}
          {imageError && <span role="alert">{imageError}</span>}
        </div>
      )}
      <textarea
        className="m-5 block min-h-[300px] w-[calc(100%-40px)] resize-y rounded-[10px] border border-line bg-control p-[15px] font-mono leading-[1.8] text-ink"
        ref={editor}
        aria-label={t("Содержимое документа", "Document contents")}
        autoFocus
        maxLength={1000000}
        onChange={(event) => setDraft(event.target.value)}
        value={draft}
      />
    </>
  );
}
