"use client";
import { useState, useTransition } from "react";
import { useTranslator } from "@/app/interface-language";
import { secondaryButton } from "@/app/ui-styles";
import type { Project } from "@/lib/projects";
import { assignAvatar } from "./actions";

export function AvatarProjects({
  avatar,
  projects,
  assigned,
}: {
  avatar: string;
  projects: Project[];
  assigned: string[];
}) {
  const t = useTranslator();
  const [selected, setSelected] = useState<string[]>([]);
  const [saved, setSaved] = useState<string[]>([]);
  const [message, setMessage] = useState("");
  const [pending, start] = useTransition();
  return (
    <fieldset
      disabled={pending}
      className="mb-5 grid gap-2 rounded-xl border border-line p-4"
    >
      <legend className="font-bold">
        {t("Добавить в проекты", "Add to projects")}
      </legend>
      <p className="text-sm text-muted">
        {t(
          "Проект получит копию текущих фотографий, одежды, документов и выбранного голоса.",
          "Each project receives a copy of the current photos, wardrobe, documents and assigned voice.",
        )}
      </p>
      {projects.map((p) => (
        <label key={p.id} className="flex gap-2">
          <input
            type="checkbox"
            disabled={assigned.includes(p.id) || saved.includes(p.id)}
            checked={assigned.includes(p.id) || selected.includes(p.id) || saved.includes(p.id)}
            onChange={(e) =>
              setSelected(
                e.target.checked
                  ? [...selected, p.id]
                  : selected.filter((id) => id !== p.id),
              )
            }
          />
          {p.name}{(assigned.includes(p.id) || saved.includes(p.id)) && <span className="text-muted">{t("Уже добавлен", "Already added")}</span>}
        </label>
      ))}
      <button
        type="button"
        disabled={!selected.length}
        className={secondaryButton + " w-fit"}
        onClick={() =>
          start(async () => {
            setMessage("");
            for (const id of selected) {
              const error = await assignAvatar(avatar, id);
              if (error) {
                setMessage(error);
                return;
              }
              setSaved((prev) => [...prev, id]);
              setSelected((prev) => prev.filter((p) => p !== id));
            }
            setMessage(t("Аватар добавлен.", "Avatar added."));
          })
        }
      >
        {t("Добавить в проект", "Add to project")}
      </button>
      <span role="status">{message}</span>
    </fieldset>
  );
}
