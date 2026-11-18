import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { getBackendStatus } from "@/lib/backend";
import { fetchCurrentUser } from "@/lib/backend";
import { accessCookie } from "@/lib/session";
import { AppShell } from "./app-shell";
import Link from "next/link";

export const dynamic = "force-dynamic";

export default async function Home() {
  const access = (await cookies()).get(accessCookie)?.value;
  if (!access) redirect("/login");
  const user = await fetchCurrentUser(access);
  if (!user) redirect("/login");
  const backendStatus = await getBackendStatus();

  return (
    <AppShell userName={user.display_name}>
      <main className="content" id="main-content">
        <span className="eyebrow">Content Mill</span>
        <h1 className="page-title">Здравствуйте, {user.display_name}</h1>
        <p className="page-lead">Создайте проект и сохраните контекст клиента для будущих материалов.</p>
        <section aria-labelledby="hero-title" className="hero-panel">
          <div>
            <span className="eyebrow">Первый этап</span>
            <h2 id="hero-title">От контекста клиента к готовому материалу</h2>
            <p>Проекты и контекст уже доступны. Соберите сведения о клиенте, аудитории и продуктах.</p>
            <Link className="primary-button" href="/projects" style={{ display: "inline-flex", alignItems: "center" }}>Перейти к проектам</Link>
          </div>
          <div aria-hidden="true" className="hero-art">m</div>
        </section>
        <h2 className="section-title">Состояние платформы</h2>
        <div className="status-grid">
          <section className="work-panel">
            <span className={`status-pill status-pill-${backendStatus}`}>API {backendStatus === "online" ? "доступен" : "недоступен"}</span>
            <h3>Сервер приложения</h3>
            <p>{backendStatus === "online" ? "Проверка соединения прошла успешно. Проекты доступны через API." : "Не удалось связаться с сервером. Проверьте, запущен ли FastAPI и указан ли BACKEND_URL."}</p>
          </section>
          <section className="work-panel">
            <h3>База знаний</h3>
            <p>Документы, изображения, аудио и видео хранятся в папках проекта.</p>
            <Link href="/knowledge" className="secondary-button">Открыть базу знаний</Link>
          </section>
        </div>
      </main>
    </AppShell>
  );
}
