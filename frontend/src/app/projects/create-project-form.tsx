"use client";

import { useState, useTransition } from "react";

import { createProject } from "./actions";

export function CreateProjectForm() {
  const [error, setError] = useState("");
  const [pending, startTransition] = useTransition();
  return <form onSubmit={(event) => {
    event.preventDefault();
    setError("");
    const data = new FormData(event.currentTarget);
    startTransition(async () => setError(await createProject(data)));
  }}>
    <label htmlFor="project-name">Название</label>
    <div className="project-create-row"><input id="project-name" maxLength={160} name="name" placeholder="Например, бренд одежды" required /><button className="primary-button" disabled={pending} type="submit">{pending ? "Создаём…" : "Создать проект"}</button></div>
    {error && <p className="form-error" role="alert">{error}</p>}
  </form>;
}
