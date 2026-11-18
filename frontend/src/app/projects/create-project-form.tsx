"use client";

import { projectField, fieldLabel, formError, primaryButton, projectCreateRow } from "@/app/ui-styles";
import { useState, useTransition } from "react";

import { createProject } from "./actions";

export function CreateProjectForm() {
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
        Название
      </label>
      <div className={projectCreateRow}>
        <input
          className={projectField}
          id="project-name"
          maxLength={160}
          name="name"
          placeholder="Например, бренд одежды"
          required
        />
        <button className={`${primaryButton} flex-none`} disabled={pending} type="submit">
          {pending ? "Создаём…" : "Создать проект"}
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
