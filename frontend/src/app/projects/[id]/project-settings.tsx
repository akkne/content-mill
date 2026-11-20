"use client";
import { useTranslator } from "@/app/interface-language";

import { projectField, fieldLabel, primaryButton, projectCreateRow, workPanel } from "@/app/ui-styles";
import { useState, useTransition } from "react";
import type { Project } from "@/lib/projects";
import { renameProject } from "../actions";

export function ProjectSettings({ project }: { project: Project }) {
  const t = useTranslator();
  const [name, setName] = useState(project.name);
  const [message, setMessage] = useState("");
  const [pending, startTransition] = useTransition();
  return (
    <details className={workPanel}>
      <summary>{t("Параметры проекта", "Project settings")}</summary>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          startTransition(async () =>
            setMessage((await renameProject(project.id, project.revision, name)) || t("Название сохранено.", "Name saved.")),
          );
        }}
      >
        <label className={fieldLabel} htmlFor="project-title">
          {t("Название проекта", "Project name")}
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
            {pending ? t("Сохраняем…", "Saving…") : t("Сохранить название", "Save name")}
          </button>
        </div>
        <p role="status">{message}</p>
      </form>
    </details>
  );
}
