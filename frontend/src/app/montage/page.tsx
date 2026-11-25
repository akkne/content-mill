import { AppShell } from "@/app/app-shell";
import { content } from "@/app/ui-styles";
import { fetchCurrentUser } from "@/lib/backend";
import { loadProjects } from "@/lib/projects";
import { motionLibrary } from "@/lib/motion";
import { accessCookie } from "@/lib/session";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { Catalog } from "./catalog";

export default async function Montage({
  searchParams,
}: {
  searchParams: Promise<{ project?: string }>;
}) {
  const token = (await cookies()).get(accessCookie)?.value;
  const user = token && (await fetchCurrentUser(token));
  if (!user) redirect("/login");
  const projects = await loadProjects();
  const selected = (await searchParams).project;
  const project =
    projects.find((p) => p.id === selected)?.id ?? projects[0]?.id ?? "";
  const library = await motionLibrary(project);
  return (
    <AppShell
      userName={user.display_name}
      section="Монтаж"
      isAdmin={user.is_admin}
    >
      <main id="main-content" className={content}>
        <Catalog
          key={project}
          {...library}
          project={project}
          projects={projects}
          origin={process.env.OPENMOTION_PUBLIC_URL ?? "http://127.0.0.1:4173"}
        />
      </main>
    </AppShell>
  );
}
