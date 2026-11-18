import { content, eyebrow, pageLead, pageTitle, primaryButton, secondaryButton, sectionTitle, workPanel } from "@/app/ui-styles";
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
      <main className={content} id="main-content">
        <span className={eyebrow}>Content Mill</span>
        <h1 className={pageTitle}>Здравствуйте, {user.display_name}</h1>
        <p className={pageLead}>Создайте проект и сохраните контекст клиента для будущих материалов.</p>
        <section
          aria-labelledby="hero-title"
          className="grid min-h-[230px] grid-cols-[minmax(0,1fr)_230px] items-center gap-6 rounded-[20px] border border-line bg-[linear-gradient(120deg,var(--surface)_36%,var(--soft-blue))] px-[34px] py-[30px] shadow-panel max-[761px]:grid-cols-1 max-[561px]:p-6"
        >
          <div>
            <span className={eyebrow}>Первый этап</span>
            <h2
              className="mt-[9px] mb-3 max-w-[600px] text-[clamp(23px,3vw,32px)] leading-[1.3] tracking-[-.03em]"
              id="hero-title"
            >
              От контекста клиента к готовому материалу
            </h2>
            <p className="max-w-[550px] text-muted">
              Проекты и контекст уже доступны. Соберите сведения о клиенте, аудитории и продуктах.
            </p>
            <Link className={`${primaryButton} mt-[15px] inline-flex items-center`} href="/projects">
              Перейти к проектам
            </Link>
          </div>
          <div
            aria-hidden="true"
            className="m-auto grid size-[166px] -rotate-[16deg] place-items-center rounded-full bg-[radial-gradient(circle_at_32%_24%,#b8dcff,#397bfa_42%,#153772_76%)] text-[62px] font-extrabold text-white shadow-[inset_-12px_-16px_22px_#0c285a90,0_20px_44px_#397bfa24] max-[761px]:hidden"
          >
            m
          </div>
        </section>
        <h2 className={sectionTitle}>Состояние платформы</h2>
        <div className="grid grid-cols-2 gap-3.5 max-[561px]:grid-cols-1">
          <section className={workPanel}>
            <span
              className={`mb-3 inline-flex items-center gap-[7px] rounded-md px-2 py-1 text-[10px] font-bold before:size-1.5 before:rounded-full before:bg-current ${backendStatus === "online" ? "bg-success-bg text-success" : "bg-warning-bg text-warning"}`}
            >
              API {backendStatus === "online" ? "доступен" : "недоступен"}
            </span>
            <h3 className="mb-2 text-[15px]">Сервер приложения</h3>
            <p className="text-xs leading-[1.7] text-muted">
              {backendStatus === "online"
                ? "Проверка соединения прошла успешно. Проекты доступны через API."
                : "Не удалось связаться с сервером. Проверьте, запущен ли FastAPI и указан ли BACKEND_URL."}
            </p>
          </section>
          <section className={workPanel}>
            <h3 className="mb-2 text-[15px]">База знаний</h3>
            <p className="text-xs leading-[1.7] text-muted">
              Документы, изображения, аудио и видео хранятся в папках проекта.
            </p>
            <Link href="/knowledge" className={secondaryButton}>
              Открыть базу знаний
            </Link>
          </section>
        </div>
      </main>
    </AppShell>
  );
}
