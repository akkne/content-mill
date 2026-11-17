import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { getBackendStatus } from "@/lib/backend";
import { fetchCurrentUser } from "@/lib/backend";
import { accessCookie } from "@/lib/session";
import { AppShell } from "./app-shell";

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
        <p className="page-lead">Здесь появятся проекты, база знаний и инструменты создания контента. Сейчас собираем основу первого этапа.</p>
        <section aria-labelledby="hero-title" className="hero-panel">
          <div>
            <span className="eyebrow">Первый этап</span>
            <h2 id="hero-title">От контекста клиента к готовому материалу</h2>
            <p>Начинаем с общего интерфейса. Затем подключим вход и работу с данными проекта через API.</p>
          </div>
          <div aria-hidden="true" className="hero-art">m</div>
        </section>
        <h2 className="section-title">Состояние платформы</h2>
        <div className="status-grid">
          <section className="work-panel">
            <span className={`status-pill status-pill-${backendStatus}`}>API {backendStatus === "online" ? "доступен" : "недоступен"}</span>
            <h3>Сервер приложения</h3>
            <p>{backendStatus === "online" ? "Проверка соединения прошла успешно. Продуктовые запросы будут подключаться по мере реализации." : "Не удалось связаться с сервером. Проверьте, запущен ли FastAPI и указан ли BACKEND_URL."}</p>
          </section>
          <section className="work-panel">
            <span className="status-pill status-pill-offline">В разработке</span>
            <h3>Пользовательские сценарии</h3>
            <p>Вход подключён. Проекты, документы и создание контента появятся в следующих фичах.</p>
          </section>
        </div>
        <h2 className="section-title">Следующие шаги</h2>
        <ol className="next-steps">
          <li>Добавить проекты и контекст клиента на реальном API.</li>
          <li>Создать базу знаний с документами и медиа.</li>
          <li>Подключить создание контента.</li>
        </ol>
      </main>
    </AppShell>
  );
}
