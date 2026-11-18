import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { fetchCurrentUser } from "@/lib/backend";
import { accessCookie } from "@/lib/session";
import { AppShell } from "./app-shell";
import { OverviewMascot } from "./overview-mascot";
import { WorkspaceIcon } from "./workspace-icon";

export const dynamic = "force-dynamic";

const card = "rounded-[18px] border border-line bg-surface shadow-panel";
const heading = "flex items-center gap-2.5 text-base font-bold";
const tag =
  "absolute flex items-center gap-[7px] whitespace-nowrap rounded-lg border border-line bg-tag px-[11px] py-[9px] text-[10px] font-semibold text-muted shadow-panel backdrop-blur-md";

export default async function Home({
  searchParams,
}: {
  searchParams: Promise<{ lang?: string }>;
}) {
  const access = (await cookies()).get(accessCookie)?.value;
  const user = access && (await fetchCurrentUser(access));
  if (!user) redirect("/login");
  const english = (await searchParams).lang === "en";
  const t = (ru: string, en: string) => (english ? en : ru);
  const pending = t("Ещё не реализовано", "Not yet implemented");
  const status = (
    <small className="block text-[10px] font-medium">{pending}</small>
  );
  return (
    <AppShell userName={user.display_name} english={english}>
      <main
        id="main-content"
        className="mx-auto w-full max-w-[1600px] flex-1 px-8 py-[29px] motion-safe:animate-[overview-appear_.24s_ease-out] max-[950px]:px-6 max-sm:px-[17px] max-sm:py-[23px] min-[1500px]:px-[45px]"
      >
        <header className="mb-6 flex items-start gap-3.5">
          <WorkspaceIcon name="home" className="mt-1 size-[37px]" />
          <div>
            <h1 className="text-[28px] leading-tight font-bold tracking-tight max-sm:text-[25px]">
              {t("Главная страница", "Home")}
            </h1>
            <p className="mt-2 text-muted">
              {t(
                "Здесь собраны ролики, план публикаций и результаты работы.",
                "Your videos, publishing plan and results in one place.",
              )}
            </p>
          </div>
        </header>
        <section className="relative mb-7 flex min-h-[268px] items-center overflow-hidden rounded-[22px] border border-line bg-hero px-8 py-7 shadow-panel max-[1100px]:flex-col max-[1100px]:items-start max-sm:px-[22px]">
          <div className="relative z-1 min-[1101px]:max-w-[calc(100%-310px)]">
            <span className="flex items-center gap-2 text-[10px] font-extrabold tracking-widest text-accent uppercase">
              <WorkspaceIcon name="agent" className="size-5" />
              {t("От идеи до публикации", "From idea to publication")}
            </span>
            <h2 className="my-3 text-[34px] leading-tight font-bold tracking-tight max-sm:text-[29px] min-[1500px]:text-[39px]">
              {t("Планируйте контент", "Plan your content")}
              <br />
              <span className="text-action">
                {t("и создавайте ролики.", "and create videos.")}
              </span>
            </h2>
            <p className="max-w-[330px] text-xs leading-relaxed text-muted">
              {t(
                "Добавьте материалы, выберите формат и подготовьте новый ролик.",
                "Add materials, choose a format and prepare a new video.",
              )}
            </p>
            <div className="mt-5 flex flex-wrap items-center gap-4 text-xs">
              {[
                t("Создать ролик", "Create video"),
                t("Анализ ниши", "Niche analysis"),
                t("Спросить агента", "Ask the agent"),
              ].map((label, index) => (
                <button
                  type="button"
                  disabled
                  key={label}
                  className={`disabled:cursor-default font-bold ${index === 0 ? "rounded-[10px] bg-action px-4 py-2 text-white" : "text-left text-muted"}`}
                >
                  {index === 0 && <span aria-hidden="true">＋ </span>}
                  {label}
                  {status}
                </button>
              ))}
            </div>
          </div>
          <div
            aria-hidden="true"
            className="pointer-events-none absolute top-1/2 right-6 h-[250px] w-[300px] -translate-y-1/2 max-[1100px]:relative max-[1100px]:inset-auto max-[1100px]:mt-[22px] max-[1100px]:-mb-2 max-[1100px]:translate-y-0 max-[1100px]:self-center max-sm:h-[235px] max-sm:max-w-full"
          >
            <OverviewMascot />
            <span
              className={`${tag} top-[25px] -left-[7px] -rotate-[7deg] max-sm:left-0`}
            >
              <WorkspaceIcon name="agent" className="size-4" />
              {t("Идея", "Idea")}
            </span>
            <span
              className={`${tag} top-[126px] -right-[7px] rotate-6 max-sm:right-0`}
            >
              <svg
                aria-hidden="true"
                viewBox="0 0 24 24"
                className="size-4 fill-none stroke-current"
                strokeWidth="1.6"
              >
                <path d="M14 3H5v18h14V8Zm0 0v5h5M8 13h8m-8 4h6" />
              </svg>
              {t("Сценарий", "Script")}
            </span>
            <span className={`${tag} -bottom-1.5 left-[71px] -rotate-3`}>
              <WorkspaceIcon name="videos" className="size-5" />
              {t("Готовый ролик", "Finished video")}
            </span>
          </div>
        </section>
        <section>
          <h2 className={heading}>
            <WorkspaceIcon name="analytics" />
            {t("Результаты за 14 дней", "Results for the last 14 days")}
          </h2>
          <div className="mt-3.5 mb-7 grid grid-cols-4 gap-3 max-[950px]:grid-cols-2">
            {[
              [t("Просмотры", "Views"), "analytics"],
              [t("Переходы", "Clicks"), "channels"],
              [t("Заявки", "Leads"), "leads"],
              [t("Ролики", "Videos"), "videos"],
            ].map(([label, icon]) => (
              <article
                key={icon}
                className={`${card} px-5 py-[19px] max-sm:p-4`}
              >
                <h3 className="flex items-center justify-between gap-1 text-xs font-semibold text-muted">
                  {label}
                  <WorkspaceIcon name={icon} />
                </h3>
                <p className="my-1 text-[29px] font-bold" aria-hidden="true">
                  —
                </p>
                <p className="text-[11px] text-muted">
                  {t("Нет данных", "No data")}
                </p>
              </article>
            ))}
          </div>
        </section>
        <section>
          <div className="mb-3.5 flex items-center justify-between gap-3">
            <h2 className={heading}>
              <WorkspaceIcon name="videos" />
              {t("Последние ролики", "Latest videos")}
            </h2>
            <button
              disabled
              className="text-right text-xs font-bold text-muted disabled:cursor-default"
            >
              {t("Все ролики", "All videos")} →{status}
            </button>
          </div>
          <div
            className={`${card} grid min-h-36 place-content-center justify-items-center gap-2 text-muted`}
          >
            <WorkspaceIcon name="videos" className="size-10" />
            <p>{t("Роликов пока нет", "No videos yet")}</p>
          </div>
        </section>
        <div className="mt-7 grid grid-cols-3 gap-3 max-[950px]:grid-cols-1">
          {[
            [
              "niche",
              t("Анализ ниши", "Niche analysis"),
              t(
                "Примеры форматов и идеи для роликов вашего бренда",
                "Format examples and video ideas for your brand",
              ),
            ],
            [
              "plan",
              t("План и автопилот", "Plan and autopilot"),
              t(
                "Планирование роликов и публикаций",
                "Video and publication planning",
              ),
            ],
            [
              "studio",
              t("Instagram-студия", "Instagram studio"),
              t(
                "Карусели, сторис и контент на неделю",
                "Carousels, stories and weekly content",
              ),
            ],
          ].map(([icon, label, description]) => (
            <button
              key={icon}
              disabled
              className={`${card} flex items-start gap-3 p-4 text-left disabled:cursor-default`}
            >
              <WorkspaceIcon name={icon} className="size-8" />
              <span>
                <strong>{label}</strong>
                <span className="mt-1 mb-2 block text-xs text-muted">
                  {description}
                </span>
                {status}
              </span>
            </button>
          ))}
        </div>
      </main>
      <footer className="flex flex-wrap justify-between gap-2 border-t border-line px-8 py-4 text-[10px] text-faint">
        <span>mill / CONTENT STUDIO</span>
        <span>
          {t(
            "Подготовка, планирование и публикация контента.",
            "Content preparation, planning and publishing.",
          )}
        </span>
      </footer>
    </AppShell>
  );
}
