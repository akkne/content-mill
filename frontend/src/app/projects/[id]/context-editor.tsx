"use client";
import { useTranslator } from "@/app/interface-language";

import { projectField, fieldLabel, formError, primaryButton, secondaryButton, workPanel } from "@/app/ui-styles";
import { useState, useTransition } from "react";

import type { ProjectContext } from "@/lib/projects";
import { saveProjectContext } from "../actions";

const lines = (items: string[]) => items.join("\n");
const splitLines = (value: string) => value.split("\n").map((item) => item.trim()).filter(Boolean);

export function ContextEditor({ initial }: { initial: ProjectContext }) {
  const t = useTranslator();
  const [revision, setRevision] = useState(initial.revision);
  const [description, setDescription] = useState(initial.description);
  const [audiences, setAudiences] = useState(lines(initial.audiences));
  const [products, setProducts] = useState(initial.products);
  const [facts, setFacts] = useState(initial.facts);
  const [terms, setTerms] = useState(lines(initial.forbidden_terms));
  const [status, setStatus] = useState("");
  const [conflict, setConflict] = useState(false);
  const [pending, startTransition] = useTransition();

  function save() {
    setStatus("");
    startTransition(async () => {
      const result = await saveProjectContext(initial.project_id, revision, {
        description,
        audiences: splitLines(audiences),
        products: products.filter((item) => item.name.trim()).map((item) => ({ name: item.name.trim(), description: item.description.trim() })),
        facts: facts.filter((item) => item.text.trim()).map((item) => ({ text: item.text.trim(), source_url: item.source_url?.trim() || null })),
        forbidden_terms: splitLines(terms),
      });
      if (result.context) {
        setRevision(result.context.revision);
        setStatus(t("Контекст сохранён", "Context saved"));
        setConflict(false);
      } else {
        setStatus(result.error ?? t("Ошибка сохранения", "Could not save changes"));
        setConflict(Boolean(result.conflict));
      }
    });
  }

  return (
    <form
      className="grid gap-4"
      onSubmit={(event) => {
        event.preventDefault();
        save();
      }}
    >
      <section className={`${workPanel} grid gap-3`}>
        <h2 className="text-[17px]">{t("О клиенте", "About the client")}</h2>
        <label className={fieldLabel} htmlFor="context-description">
          {t("Описание", "Description")}
        </label>
        <textarea
          className={`${projectField} resize-y`}
          id="context-description"
          maxLength={10000}
          onChange={(event) => setDescription(event.target.value)}
          placeholder={t("Чем занимается клиент и что важно знать о бренде", "What the client does and what matters about the brand")}
          rows={5}
          value={description}
        />
      </section>
      <section className={`${workPanel} grid gap-3`}>
        <h2 className="text-[17px]">{t("Аудитория", "Audience")}</h2>
        <p className="text-xs leading-[1.7] text-muted">{t("Каждую аудиторию укажите с новой строки.", "Enter one audience per line.")}</p>
        <label className={fieldLabel} htmlFor="context-audiences">
          {t("Сегменты аудитории", "Audience segments")}
        </label>
        <textarea
          className={`${projectField} resize-y`}
          id="context-audiences"
          onChange={(event) => setAudiences(event.target.value)}
          placeholder={t("Начинающие предприниматели\nМаркетологи малых команд", "First-time entrepreneurs\nSmall marketing teams")}
          rows={4}
          value={audiences}
        />
      </section>
      <section className={`${workPanel} grid gap-3`}>
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-[17px]">{t("Продукты", "Products")}</h2>
          <button
            className={secondaryButton}
            onClick={() => setProducts([...products, { name: "", description: "" }])}
            type="button"
          >
            {t("+ Добавить", "+ Add")}
          </button>
        </div>
        {products.length === 0 && (
          <p className="text-xs leading-[1.7] text-muted">{t("Добавьте продукты или услуги клиента.", "Add the client's products or services.")}</p>
        )}
        {products.map((product, index) => (
          <div
            className="grid grid-cols-[1fr_1fr_auto] items-end gap-2.5 max-[561px]:grid-cols-1"
            key={index}
          >
            <label className={fieldLabel}>
              {t("Название", "Name")}
              <input
                className={projectField}
                maxLength={160}
                onChange={(event) =>
                  setProducts(
                    products.map((item, i) => (i === index ? { ...item, name: event.target.value } : item)),
                  )
                }
                value={product.name}
              />
            </label>
            <label className={fieldLabel}>
              {t("Описание", "Description")}
              <input
                className={projectField}
                maxLength={2000}
                onChange={(event) =>
                  setProducts(
                    products.map((item, i) =>
                      i === index ? { ...item, description: event.target.value } : item,
                    ),
                  )
                }
                value={product.description}
              />
            </label>
            <button
              aria-label={t(`Удалить продукт ${index + 1}`, `Remove product ${index + 1}`)}
              className="size-[42px] rounded-lg border border-line bg-control text-[23px] text-ink max-[561px]:w-full"
              onClick={() => setProducts(products.filter((_, i) => i !== index))}
              type="button"
            >
              ×
            </button>
          </div>
        ))}
      </section>
      <section className={`${workPanel} grid gap-3`}>
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-[17px]">{t("Подтверждённые факты", "Verified facts")}</h2>
          <button
            className={secondaryButton}
            onClick={() => setFacts([...facts, { text: "", source_url: null }])}
            type="button"
          >
            {t("+ Добавить", "+ Add")}
          </button>
        </div>
        {facts.length === 0 && (
          <p className="text-xs leading-[1.7] text-muted">
            {t("Факты помогут сохранять точность будущих материалов.", "Use facts to keep future materials accurate.")}
          </p>
        )}
        {facts.map((fact, index) => (
          <div
            className="grid grid-cols-[1fr_1fr_auto] items-end gap-2.5 max-[561px]:grid-cols-1"
            key={index}
          >
            <label className={fieldLabel}>
              {t("Факт", "Fact")}
              <input
                className={projectField}
                maxLength={2000}
                onChange={(event) =>
                  setFacts(
                    facts.map((item, i) => (i === index ? { ...item, text: event.target.value } : item)),
                  )
                }
                value={fact.text}
              />
            </label>
            <label className={fieldLabel}>
              {t("Ссылка на источник", "Source link")}
              <input
                className={projectField}
                maxLength={2000}
                onChange={(event) =>
                  setFacts(
                    facts.map((item, i) =>
                      i === index ? { ...item, source_url: event.target.value } : item,
                    ),
                  )
                }
                placeholder="https://"
                type="url"
                value={fact.source_url ?? ""}
              />
            </label>
            <button
              aria-label={t(`Удалить факт ${index + 1}`, `Remove fact ${index + 1}`)}
              className="size-[42px] rounded-lg border border-line bg-control text-[23px] text-ink max-[561px]:w-full"
              onClick={() => setFacts(facts.filter((_, i) => i !== index))}
              type="button"
            >
              ×
            </button>
          </div>
        ))}
      </section>
      <section className={`${workPanel} grid gap-3`}>
        <h2 className="text-[17px]">{t("Ограничения", "Restrictions")}</h2>
        <label className={fieldLabel} htmlFor="context-terms">
          {t("Запрещённые слова и темы", "Prohibited words and topics")}
        </label>
        <textarea
          className={`${projectField} resize-y`}
          id="context-terms"
          onChange={(event) => setTerms(event.target.value)}
          placeholder={t("Каждое ограничение с новой строки", "One restriction per line")}
          rows={3}
          value={terms}
        />
      </section>
      <div className="flex flex-wrap items-center justify-end gap-3">
        <span
          aria-live="polite"
          className={status && status !== t("Контекст сохранён", "Context saved") ? formError : "mr-auto font-bold text-success"}
        >
          {status}
        </span>
        {conflict && (
          <button className={secondaryButton} onClick={() => window.location.reload()} type="button">
            {t("Обновить страницу", "Refresh page")}
          </button>
        )}
        <button className={primaryButton} disabled={pending || conflict} type="submit">
          {pending ? t("Сохраняем…", "Saving…") : t("Сохранить контекст", "Save context")}
        </button>
      </div>
    </form>
  );
}
