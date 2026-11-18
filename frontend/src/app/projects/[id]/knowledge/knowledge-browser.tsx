"use client";

import { eyebrow, field, fieldLabel, formError, kbDocumentFoot, kbDocumentHead, kbEmpty, primaryButton, secondaryButton } from "@/app/ui-styles";
import type { CSSProperties } from "react";
import { useEffect, useMemo, useRef, useState, useTransition } from "react";

import { DocumentEditor } from "./document-editor";
import Markdown from "react-markdown";
import { FolderProfile } from "./folder-profile";
import { MediaPreview } from "./media-preview";
import { exampleFiles } from "./media-actions";
import { acceptedMedia, uploadMedia } from "./upload-media";
import type { KnowledgeNode } from "@/lib/knowledge";
import { changeKnowledgeNode, loadDocument, saveDocument, searchKnowledge, type DocumentContent, type DocumentVersion } from "./actions";

import { saveProjectContext } from "../../actions";

type ContextSources = { ids: string[]; revision: number };

const folderButton =
  "flex min-h-[38px] items-center gap-2 truncate rounded-lg pr-3 pl-[calc(12px+var(--folder-depth,0)*16px)] py-[7px] text-left text-muted hover:bg-tint hover:text-accent aria-[current=page]:bg-tint aria-[current=page]:text-accent min-[761px]:shrink-0";

function FolderIcon() {
  return <svg aria-hidden="true" className="h-6 w-7 flex-none" viewBox="0 0 48 40"><path d="M4 7a4 4 0 0 1 4-4h12l5 5h15a4 4 0 0 1 4 4v21a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4z" fill="#51A2FF" /><path d="M4 14h40v19a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4z" fill="#2783ED" /></svg>;
}

function FileIcon() {
  return <svg aria-hidden="true" className="h-[29px] w-6 flex-none text-accent" viewBox="0 0 36 42"><path d="M5 1h17l9 9v29a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V3a2 2 0 0 1 2-2z" fill="currentColor" opacity=".15" /><path d="M5 1h17l9 9v29a2 2 0 0 1-2-2H5a2 2 0 0 1-2-2V3a2 2 0 0 1 2-2zM22 1v9h9M9 17h16M9 23h16M9 29h12" fill="none" stroke="currentColor" strokeWidth="2" /></svg>;
}

export function KnowledgeBrowser({ initial, initialSources, projectId, projectName }: { initialSources: ContextSources; initial: KnowledgeNode[]; projectId: string; projectName: string }) {
  const picker = useRef<HTMLInputElement>(null);
  const [mediaId, setMediaId] = useState<string | null>(null);
  const [sources, setSources] = useState(initialSources);
  const [nodes, setNodes] = useState(initial);
  const [addingProfile, setAddingProfile] = useState(false);
  const [profileName, setProfileName] = useState("");
  const [folderId, setFolderId] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [searchIds, setSearchIds] = useState<string[] | null>(null);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [pending, startTransition] = useTransition();
  const documentRequest = useRef(0);
  const [openId, setOpenId] = useState<string | null>(null);
  const [document, setDocument] = useState<DocumentContent | null>(null);
  const [versions, setVersions] = useState<DocumentVersion[]>([]);
  const [draft, setDraft] = useState("");
  const [documentError, setDocumentError] = useState("");
  const [editing, setEditing] = useState(false);
  const byId = useMemo(() => new Map(nodes.map((node) => [node.id, node])), [nodes]);
  const media = mediaId ? byId.get(mediaId) : undefined;
  const selected = selectedId ? byId.get(selectedId) : undefined;
  const folder = folderId ? byId.get(folderId) : undefined;
  const role = folder?.folder_role ?? "";
  const labelsByRole: Record<string, string> = { avatars: "Аватар", voices: "Голос", wardrobe: "Предмет одежды" };
  const folderLabel = labelsByRole[role] ?? "Папка";
  const mediaOnly = ["voice", "photos", "outfit"].includes(role);
  const folders = nodes.filter((node) => node.kind === "folder");
  const orderedFolders: KnowledgeNode[] = [];
  function visit(parentId: string | null) {
    folders.filter((node) => node.parent_id === parentId).sort((a, b) => a.name.localeCompare(b.name, "ru"))
      .forEach((node) => { orderedFolders.push(node); visit(node.id); });
  }
  visit(null);
  const visible = nodes.filter((node) => query ? (searchIds ? searchIds.includes(node.id) : node.name.toLocaleLowerCase("ru").includes(query.toLocaleLowerCase("ru"))) : node.parent_id === folderId)
    .sort((a, b) => Number(b.kind === "folder") - Number(a.kind === "folder") || a.name.localeCompare(b.name, "ru"));
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
        if (result.items) setNodes(result.items);
        setSelectedId(null);
        if (folderId && removed.has(folderId)) setFolderId(null);
      } else if (result.node) {
        const updated = result.node;
        if (result.items) setNodes(result.items);
        else setNodes(previous => action === "create" ? [...previous, updated] : previous.map(node => node.id === updated.id ? updated : node));
        setSelectedId(result.node.id);
        if (action === "create" && (updated.folder_role === "voice" || updated.folder_role === "avatar")) setAddingProfile(false);
        if (action === "create" && result.node.kind === "document") openDocument(result.node.id);
      }
    });
  }

  function create() {
    if (role === "voices" || role === "avatars") {
      setProfileName("");
      setError("");
      setAddingProfile(true);
      return;
    }
    const name = window.prompt(`Введите название («${folderLabel}»)`);
    if (name?.trim()) mutate("create", { parentId: folderId, name: name.trim(), kind: "folder" });
  }

  function createDocument() {
    const name = window.prompt("Название документа (.md или .txt)", "Новый документ.md");
    if (!name) return;
    if (!/\.(md|txt)$/i.test(name.trim())) { setError("Документ должен иметь расширение .md или .txt."); return; }
    mutate("create", { parentId: folderId, name: name.trim(), kind: "document" });
  }

  function openDocument(nodeId: string, version?: number) {
    const request = ++documentRequest.current;
    setOpenId(nodeId);
    setDocument(null);
    setDocumentError("");
    setEditing(false);
    startTransition(async () => {
      const result = await loadDocument(projectId, nodeId, version);
      if (request !== documentRequest.current) return;
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

  function enter(folder: string | null) {
    setAddingProfile(false);
    setFolderId(folder);
    setSelectedId(null);
    changeQuery("");
  }

  function open(node: KnowledgeNode) {
    if (node.kind === "folder") enter(node.id);
    else if (node.kind === "document") openDocument(node.id);
    else setMediaId(node.id);
  }

  function upload(files: File[], parent: string | null) {
    setError("");
    startTransition(async () => {
      try {
        for (const file of files) {
          const node = await uploadMedia(projectId, parent, file);
          setNodes(previous => [...previous, node]);
          setSelectedId(node.id);
        }
        setFolderId(parent);
        changeQuery("");
      } catch (e) { setError(e instanceof Error ? e.message : "Не удалось загрузить файл."); }
    });
  }

  function drop(event: React.DragEvent, parent: string | null) {
    event.preventDefault();
    event.stopPropagation();
    if (pending) return;
    if (event.dataTransfer.files.length) { upload(Array.from(event.dataTransfer.files), parent); return; }
    const item = byId.get(event.dataTransfer.getData("application/x-knowledge-node"));
    if (item && item.id !== parent && item.parent_id !== parent) {
      mutate("move", { nodeId: item.id, revision: item.revision, parentId: parent });
    }
  }

  function examples() {
    setError("");
    startTransition(async () => {
      const result = await exampleFiles(projectId);
      if (!result.data) { setError(result.error); return; }
      setNodes(previous => [...previous, ...result.data.items]);
      enter(result.data.items[0].id);
    });
  }

  const labels = { folder: "Папка", document: "Документ", image: "Изображение", video: "Видео", audio: "Аудио", file: "PDF" };
  return (
    <section
      className="min-h-[560px] overflow-hidden rounded-[18px] border border-line bg-surface"
      aria-label="База знаний проекта"
    >
      <div className="flex items-center justify-between gap-4 border-b border-line px-[22px] py-4 max-[761px]:flex-wrap">
        <nav
          className="flex flex-wrap gap-1 text-muted [&_button]:py-[3px] [&_button]:font-bold [&_button]:text-ink"
          aria-label="Путь к папке"
        >
          <button onClick={() => enter(null)} type="button">
            {projectName}
          </button>
          {crumbs.map((node) => (
            <span key={node.id}>
              {" "}
              /{" "}
              <button onClick={() => enter(node.id)} type="button">
                {node.name}
              </button>
            </span>
          ))}
        </nav>
        <input
          className="w-full max-w-60 min-h-9 rounded-[9px] border border-line bg-control px-2.5 py-[7px] text-ink"
          aria-label="Поиск папок и документов"
          maxLength={200}
          onChange={(event) => changeQuery(event.target.value)}
          placeholder="Поиск по названию и тексту"
          type="search"
          value={query}
        />
      </div>
      <div className="grid min-h-[500px] grid-cols-[230px_minmax(0,1fr)] max-[761px]:grid-cols-1">
        <aside
          className="flex max-h-[75vh] flex-col gap-[3px] overflow-auto border-r border-line px-2.5 py-[18px] max-[761px]:max-h-[180px] max-[761px]:border-r-0 max-[761px]:border-b"
          aria-label="Папки"
        >
          <strong className="px-3 pb-3 text-[10px] tracking-[.1em] text-faint">ПАПКИ</strong>
          <button
            className={folderButton}
            onDragOver={(event) => event.preventDefault()}
            onDrop={(event) => drop(event, null)}
            aria-current={folderId === null ? "page" : undefined}
            onClick={() => enter(null)}
            type="button"
          >
            <FolderIcon />
            {projectName}
          </button>
          {orderedFolders.map((node) => (
            <button
              className={folderButton}
              onDragOver={(event) => event.preventDefault()}
              onDrop={(event) => drop(event, node.id)}
              aria-current={folderId === node.id ? "page" : undefined}
              key={node.id}
              onClick={() => enter(node.id)}
              style={{ "--folder-depth": depth(node, byId) } as CSSProperties}
              type="button"
            >
              <FolderIcon />
              {node.name}
            </button>
          ))}
        </aside>
        <div
          className="min-w-0 p-[23px]"
          onDragOver={(event) => event.preventDefault()}
          onDrop={(event) => drop(event, folderId)}
        >
          <div className="mb-5 flex items-center justify-between gap-[15px] max-[901px]:flex-col max-[901px]:items-start">
            <div>
              <span className={eyebrow}>{query ? "Результаты поиска" : "Содержимое папки"}</span>
              <h2 className="my-1 text-xl">{query ? "Поиск" : (folder?.name ?? projectName)}</h2>
              <p className="text-muted">{searching ? "Ищем…" : `${visible.length} элементов`}</p>
            </div>
            <div className="flex flex-wrap items-center justify-end gap-2 max-[901px]:justify-start">
              <input
                hidden
                ref={picker}
                type="file"
                multiple
                accept={role === "voice" ? "audio/*" : ["photos", "outfit"].includes(role) ? "image/*" : acceptedMedia}
                aria-label="Выберите файлы для загрузки"
                onChange={(event) => {
                  upload(Array.from(event.target.files || []), folderId);
                  event.target.value = "";
                }}
              />
              <button className={secondaryButton} disabled={pending || role === "wardrobe"} onClick={() => picker.current?.click()}>
                Загрузить файл
              </button>
              <button className={secondaryButton} disabled={pending || mediaOnly} onClick={create} type="button">
                + {folderLabel}
              </button>
              <button className={primaryButton} disabled={pending || mediaOnly || role === "wardrobe"} onClick={createDocument} type="button">
                + Документ
              </button>
            </div>
          </div>
          {addingProfile && (role === "voices" || role === "avatars") && (
            <form className="mb-5 flex flex-wrap items-end gap-2" onSubmit={event => {
              event.preventDefault();
              const name = profileName.trim();
              if (name && !pending) mutate("create", { parentId: folderId, name, kind: "folder" });
            }}>
              <label className={fieldLabel}>{role === "voices" ? "Имя голоса" : "Имя аватара"}
                <input className={field} autoFocus required maxLength={160} value={profileName}
                  onChange={event => setProfileName(event.target.value)} />
              </label>
              <button className={primaryButton} disabled={pending || !profileName.trim()}>Создать</button>
              <button className={secondaryButton} type="button" disabled={pending} onClick={() => setAddingProfile(false)}>Отмена</button>
            </form>
          )}
          {!query && folder && (folder.folder_role === "avatar" || folder.folder_role === "voice") && (
            <FolderProfile key={folder.id} project={projectId} folder={folder}
              voices={folders.filter(node => node.folder_role === "voice")}
              onSave={updated => setNodes(previous => previous.map(node => node.id === updated.id ? updated : node))} />
          )}
          {folderId === null && !query && !nodes.some((n) => !n.parent_id && n.name === "Пример проекта") && (
            <button className={`${secondaryButton} mb-3`} onClick={examples} disabled={pending}>
              Добавить примеры материалов
            </button>
          )}
          {pending && <span role="status"> Выполняется…</span>}
          <div className="grid gap-[5px]">
            {visible.length ? (
              visible.map((node) => (
                <button
                  aria-pressed={selectedId === node.id}
                  className="grid w-full grid-cols-[36px_1fr_auto] items-center gap-3 rounded-[10px] border border-transparent p-3 text-left text-ink hover:bg-subtle aria-pressed:border-accent aria-pressed:bg-tint"
                  key={node.id}
                  draggable={!pending}
                  onDragStart={(event) => event.dataTransfer.setData("application/x-knowledge-node", node.id)}
                  onDrop={node.kind === "folder" ? (event) => drop(event, node.id) : undefined}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") {
                      event.preventDefault();
                      open(node);
                    }
                  }}
                  onClick={() => setSelectedId(node.id)}
                  onDoubleClick={() => open(node)}
                  type="button"
                >
                  <span aria-hidden="true">
                    {node.kind === "folder" ? (
                      <FolderIcon />
                    ) : node.kind === "document" ? (
                      <FileIcon />
                    ) : (
                      <svg className="h-[29px] w-6 flex-none text-accent" viewBox="0 0 36 42">
                        <rect x="3" y="5" width="30" height="32" rx="6" fill="currentColor" opacity=".15" />
                        <path d="m14 13 12 8-12 8z" fill="currentColor" />
                      </svg>
                    )}
                  </span>
                  <span>
                    <strong className="block">{node.name}</strong>
                    <small className="block text-muted">
                      {query ? nodePath(node, byId, projectName) : labels[node.kind]}
                    </small>
                  </span>
                  <span aria-hidden="true">›</span>
                </button>
              ))
            ) : (
              <p className={kbEmpty}>Здесь пока нет файлов и папок.</p>
            )}
          </div>
          {searchError && (
            <p className={formError} role="alert">
              {searchError}
            </p>
          )}
          {selected && (
            <div className="mt-[22px] flex flex-wrap items-center justify-between gap-3 border-t border-line pt-[18px]">
              <strong>{selected.name}</strong>
              <div className="flex flex-wrap items-center gap-2">
                <button className={secondaryButton} onClick={() => open(selected)} type="button">
                  Открыть
                </button>
                <button className={secondaryButton} disabled={pending} onClick={rename} type="button">
                  Переименовать
                </button>
                <label className="flex items-center gap-[7px] text-muted">
                  Переместить в{" "}
                  <select
                    className="min-h-9 rounded-[9px] border border-line bg-control px-2.5 py-[7px] text-ink"
                    disabled={pending}
                    onChange={(event) => move(event.target.value)}
                    value={selected.parent_id ?? ""}
                  >
                    <option value="">{projectName}</option>
                    {folders
                      .filter((item) => item.id !== selected.id)
                      .map((item) => (
                        <option key={item.id} value={item.id}>
                          {item.name}
                        </option>
                      ))}
                  </select>
                </label>
                <button className={secondaryButton} disabled={pending} onClick={archive} type="button">
                  Архивировать
                </button>
              </div>
            </div>
          )}
          {error && (
            <p className={formError} role="alert">
              {error}
            </p>
          )}
        </div>
      </div>
      {media && (
        <MediaPreview
          key={media.id}
          project={projectId}
          node={media}
          voiceSample={!!media.parent_id && byId.get(media.parent_id)?.folder_role === "voice"}
          path={nodePath(media, byId, projectName)}
          onChange={(updated) =>
            setNodes((previous) => previous.map((n) => (n.id === updated.id ? updated : n)))
          }
          onClose={() => setMediaId(null)}
        />
      )}
      {openId && (
        <div
          className="fixed inset-0 z-40 grid place-items-center bg-[#081528b8] p-[15px]"
          role="presentation"
        >
          <div
            aria-labelledby="kb-document-title"
            aria-modal="true"
            className="flex max-h-[88vh] w-full max-w-[800px] flex-col overflow-hidden rounded-2xl border border-line bg-surface shadow-[0_25px_80px_#0006]"
            onKeyDown={(event) => {
              if (event.key === "Escape") {
                setOpenId(null);
                setDocument(null);
                setEditing(false);
              }
            }}
            role="dialog"
          >
            <div className={kbDocumentHead}>
              <div>
                <span className={eyebrow}>Документ</span>
                <h2 className="mt-1 text-lg" id="kb-document-title">
                  {byId.get(openId)?.name ?? "Документ"}
                </h2>
              </div>
              <button
                aria-label="Закрыть документ"
                autoFocus
                className={`${secondaryButton} text-[22px]`}
                onClick={() => {
                  setOpenId(null);
                  setDocument(null);
                  setEditing(false);
                }}
                type="button"
              >
                ×
              </button>
            </div>
            {document ? (
              <>
                <div className="grid min-h-[280px] grid-cols-[minmax(0,1fr)_180px] overflow-auto max-[561px]:grid-cols-1">
                  <div className="min-w-0">
                    {editing ? (
                      <DocumentEditor
                        project={projectId}
                        images={nodes.filter((n) => n.kind === "image")}
                        draft={draft}
                        markdown={document.format === "markdown"}
                        setDraft={setDraft}
                      />
                    ) : document.format === "markdown" && document.content ? (
                      <article className="wrap-anywhere p-6 [&_:is(h1,h2,h3)]:mt-[1em] [&_:is(h1,h2,h3)]:mb-[.4em] [&_:is(h1,h2,h3)]:font-bold [&_h1]:text-[1.65rem] [&_h2]:text-[1.3rem] [&_p]:my-[.75em] [&_:is(ul,ol)]:pl-[1.6em] [&_ul]:list-disc [&_ol]:list-decimal [&_a]:text-accent [&_a]:underline [&_img]:max-h-[45vh]">
                        <Markdown>{document.content}</Markdown>
                      </article>
                    ) : (
                      <pre className="wrap-anywhere p-[26px] font-mono leading-[1.8] whitespace-pre-wrap">
                        {document.content || "Документ пуст."}
                      </pre>
                    )}
                  </div>
                  <aside className="flex flex-col gap-[5px] border-l border-line px-3 py-5 max-[561px]:max-h-[150px] max-[561px]:overflow-auto max-[561px]:border-t max-[561px]:border-l-0">
                    <small className="block text-muted">
                      {document.format === "plain" ? "Текст" : "Markdown"} · {shownVersion?.size_bytes ?? 0} Б
                    </small>
                    <strong className="px-2 pb-2 text-[11px]">История версий</strong>
                    {versions.map((item) => (
                      <button
                        className="rounded-lg p-2 text-left text-ink hover:bg-tint hover:text-accent aria-[current=page]:bg-tint aria-[current=page]:text-accent"
                        aria-current={document.version === item.version ? "page" : undefined}
                        key={item.id}
                        onClick={() => openDocument(openId, item.version)}
                        type="button"
                      >
                        Версия {item.version}
                        <small className="block text-muted">
                          {new Date(item.created_at).toLocaleString("ru-RU")}
                        </small>
                      </button>
                    ))}
                    {versions.length === 0 && <p className="text-muted">Версий пока нет.</p>}
                  </aside>
                </div>
                <div className={kbDocumentFoot}>
                  <span>Версия {document.version || "не сохранён"}</span>
                  <div className="flex items-center gap-2">
                    {shownVersion && !editing && (
                      <button
                        aria-pressed={Boolean(linked)}
                        className={secondaryButton}
                        disabled={pending}
                        onClick={toggleSource}
                        type="button"
                      >
                        {linked ? "Убрать из источников контекста" : "Добавить в источники контекста"}
                      </button>
                    )}
                    {document.version > 0 && document.version !== versions[0]?.version && (
                      <button className={secondaryButton} onClick={() => openDocument(openId)} type="button">
                        Текущая версия
                      </button>
                    )}
                    {editing ? (
                      <>
                        <button
                          className={secondaryButton}
                          onClick={() => {
                            setEditing(false);
                            setDraft(document.content);
                          }}
                          type="button"
                        >
                          Отменить
                        </button>
                        <button
                          className={primaryButton}
                          disabled={pending}
                          onClick={saveOpenDocument}
                          type="button"
                        >
                          {pending ? "Сохраняем…" : "Сохранить"}
                        </button>
                      </>
                    ) : (
                      (document.version === 0 || document.version === versions[0]?.version) && (
                        <button
                          className={secondaryButton}
                          onClick={() => {
                            setEditing(true);
                            setDraft(document.content);
                          }}
                          type="button"
                        >
                          Редактировать
                        </button>
                      )
                    )}
                  </div>
                </div>
              </>
            ) : (
              <p className={kbEmpty}>
                {pending ? "Открываем документ…" : documentError || "Не удалось открыть документ."}
              </p>
            )}
            {documentError && document && (
              <p className={`${formError} px-[23px] pb-[18px]`} role="alert">
                {documentError}
              </p>
            )}
          </div>
        </div>
      )}
    </section>
  );
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
