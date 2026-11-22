"use client";

import { useRef, useState } from "react";
import { useTranslator } from "@/app/interface-language";
import { primaryButton, secondaryButton } from "@/app/ui-styles";
import type { VideoOptions, VideoSource } from "@/lib/videos";
import { FileIcon, FolderIcon } from "../../knowledge/file-icons";

type Folders = VideoOptions["folders"];

export function resolveMaterials(selection: string[], folders: Folders, sources: VideoSource[]) {
  const chosen = new Set(selection);
  const parents = new Map(folders.map(folder => [folder.id, folder.parent_id]));
  const latest = new Map<string, VideoSource>();
  const versions = new Set<string>();
  for (const source of sources) {
    if (chosen.has(source.id)) versions.add(source.id);
    let parent = source.parent_id;
    while (parent && !chosen.has(parent)) parent = parents.get(parent);
    if (parent) {
      const node = source.node_id ?? source.id;
      if ((latest.get(node)?.version ?? 0) < source.version) latest.set(node, source);
    }
  }
  for (const source of latest.values()) versions.add(source.id);
  return versions;
}

export function MaterialPicker({ project, folders, sources, selection, onChange, disabled }: {
  project: string;
  folders: Folders;
  sources: VideoSource[];
  selection: string[];
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
  const count = resolveMaterials(draft, folders, sources).size;
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
      className="fixed inset-0 m-auto w-[min(48rem,calc(100%-1rem))] max-w-none rounded-2xl border border-line bg-surface p-0 text-ink shadow-2xl backdrop:bg-black/50 backdrop:backdrop-blur-sm">
      <div className="flex h-[min(37rem,88dvh)] flex-col">
        <header className="flex items-start justify-between gap-4 border-b border-line px-5 py-4">
          <div><h2 id="material-picker-title" className="text-xl font-extrabold">{t("База знаний", "Knowledge base")}</h2>
            <p className="mt-1 text-sm text-muted">{t("Выберите файлы или папки целиком. Двойной клик открывает папку.", "Select files or entire folders. Double-click a folder to open it.")}</p>
          </div>
          <button type="button" className={secondaryButton} aria-label={t("Закрыть", "Close")} onClick={() => dialog.current?.close()}>×</button>
        </header>
        <nav aria-label={t("Путь к папке", "Folder path")} className="flex flex-wrap items-center gap-1 border-b border-line bg-subtle px-5 py-2 text-sm font-bold">
          {[{ id: null, name: project }, ...crumbs].map((folder, index) => <span key={folder.id ?? "root"} className="flex min-w-0 items-center gap-1">
            {index > 0 && <span aria-hidden="true" className="text-faint">›</span>}
            <button type="button" className="truncate rounded px-1 py-1 text-accent aria-current:text-ink"
              aria-current={folder.id === location ? "location" : undefined} onClick={() => setLocation(folder.id)}>{folder.name}</button>
          </span>)}
        </nav>
        <div className="min-h-0 flex-1 overflow-auto p-4">
          <ul className="grid grid-cols-[repeat(auto-fill,minmax(8rem,1fr))] gap-2">
            {visible.map(entry => <li key={entry.id} className="relative">
              <button type="button" aria-pressed={draft.includes(entry.id)} onClick={() => toggle(entry.id)}
                onDoubleClick={entry.folder ? () => setLocation(entry.id) : undefined}
                className="flex h-full min-h-28 w-full select-none flex-col items-center justify-center gap-2 rounded-xl border border-transparent px-2 py-3 text-center hover:bg-subtle aria-pressed:border-accent aria-pressed:bg-tint">
                {entry.folder ? <FolderIcon /> : <FileIcon />}
                <span className="line-clamp-2 break-all text-sm font-bold" title={entry.name}>{entry.name}</span>
                {!entry.folder && <span className="text-xs text-muted">v{entry.version}</span>}
              </button>
              {entry.folder && <button type="button" aria-label={t("Открыть папку ", "Open folder ") + entry.name}
                title={t("Открыть папку", "Open folder")} onClick={() => setLocation(entry.id)}
                className="absolute top-1 right-1 size-8 rounded-lg text-xl text-muted hover:bg-control hover:text-ink">›</button>}
            </li>)}
          </ul>
          {!visible.length && <p className="py-12 text-center text-muted">{t("В этой папке пока нет материалов.", "This folder has no materials yet.")}</p>}
        </div>
        <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-line px-5 py-3">
          <span role="status" className="text-sm text-muted">{count > 100 ? t("Можно добавить до 100 файлов.", "Select up to 100 files.") : totalLabel + " · " + count}</span>
          <div className="ml-auto flex gap-2">
            <button type="button" className={secondaryButton} onClick={() => dialog.current?.close()}>{t("Отмена", "Cancel")}</button>
            {(draft.length > 0 || selection.length > 0) && <button type="button" className={primaryButton}
              disabled={count > 100 || (draft.length > 0 && count === 0)} onClick={() => { onChange(draft); dialog.current?.close(); }}>{choose}</button>}
          </div>
        </footer>
      </div>
    </dialog>
  </section>;
}
