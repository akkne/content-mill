"use client";

import { useRef, useState } from "react";
import { useTranslator } from "@/app/interface-language";
import { primaryButton, secondaryButton } from "@/app/ui-styles";
import type { VideoOptions, VideoSource } from "@/lib/videos";
import { FileIcon, FolderIcon } from "../../knowledge/file-icons";

type Folders = VideoOptions["folders"];

export function resolveMaterials(selection: string[], folders: Folders, sources: VideoSource[], avatarFolders: Set<string>) {
  const chosen = new Set(selection);
  const parents = new Map(folders.map(folder => [folder.id, folder.parent_id]));
  const latest = new Map<string, VideoSource>();
  const versions = new Set<string>();
  const pinnedNodes = new Set(sources.filter(source => chosen.has(source.id)).map(source => source.node_id));
  for (const source of sources) {
    if (chosen.has(source.id)) versions.add(source.id);
    let parent = source.parent_id;
    while (parent) {
      const includeAvatar = source.character_id === parent && !pinnedNodes.has(source.node_id);
      if (chosen.has(parent) && (!avatarFolders.has(parent) || includeAvatar)) break;
      parent = parents.get(parent);
    }
    if (parent) {
      const node = source.node_id ?? source.id;
      if ((latest.get(node)?.version ?? 0) < source.version) latest.set(node, source);
    }
  }
  for (const source of latest.values()) versions.add(source.id);
  return versions;
}

export function MaterialPicker({ project, folders, sources, selection, avatarFolders, onChange, disabled }: {
  project: string;
  folders: Folders;
  sources: VideoSource[];
  selection: string[];
  avatarFolders: Set<string>;
  onChange: (selection: string[]) => void;
  disabled: boolean;
}) {
  const t = useTranslator();
  const dialog = useRef<HTMLDialogElement>(null);
  const [draft, setDraft] = useState<string[]>([]);
  const [location, setLocation] = useState<string | null>(null);
  const folderById = new Map(folders.map(folder => [folder.id, folder]));
  const entries = [
    ...folders.map(folder => ({ ...folder, folder: true, version: 0 })),
    ...sources.map(file => ({ ...file, folder: false, version: file.version })),
  ];
  const byId = new Map(entries.map(entry => [entry.id, entry]));
  const visible = entries.filter(entry => (entry.parent_id ?? null) === location)
    .sort((a, b) => Number(b.folder) - Number(a.folder) || a.name.localeCompare(b.name) || b.version - a.version);
  const crumbs = [];
  for (let folder = location && folderById.get(location); folder; folder = folder.parent_id && folderById.get(folder.parent_id)) {
    crumbs.unshift(folder);
  }
  const included = resolveMaterials(draft, folders, sources, avatarFolders);
  const count = included.size;
  const openPath = new Set(crumbs.map(folder => folder.id));
  const children = new Map<string | null, Folders>();
  for (const folder of folders) {
    const siblings = children.get(folder.parent_id) ?? [];
    siblings.push(folder);
    children.set(folder.parent_id, siblings);
  }
  function folderList(parent: string | null) {
    return <ul className={parent ? "ml-2 border-l border-line pl-1" : ""}>
      {children.get(parent)?.map(folder => <li key={folder.id}>
        <button type="button" title={folder.name} aria-current={location === folder.id ? "location" : undefined}
          onClick={() => setLocation(folder.id)}
          className="flex min-h-9 w-full items-center gap-1.5 rounded-lg px-1.5 text-left text-sm hover:bg-control aria-current:bg-tint aria-current:font-bold aria-current:text-accent">
          <span aria-hidden="true" className="w-2 shrink-0 text-faint">{children.has(folder.id) ? openPath.has(folder.id) ? "⌄" : "›" : ""}</span>
          <FolderIcon /><span className="truncate">{folder.name}</span>
        </button>
        {openPath.has(folder.id) && children.has(folder.id) && folderList(folder.id)}
      </li>)}
    </ul>;
  }
  const totalLabel = t("Файлов", "Files");
  const choose = t("Выбрать", "Select");
  function toggle(id: string) {
    setDraft(previous => previous.includes(id) ? previous.filter(key => key !== id) : [...previous, id]);
  }

  return <section className="rounded-xl border border-line p-4">
    <div className="flex flex-wrap items-center justify-between gap-3">
      <h2 className="font-bold">{t("Материалы из базы знаний", "Knowledge base materials")}</h2>
      <button type="button" disabled={disabled} className={secondaryButton} onClick={() => {
        setDraft(selection);
        setLocation(null);
        dialog.current?.showModal();
      }}>{t("Открыть базу знаний", "Open knowledge base")}</button>
    </div>
    {selection.length > 0 && <ul className="mt-3 flex max-h-40 flex-wrap gap-2 overflow-auto">
      {selection.map(id => {
        const entry = byId.get(id);
        if (!entry) return null;
        return <li key={id} className="flex max-w-full items-center gap-2 rounded-lg bg-control px-2 py-1 text-sm">
          {entry.folder ? <FolderIcon /> : <FileIcon />}
          <span className="truncate">{entry.name}{!entry.folder && ' · v' + entry.version}</span>
          <button type="button" disabled={disabled} className="rounded px-1 text-muted hover:text-ink"
            aria-label={t("Убрать ", "Remove ") + entry.name} onClick={() => onChange(selection.filter(key => key !== id))}>×</button>
        </li>;
      })}
    </ul>}
    <dialog ref={dialog} aria-labelledby="material-picker-title"
      className="fixed inset-0 m-auto w-[min(62rem,calc(100%-1rem))] max-w-none rounded-2xl border border-line bg-surface p-0 text-ink shadow-2xl backdrop:bg-black/50 backdrop:backdrop-blur-sm">
      <div className="flex h-[min(43rem,90dvh)] flex-col">
        <header className="flex items-start justify-between gap-4 border-b border-line px-5 py-4">
          <div><h2 id="material-picker-title" className="text-xl font-extrabold">{t("База знаний", "Knowledge base")}</h2>
            <p className="mt-1 text-sm text-muted">{t("Откройте папку слева и выберите материалы справа.", "Open a folder on the left and select materials on the right.")}</p>
          </div>
          <button type="button" className={secondaryButton} aria-label={t("Закрыть", "Close")} onClick={() => dialog.current?.close()}>×</button>
        </header>
        <div className="grid min-h-0 flex-1 grid-cols-[minmax(7rem,34%)_minmax(0,1fr)] sm:grid-cols-[15rem_minmax(0,1fr)]">
          <nav aria-label={t("Папки", "Folders")} className="overflow-auto border-r border-line bg-subtle p-1.5 sm:p-3">
            <button type="button" onClick={() => setLocation(null)} aria-current={location === null ? "location" : undefined}
              className="mb-2 w-full truncate rounded-lg px-2 py-2 text-left font-bold hover:bg-control aria-current:bg-tint aria-current:text-accent">{project}</button>
            {folderList(null)}
          </nav>
          <section aria-label={t("Содержимое папки", "Folder contents")} className="flex min-h-0 flex-col">
            <header className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-3 py-3 sm:px-5">
              <div className="min-w-0">
                {location && <p className="truncate text-xs text-muted">{[project, ...crumbs.slice(0,-1).map(f => f.name)].join(" › ")}</p>}
                <h3 className="break-words font-bold">{crumbs.at(-1)?.name ?? project}</h3>
              </div>
              {location && <button type="button" aria-pressed={draft.includes(location)} onClick={() => toggle(location)}
                className={secondaryButton + " text-xs aria-pressed:bg-tint aria-pressed:text-accent"}>
                {draft.includes(location) ? t("✓ Папка выбрана", "✓ Folder selected") : t("Выбрать папку", "Select folder")}
              </button>}
            </header>
            <div className="min-h-0 flex-1 overflow-auto p-1.5 sm:p-3">
              <ul className="space-y-1">
                {visible.map(entry => <li key={entry.id} className="flex items-center">
                  <button type="button" aria-pressed={draft.includes(entry.id)}
                    onClick={() => toggle(entry.id)} onDoubleClick={entry.folder ? () => setLocation(entry.id) : undefined}
                    className="flex min-h-11 min-w-0 flex-1 items-center gap-2 rounded-lg px-2 text-left text-sm hover:bg-subtle aria-pressed:bg-tint aria-pressed:text-accent">
                    {entry.folder ? <FolderIcon /> : <FileIcon />}
                    <span className="min-w-0 flex-1 break-words">{entry.name}</span>
                    {!entry.folder && <small className="text-muted">v{entry.version}</small>}
                    {(draft.includes(entry.id) || included.has(entry.id)) && <span aria-label={t("В контексте", "In context")} className="text-accent">✓</span>}
                  </button>
                  {entry.folder && <button type="button" aria-label={t("Открыть папку ", "Open folder ") + entry.name}
                    onClick={() => setLocation(entry.id)} className="size-9 shrink-0 rounded-lg text-lg text-muted hover:bg-control">›</button>}
                </li>)}
              </ul>
              {!visible.length && <p className="p-4 text-sm text-muted">{t("Папка пуста", "This folder is empty")}</p>}
            </div>
          </section>
        </div>
        <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-line px-5 py-3">
          <span role="status" className="text-sm text-muted">{count > 100 ? t("Можно добавить до 100 файлов.", "Select up to 100 files.") : totalLabel + " · " + count}</span>
          <div className="ml-auto flex gap-2">
            <button type="button" className={secondaryButton} onClick={() => dialog.current?.close()}>{t("Отмена", "Cancel")}</button>
            {(draft.length > 0 || selection.length > 0) && <button type="button" className={primaryButton}
              disabled={count > 100} onClick={() => { onChange(draft); dialog.current?.close(); }}>{choose}</button>}
          </div>
        </footer>
      </div>
    </dialog>
  </section>;
}
