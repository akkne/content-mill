"use client";

import { projectField, fieldLabel, formError, primaryButton, secondaryButton, workPanel } from "@/app/ui-styles";
import { useState, useTransition } from "react";

import type { ProjectContext } from "@/lib/projects";
import { saveProjectContext } from "../actions";

const lines = (items: string[]) => items.join("\n");
const splitLines = (value: string) => value.split("\n").map((item) => item.trim()).filter(Boolean);

export function ContextEditor({ initial }: { initial: ProjectContext }) {
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
        setStatus("Контекст сохранён");
        setConflict(false);
      } else {
        setStatus(result.error ?? "Ошибка сохранения");
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
        <h2 className="text-[17px]">О клиенте</h2>
        <label className={fieldLabel} htmlFor="context-description">
          Описание
        </label>
        <textarea
          className={`${projectField} resize-y`}
          id="context-description"
          maxLength={10000}
          onChange={(event) => setDescription(event.target.value)}
          placeholder="Чем занимается клиент и что важно знать о бренде"
          rows={5}
          value={description}
        />
      </section>
      <section className={`${workPanel} grid gap-3`}>
        <h2 className="text-[17px]">Аудитория</h2>
        <p className="text-xs leading-[1.7] text-muted">Каждую аудиторию укажите с новой строки.</p>
        <label className={fieldLabel} htmlFor="context-audiences">
          Сегменты аудитории
        </label>
        <textarea
          className={`${projectField} resize-y`}
          id="context-audiences"
          onChange={(event) => setAudiences(event.target.value)}
          placeholder="Начинающие предприниматели&#10;Маркетологи малых команд"
          rows={4}
          value={audiences}
        />
      </section>
      <section className={`${workPanel} grid gap-3`}>
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-[17px]">Продукты</h2>
          <button
            className={secondaryButton}
            onClick={() => setProducts([...products, { name: "", description: "" }])}
            type="button"
          >
            + Добавить
          </button>
        </div>
        {products.length === 0 && (
          <p className="text-xs leading-[1.7] text-muted">Добавьте продукты или услуги клиента.</p>
        )}
        {products.map((product, index) => (
          <div
            className="grid grid-cols-[1fr_1fr_auto] items-end gap-2.5 max-[561px]:grid-cols-1"
            key={index}
          >
            <label className={fieldLabel}>
              Название
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
              Описание
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
              aria-label={`Удалить продукт ${index + 1}`}
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
          <h2 className="text-[17px]">Подтверждённые факты</h2>
          <button
            className={secondaryButton}
            onClick={() => setFacts([...facts, { text: "", source_url: null }])}
            type="button"
          >
            + Добавить
          </button>
        </div>
        {facts.length === 0 && (
          <p className="text-xs leading-[1.7] text-muted">
            Факты помогут сохранять точность будущих материалов.
          </p>
        )}
        {facts.map((fact, index) => (
          <div
            className="grid grid-cols-[1fr_1fr_auto] items-end gap-2.5 max-[561px]:grid-cols-1"
            key={index}
          >
            <label className={fieldLabel}>
              Факт
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
              Ссылка на источник
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
              aria-label={`Удалить факт ${index + 1}`}
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
        <h2 className="text-[17px]">Ограничения</h2>
        <label className={fieldLabel} htmlFor="context-terms">
          Запрещённые слова и темы
        </label>
        <textarea
          className={`${projectField} resize-y`}
          id="context-terms"
          onChange={(event) => setTerms(event.target.value)}
          placeholder="Каждое ограничение с новой строки"
          rows={3}
          value={terms}
        />
      </section>
      <div className="flex flex-wrap items-center justify-end gap-3">
        <span
          aria-live="polite"
          className={status && status !== "Контекст сохранён" ? formError : "mr-auto font-bold text-success"}
        >
          {status}
        </span>
        {conflict && (
          <button className={secondaryButton} onClick={() => window.location.reload()} type="button">
            Обновить страницу
          </button>
        )}
        <button className={primaryButton} disabled={pending || conflict} type="submit">
          {pending ? "Сохраняем…" : "Сохранить контекст"}
        </button>
      </div>
    </form>
  );
}
