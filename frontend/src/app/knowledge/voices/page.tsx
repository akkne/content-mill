import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { AppShell } from "@/app/app-shell";
import { backLink, content } from "@/app/ui-styles";
import { fetchCurrentUser } from "@/lib/backend";
import { accessCookie } from "@/lib/session";
import { loadProjects } from "@/lib/projects";
import { listSaved } from "./actions";
import { VoiceLibrary } from "./voice-library";

export default async function VoicesPage({
  searchParams,
}: {
  searchParams: Promise<{ create?: string }>;
}) {
  const token = (await cookies()).get(accessCookie)?.value;
  const user = token && (await fetchCurrentUser(token));
  if (!user) redirect("/login");
  const [result, projects, params] = await Promise.all([
    listSaved(),
    loadProjects(),
    searchParams,
  ]);
  return (
    <AppShell userName={user.display_name} section="База знаний">
      <main className={content} id="main-content">
        <Link className={backLink} href="/knowledge">
          ← База знаний
        </Link>
        <h1 className="mb-6 text-4xl font-semibold tracking-tight sm:text-5xl">
          Библиотека голосов
        </h1>
        {result.data ? (
          <VoiceLibrary
            initial={result.data}
            projects={projects}
            creating={params.create === "1"}
          />
        ) : (
          <p role="alert">{result.error}</p>
        )}
      </main>
    </AppShell>
  );
}
