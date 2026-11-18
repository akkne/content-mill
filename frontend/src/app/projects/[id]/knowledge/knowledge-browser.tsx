"use client";

import { useEffect, useMemo, useState, useTransition } from "react";

import type { KnowledgeNode } from "@/lib/knowledge";
import { changeKnowledgeNode, loadDocument, saveDocument, searchKnowledge, type DocumentContent, type DocumentVersion } from "./actions";

import { saveProjectContext } from "../../actions";

type ContextSources = { ids: string[]; revision: number };

function FolderIcon() {
  return <svg aria-hidden="true" className="kb-folder-icon" viewBox="0 0 48 40"><path d="M4 7a4 4 0 0 1 4-4h12l5 5h15a4 4 0 0 1 4 4v21a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4z" fill="#51A2FF" /><path d="M4 14h40v19a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4z" fill="#2783ED" /></svg>;
}

function FileIcon() {
  return <svg aria-hidden="true" className="kb-file-icon" viewBox="0 0 36 42"><path d="M5 1h17l9 9v29a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V3a2 2 0 0 1 2-2z" fill="currentColor" opacity=".15" /><path d="M5 1h17l9 9v29a2 2 0 0 1-2-2H5a2 2 0 0 1-2-2V3a2 2 0 0 1 2-2zM22 1v9h9M9 17h16M9 23h16M9 29h12" fill="none" stroke="currentColor" strokeWidth="2" /></svg>;
}

export function KnowledgeBrowser({ initial, initialSources, projectId, projectName }: { initialSources: ContextSources; initial: KnowledgeNode[]; projectId: string; projectName: string }) {
  const [sources, setSources] = useState(initialSources);
  const [nodes, setNodes] = useState(initial);
  const [folderId, setFolderId] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [searchIds, setSearchIds] = useState<string[] | null>(null);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [pending, startTransition] = useTransition();
  const [openId, setOpenId] = useState<string | null>(null);
  const [document, setDocument] = useState<DocumentContent | null>(null);
  const [versions, setVersions] = useState<DocumentVersion[]>([]);
  const [draft, setDraft] = useState("");
  const [documentError, setDocumentError] = useState("");
  const [editing, setEditing] = useState(false);
  const byId = useMemo(() => new Map(nodes.map((node) => [node.id, node])), [nodes]);
  const selected = selectedId ? byId.get(selectedId) : undefined;
  const folder = folderId ? byId.get(folderId) : undefined;
  const folders = nodes.filter((node) => node.kind === "folder");
  const orderedFolders: KnowledgeNode[] = [];
  function visit(parentId: string | null) {
    folders.filter((node) => node.parent_id === parentId).sort((a, b) => a.name.localeCompare(b.name, "ru"))
      .forEach((node) => { orderedFolders.push(node); visit(node.id); });
  }
  visit(null);
  const visible = nodes.filter((node) => query ? (searchIds ? searchIds.includes(node.id) : node.name.toLocaleLowerCase("ru").includes(query.toLocaleLowerCase("ru"))) : node.parent_id === folderId)
    .sort((a, b) => a.kind === b.kind ? a.name.localeCompare(b.name, "ru") : a.kind === "folder" ? -1 : 1);
  const crumbs: KnowledgeNode[] = [];
  let ancestor = folder;
  while (ancestor) { crumbs.unshift(ancestor); ancestor = ancestor.parent_id ? byId.get(ancestor.parent_id) : undefined; }

  useEffect(() => {
    const clean = query.trim();
    if (!clean) return;
    let cancelled = false;
    const timer = window.setTimeout(async () => {
      const result = await searchKnowledge(projectId, clean);
      if (cancelled) return;
      setSearchIds(result.ids ?? []);
      setSearchError(result.error ?? "");
      setSearching(false);
    }, 250);
    return () => { cancelled = true; window.clearTimeout(timer); };
  }, [projectId, query]);

  function changeQuery(value: string) {
    setQuery(value);
    setSearchIds(null);
    setSearching(Boolean(value.trim()));
    setSearchError("");
  }

  function mutate(action: "create" | "rename" | "move" | "archive", data: Parameters<typeof changeKnowledgeNode>[2]) {
    setError("");
    startTransition(async () => {
      const result = await changeKnowledgeNode(projectId, action, data);
      if (result.error) { setError(result.error); return; }
      if (action === "archive" && data.nodeId) {
        const removed = new Set([data.nodeId]);
        let changed = true;
        while (changed) { changed = false; for (const node of nodes) if (node.parent_id && removed.has(node.parent_id) && !removed.has(node.id)) { removed.add(node.id); changed = true; } }
        setNodes(nodes.filter((node) => !removed.has(node.id)));
        setSelectedId(null);
        if (folderId && removed.has(folderId)) setFolderId(null);
      } else if (result.node) {
        setNodes(action === "create" ? [...nodes, result.node] : nodes.map((node) => node.id === result.node?.id ? result.node : node));
        setSelectedId(result.node.id);
        if (action === "create" && result.node.kind === "document") openDocument(result.node.id);
      }
    });
  }

  function create() {
    const name = window.prompt("Название новой папки");
    if (name?.trim()) mutate("create", { parentId: folderId, name: name.trim(), kind: "folder" });
  }

  function createDocument() {
    const name = window.prompt("Название документа (.md или .txt)", "Новый документ.md");
    if (!name) return;
    if (!/\.(md|txt)$/i.test(name.trim())) { setError("Документ должен иметь расширение .md или .txt."); return; }
    mutate("create", { parentId: folderId, name: name.trim(), kind: "document" });
  }

  function openDocument(nodeId: string, version?: number) {
    setOpenId(nodeId);
    setDocument(null);
    setDocumentError("");
    setEditing(false);
    startTransition(async () => {
      const result = await loadDocument(projectId, nodeId, version);
      if (result.error) { setDocumentError(result.error); return; }
      setDocument(result.document ?? null);
      setDraft(result.document?.content ?? "");
      setVersions(result.versions ?? []);
    });
  }

  function saveOpenDocument() {
    if (!openId || !document) return;
    setDocumentError("");
    startTransition(async () => {
      const result = await saveDocument(projectId, openId, document.revision, draft, document.format);
      if (result.error) { setDocumentError(result.error); return; }
      if (result.document) {
        setDocument(result.document);
        setEditing(false);
        setNodes(nodes.map((node) => node.id === openId ? { ...node, revision: result.document!.revision } : node));
        changeQuery("");
        const history = await loadDocument(projectId, openId);
        setVersions(history.versions ?? []);
      }
    });
  }

  const shownVersion = versions.find((item) => item.node_id === openId && item.version === document?.version && document.node_id === openId);
  const linked = shownVersion && sources.ids.includes(shownVersion.id);

  function toggleSource() {
    if (!shownVersion) return;
    const ids = linked ? sources.ids.filter((id) => id !== shownVersion.id) : [...sources.ids, shownVersion.id];
    setDocumentError("");
    startTransition(async () => {
      const result = await saveProjectContext(projectId, sources.revision, { source_version_ids: ids });
      if (result.context) {
        setSources({ ids: result.context.source_version_ids, revision: result.context.revision });
      } else {
        setDocumentError(result.error ?? "Не удалось сохранить источники контекста.");
      }
    });
  }

  function rename() {
    if (!selected) return;
    const name = window.prompt("Новое название", selected.name);
    if (name?.trim() && name.trim() !== selected.name) mutate("rename", { nodeId: selected.id, revision: selected.revision, name: name.trim() });
  }

  function move(destination: string) {
    if (!selected) return;
    mutate("move", { nodeId: selected.id, revision: selected.revision, parentId: destination || null });
  }

  function archive() {
    if (selected && window.confirm(`Архивировать «${selected.name}»${selected.kind === "folder" ? " вместе с содержимым" : ""}?`)) {
      mutate("archive", { nodeId: selected.id, revision: selected.revision });
    }
  }

  return <section className="kb-shell" aria-label="База знаний проекта">
    <div className="kb-toolbar"><nav className="kb-crumbs" aria-label="Путь к папке"><button onClick={() => { setFolderId(null); changeQuery(""); }} type="button">{projectName}</button>{crumbs.map((node) => <span key={node.id}> / <button onClick={() => { setFolderId(node.id); changeQuery(""); }} type="button">{node.name}</button></span>)}</nav><input aria-label="Поиск папок и документов" maxLength={200} onChange={(event) => changeQuery(event.target.value)} placeholder="Поиск по названию и тексту" type="search" value={query} /></div>
    <div className="kb-layout"><aside className="kb-tree" aria-label="Папки"><strong>ПАПКИ</strong><button aria-current={folderId === null ? "page" : undefined} onClick={() => { setFolderId(null); changeQuery(""); }} type="button"><FolderIcon />{projectName}</button>{orderedFolders.map((node) => <button aria-current={folderId === node.id ? "page" : undefined} key={node.id} onClick={() => { setFolderId(node.id); changeQuery(""); }} style={{ paddingLeft: `${12 + depth(node, byId) * 16}px` }} type="button"><FolderIcon />{node.name}</button>)}</aside>
      <div className="kb-content"><div className="kb-content-head"><div><span className="eyebrow">{query ? "Результаты поиска" : "Содержимое папки"}</span><h2>{query ? "Поиск" : folder?.name ?? projectName}</h2><p>{searching ? "Ищем…" : `${visible.length} элементов`}</p></div><div className="kb-create-actions"><button className="secondary-button" disabled={pending} onClick={create} type="button">+ Папка</button><button className="primary-button" disabled={pending} onClick={createDocument} type="button">+ Файл</button></div></div>
        <div className="kb-list">{visible.length ? visible.map((node) => <button aria-pressed={selectedId === node.id} className="kb-row" key={node.id} onClick={() => setSelectedId(node.id)} onDoubleClick={() => { if (node.kind === "folder") { setFolderId(node.id); changeQuery(""); } else openDocument(node.id); }} type="button"><span aria-hidden="true">{node.kind === "folder" ? <FolderIcon /> : <FileIcon />}</span><span><strong>{node.name}</strong><small>{query ? nodePath(node, byId, projectName) : node.kind === "folder" ? "Папка" : "Документ"}</small></span><span aria-hidden="true">›</span></button>) : <p className="kb-empty">Здесь пока нет файлов и папок.</p>}</div>
        {searchError && <p className="form-error" role="alert">{searchError}</p>}
        {selected && <div className="kb-selection"><strong>{selected.name}</strong><div>{selected.kind === "document" && <button className="secondary-button" onClick={() => openDocument(selected.id)} type="button">Открыть</button>}<button className="secondary-button" disabled={pending} onClick={rename} type="button">Переименовать</button><label>Переместить в <select disabled={pending} onChange={(event) => move(event.target.value)} value={selected.parent_id ?? ""}><option value="">{projectName}</option>{folders.filter((item) => item.id !== selected.id).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><button className="secondary-button" disabled={pending} onClick={archive} type="button">Архивировать</button></div></div>}
        {error && <p className="form-error" role="alert">{error}</p>}
      </div></div>
    {openId && <div className="kb-modal-backdrop" role="presentation"><div aria-labelledby="kb-document-title" aria-modal="true" className="kb-document-modal" onKeyDown={(event) => { if (event.key === "Escape") { setOpenId(null); setDocument(null); setEditing(false); } }} role="dialog"><div className="kb-document-head"><div><span className="eyebrow">Документ</span><h2 id="kb-document-title">{byId.get(openId)?.name ?? "Документ"}</h2></div><button aria-label="Закрыть документ" autoFocus className="secondary-button" onClick={() => { setOpenId(null); setDocument(null); setEditing(false); }} type="button">×</button></div>
      {document ? <><div className="kb-document-body"><div className="kb-document-main">{editing ? <textarea aria-label="Содержимое документа" autoFocus maxLength={1000000} onChange={(event) => setDraft(event.target.value)} value={draft} /> : <pre>{document.content || "Документ пуст."}</pre>}</div><aside className="kb-history"><strong>История версий</strong>{versions.map((item) => <button aria-current={document.version === item.version ? "page" : undefined} key={item.id} onClick={() => openDocument(openId, item.version)} type="button">Версия {item.version}<small>{new Date(item.created_at).toLocaleString("ru-RU")}</small></button>)}{versions.length === 0 && <p>Версий пока нет.</p>}</aside></div><div className="kb-document-foot"><span>Версия {document.version || "не сохранён"}</span><div>{shownVersion && !editing && <button aria-pressed={Boolean(linked)} className="secondary-button" disabled={pending} onClick={toggleSource} type="button">{linked ? "Убрать из источников контекста" : "Добавить в источники контекста"}</button>}{document.version > 0 && document.version !== versions[0]?.version && <button className="secondary-button" onClick={() => openDocument(openId)} type="button">Текущая версия</button>}{editing ? <><button className="secondary-button" onClick={() => { setEditing(false); setDraft(document.content); }} type="button">Отменить</button><button className="primary-button" disabled={pending} onClick={saveOpenDocument} type="button">{pending ? "Сохраняем…" : "Сохранить"}</button></> : (document.version === 0 || document.version === versions[0]?.version) && <button className="secondary-button" onClick={() => { setEditing(true); setDraft(document.content); }} type="button">Редактировать</button>}</div></div></> : <p className="kb-empty">{pending ? "Открываем документ…" : documentError || "Не удалось открыть документ."}</p>}{documentError && document && <p className="form-error" role="alert">{documentError}</p>}</div></div>}
  </section>;
}

function depth(node: KnowledgeNode, byId: Map<string, KnowledgeNode>): number {
  let count = 0;
  let parent = node.parent_id;
  while (parent && count < 20) { count++; parent = byId.get(parent)?.parent_id ?? null; }
  return count;
}

function nodePath(node: KnowledgeNode, byId: Map<string, KnowledgeNode>, projectName: string): string {
  const names: string[] = [];
  let parent = node.parent_id;
  while (parent) { const folder = byId.get(parent); if (!folder) break; names.unshift(folder.name); parent = folder.parent_id; }
  return [projectName, ...names].join(" / ");
}
