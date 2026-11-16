import { getBackendStatus } from "@/lib/backend";

export const dynamic = "force-dynamic";

export default async function Home() {
  const backendStatus = await getBackendStatus();

  return (
    <main className="mx-auto flex min-h-screen max-w-4xl flex-col justify-center px-6 py-16">
      <div className="rounded-2xl border border-border-light bg-surface p-8 shadow-sm sm:p-12">
        <span className="text-sm font-semibold uppercase tracking-widest text-accent">
          Content Mill
        </span>
        <h1 className="mt-5 text-4xl font-semibold tracking-tight sm:text-5xl">
          Платформа готовится к запуску
        </h1>
        <p className="mt-5 max-w-2xl text-lg leading-8 text-text-secondary">
          Каркас интерфейса и API уже работает. Продуктовые сценарии будут
          появляться здесь по этапам реализации.
        </p>
        <div className="mt-8 inline-flex items-center gap-3 rounded-xl bg-subtle px-4 py-3 text-sm text-text-secondary">
          <span
            aria-hidden="true"
            className={`h-2.5 w-2.5 rounded-full ${backendStatus === "online" ? "bg-success" : "bg-warning"}`}
          />
          API: {backendStatus === "online" ? "доступен" : "недоступен"}
        </div>
      </div>
    </main>
  );
}
