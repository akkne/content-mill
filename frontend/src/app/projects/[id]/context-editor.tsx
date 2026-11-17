"use client";

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
  const [tone, setTone] = useState(initial.tone_of_voice);
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
        tone_of_voice: tone,
        forbidden_terms: splitLines(terms),
        source_version_ids: [],
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

  return <form className="context-form" onSubmit={(event) => { event.preventDefault(); save(); }}>
    <section className="work-panel context-section"><h2>О клиенте</h2><label htmlFor="context-description">Описание</label><textarea id="context-description" maxLength={10000} onChange={(event) => setDescription(event.target.value)} placeholder="Чем занимается клиент и что важно знать о бренде" rows={5} value={description} /></section>
    <section className="work-panel context-section"><h2>Аудитория</h2><p>Каждую аудиторию укажите с новой строки.</p><label htmlFor="context-audiences">Сегменты аудитории</label><textarea id="context-audiences" onChange={(event) => setAudiences(event.target.value)} placeholder="Начинающие предприниматели&#10;Маркетологи малых команд" rows={4} value={audiences} /></section>
    <section className="work-panel context-section"><div className="section-heading"><h2>Продукты</h2><button className="secondary-button" onClick={() => setProducts([...products, { name: "", description: "" }])} type="button">+ Добавить</button></div>
      {products.length === 0 && <p>Добавьте продукты или услуги клиента.</p>}
      {products.map((product, index) => <div className="entry-row" key={index}><label>Название<input maxLength={160} onChange={(event) => setProducts(products.map((item, i) => i === index ? { ...item, name: event.target.value } : item))} value={product.name} /></label><label>Описание<input maxLength={2000} onChange={(event) => setProducts(products.map((item, i) => i === index ? { ...item, description: event.target.value } : item))} value={product.description} /></label><button aria-label={`Удалить продукт ${index + 1}`} className="remove-button" onClick={() => setProducts(products.filter((_, i) => i !== index))} type="button">×</button></div>)}
    </section>
    <section className="work-panel context-section"><div className="section-heading"><h2>Подтверждённые факты</h2><button className="secondary-button" onClick={() => setFacts([...facts, { text: "", source_url: null }])} type="button">+ Добавить</button></div>
      {facts.length === 0 && <p>Факты помогут сохранять точность будущих материалов.</p>}
      {facts.map((fact, index) => <div className="entry-row" key={index}><label>Факт<input maxLength={2000} onChange={(event) => setFacts(facts.map((item, i) => i === index ? { ...item, text: event.target.value } : item))} value={fact.text} /></label><label>Ссылка на источник<input maxLength={2000} onChange={(event) => setFacts(facts.map((item, i) => i === index ? { ...item, source_url: event.target.value } : item))} placeholder="https://" type="url" value={fact.source_url ?? ""} /></label><button aria-label={`Удалить факт ${index + 1}`} className="remove-button" onClick={() => setFacts(facts.filter((_, i) => i !== index))} type="button">×</button></div>)}
    </section>
    <section className="work-panel context-section"><h2>Голос и ограничения</h2><label htmlFor="context-tone">Tone of Voice</label><textarea id="context-tone" maxLength={5000} onChange={(event) => setTone(event.target.value)} placeholder="Стиль общения, тон и примеры формулировок" rows={4} value={tone} /><label htmlFor="context-terms">Запрещённые слова и темы</label><textarea id="context-terms" onChange={(event) => setTerms(event.target.value)} placeholder="Каждое ограничение с новой строки" rows={3} value={terms} /></section>
    <div className="context-actions"><span aria-live="polite" className={status && status !== "Контекст сохранён" ? "form-error" : "save-status"}>{status}</span>{conflict && <button className="secondary-button" onClick={() => window.location.reload()} type="button">Обновить страницу</button>}<button className="primary-button" disabled={pending || conflict} type="submit">{pending ? "Сохраняем…" : "Сохранить контекст"}</button></div>
  </form>;
}
