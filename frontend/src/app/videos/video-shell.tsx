import { AppShell } from "@/app/app-shell";
import { content } from "@/app/ui-styles";
import { fetchCurrentUser } from "@/lib/backend";
import { accessCookie } from "@/lib/session";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

export async function VideoShell({ children }: { children: React.ReactNode }) {
  const token = (await cookies()).get(accessCookie)?.value;
  const user = token && (await fetchCurrentUser(token));
  if (!user) redirect("/login");
  return (
    <AppShell userName={user.display_name} section="Ролики">
      <main id="main-content" className={content}>
        {children}
      </main>
    </AppShell>
  );
}
