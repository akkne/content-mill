"use client";

import { useState, useTransition } from "react";
import type { Project } from "@/lib/projects";
import { renameProject } from "../actions";

export function ProjectSettings({ project }: { project: Project }) {
  const [name, setName] = useState(project.name);
  const [message, setMessage] = useState("");
  const [pending, startTransition] = useTransition();
  return <details className="work-panel project-create">
    <summary>Параметры проекта</summary>
    <form onSubmit={(event) => {
      event.preventDefault();
      startTransition(async () => setMessage(await renameProject(project.id, project.revision, name) || "Название сохранено."));
    }}>
      <label htmlFor="project-title">Название проекта</label>
      <div className="project-create-row">
        <input id="project-title" value={name} maxLength={160} required disabled={pending}
          onChange={(event) => { setName(event.target.value); setMessage(""); }} />
        <button className="primary-button" disabled={pending || !name.trim() || name.trim() === project.name}>
          {pending ? "Сохраняем…" : "Сохранить название"}
        </button>
      </div>
      <p role="status">{message}</p>
    </form>
  </details>;
}
