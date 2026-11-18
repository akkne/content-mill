"use client";

import { useMemo, useState, useTransition } from "react";

import type { KnowledgeNode } from "@/lib/knowledge";
import { changeKnowledgeNode } from "./actions";

export function KnowledgeBrowser({ initial, projectId, projectName }: { initial: KnowledgeNode[]; projectId: string; projectName: string }) {
  const [nodes, setNodes] = useState(initial);
  const [folderId, setFolderId] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [pending, startTransition] = useTransition();
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
  const visible = nodes.filter((node) => query ? node.name.toLocaleLowerCase("ru").includes(query.toLocaleLowerCase("ru")) : node.parent_id === folderId)
    .sort((a, b) => a.kind === b.kind ? a.name.localeCompare(b.name, "ru") : a.kind === "folder" ? -1 : 1);
  const crumbs: KnowledgeNode[] = [];
  let ancestor = folder;
  while (ancestor) { crumbs.unshift(ancestor); ancestor = ancestor.parent_id ? byId.get(ancestor.parent_id) : undefined; }

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
      }
    });
  }

  function create() {
    const name = window.prompt("Название новой папки");
    if (name?.trim()) mutate("create", { parentId: folderId, name: name.trim(), kind: "folder" });
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
    <div className="kb-toolbar"><nav className="kb-crumbs" aria-label="Путь к папке"><button onClick={() => { setFolderId(null); setQuery(""); }} type="button">{projectName}</button>{crumbs.map((node) => <span key={node.id}> / <button onClick={() => { setFolderId(node.id); setQuery(""); }} type="button">{node.name}</button></span>)}</nav><input aria-label="Поиск папок и документов" onChange={(event) => setQuery(event.target.value)} placeholder="Поиск файлов и папок" type="search" value={query} /></div>
    <div className="kb-layout"><aside className="kb-tree" aria-label="Папки"><strong>ПАПКИ</strong><button aria-current={folderId === null ? "page" : undefined} onClick={() => { setFolderId(null); setQuery(""); }} type="button">📁 {projectName}</button>{orderedFolders.map((node) => <button aria-current={folderId === node.id ? "page" : undefined} key={node.id} onClick={() => { setFolderId(node.id); setQuery(""); }} style={{ paddingLeft: `${12 + depth(node, byId) * 16}px` }} type="button">📁 {node.name}</button>)}</aside>
      <div className="kb-content"><div className="kb-content-head"><div><span className="eyebrow">{query ? "Результаты поиска" : "Содержимое папки"}</span><h2>{query ? "Поиск" : folder?.name ?? projectName}</h2><p>{visible.length} элементов</p></div><button className="primary-button" disabled={pending} onClick={create} type="button">+ Папка</button></div>
        <div className="kb-list">{visible.length ? visible.map((node) => <button aria-pressed={selectedId === node.id} className="kb-row" key={node.id} onClick={() => setSelectedId(node.id)} onDoubleClick={() => { if (node.kind === "folder") { setFolderId(node.id); setQuery(""); } }} type="button"><span aria-hidden="true">{node.kind === "folder" ? "📁" : "📄"}</span><span><strong>{node.name}</strong><small>{node.kind === "folder" ? "Папка" : "Документ"}</small></span><span aria-hidden="true">›</span></button>) : <p className="kb-empty">Здесь пока нет файлов и папок.</p>}</div>
        {selected && <div className="kb-selection"><strong>{selected.name}</strong><div><button className="secondary-button" disabled={pending} onClick={rename} type="button">Переименовать</button><label>Переместить в <select disabled={pending} onChange={(event) => move(event.target.value)} value={selected.parent_id ?? ""}><option value="">{projectName}</option>{folders.filter((item) => item.id !== selected.id).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><button className="secondary-button" disabled={pending} onClick={archive} type="button">Архивировать</button></div></div>}
        {error && <p className="form-error" role="alert">{error}</p>}
      </div></div>
  </section>;
}

function depth(node: KnowledgeNode, byId: Map<string, KnowledgeNode>): number {
  let count = 0;
  let parent = node.parent_id;
  while (parent && count < 20) { count++; parent = byId.get(parent)?.parent_id ?? null; }
  return count;
}
