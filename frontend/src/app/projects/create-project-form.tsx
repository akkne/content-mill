"use client";
import { useTranslator } from "@/app/interface-language";

import { projectField, fieldLabel, formError, primaryButton, projectCreateRow } from "@/app/ui-styles";
import { useState, useTransition } from "react";

import { createProject } from "./actions";

export function CreateProjectForm() {
  const t = useTranslator();
  const [error, setError] = useState("");
  const [pending, startTransition] = useTransition();
  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        setError("");
        const data = new FormData(event.currentTarget);
        startTransition(async () => setError(await createProject(data)));
      }}
    >
      <label className={fieldLabel} htmlFor="project-name">
        {t("Название", "Name")}
      </label>
      <div className={projectCreateRow}>
        <input
          className={projectField}
          id="project-name"
          maxLength={160}
          name="name"
          placeholder={t("Например, бренд одежды", "For example, a clothing brand")}
          required
        />
        <button className={`${primaryButton} flex-none`} disabled={pending} type="submit">
          {pending ? t("Создаём…", "Creating…") : t("Создать проект", "Create project")}
        </button>
      </div>
      {error && (
        <p className={formError} role="alert">
          {error}
        </p>
      )}
    </form>
  );
}
