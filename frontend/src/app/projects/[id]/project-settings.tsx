"use client";

import { projectField, fieldLabel, primaryButton, projectCreateRow, workPanel } from "@/app/ui-styles";
import { useState, useTransition } from "react";
import type { Project } from "@/lib/projects";
import { renameProject } from "../actions";

export function ProjectSettings({ project }: { project: Project }) {
  const [name, setName] = useState(project.name);
  const [message, setMessage] = useState("");
  const [pending, startTransition] = useTransition();
  return (
    <details className={workPanel}>
      <summary>Параметры проекта</summary>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          startTransition(async () =>
            setMessage((await renameProject(project.id, project.revision, name)) || "Название сохранено."),
          );
        }}
      >
        <label className={fieldLabel} htmlFor="project-title">
          Название проекта
        </label>
        <div className={projectCreateRow}>
          <input
            className={projectField}
            id="project-title"
            value={name}
            maxLength={160}
            required
            disabled={pending}
            onChange={(event) => {
              setName(event.target.value);
              setMessage("");
            }}
          />
          <button
            className={`${primaryButton} flex-none`}
            disabled={pending || !name.trim() || name.trim() === project.name}
          >
            {pending ? "Сохраняем…" : "Сохранить название"}
          </button>
        </div>
        <p role="status">{message}</p>
      </form>
    </details>
  );
}
