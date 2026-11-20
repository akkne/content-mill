"use client";
import { useTranslator } from "@/app/interface-language";

import { useState, useTransition } from "react";
import { field, primaryButton, secondaryButton, workPanel } from "@/app/ui-styles";
import { manageAgentToken } from "../actions";

export function AgentAccess({ projectId }: { projectId: string }) {
  const t = useTranslator();
  const [token, setToken] = useState("");
  const [notice, setNotice] = useState("");
  const [pending, start] = useTransition();
  function change(action: "issue" | "revoke") {
    start(async () => {
      const result = await manageAgentToken(projectId, action);
      setToken(result.token ?? "");
      setNotice(result.message);
    });
  }
  return <details className={workPanel}>
    <summary>{t("Доступ агента по MCP", "MCP agent access")}</summary>
    <p className="my-3 text-muted">{t("Claude Code и Codex смогут читать файлы этого проекта. Токен действует один час. Выпуск нового токена заменяет предыдущий.", "Claude Code and Codex can read this project's files. Tokens expire after one hour. Issuing a new token replaces the previous one.")}</p>
    <div className="flex flex-wrap gap-2">
      <button className={primaryButton} disabled={pending} onClick={() => change("issue")}>{t("Выдать токен", "Issue token")}</button>
      <button className={secondaryButton} disabled={pending} onClick={() => change("revoke")}>{t("Отозвать доступ", "Revoke access")}</button>
    </div>
    {token && <label className="mt-3 block">{t("Скопируйте в CONTENT_MILL_MCP_TOKEN", "Copy to CONTENT_MILL_MCP_TOKEN")}
      <input className={field} readOnly type="password" autoComplete="off" value={token} onFocus={e => e.target.select()} />
    </label>}
    <p role="status" className="mt-2">{notice}</p>
  </details>;
}
