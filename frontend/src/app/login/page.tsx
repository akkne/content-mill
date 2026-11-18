import { eyebrow } from "@/app/ui-styles";
import { LoginForm } from "./login-form";

export default function LoginPage() {
  return (
    <main className="grid min-h-screen place-items-center p-6">
      <section
        aria-labelledby="login-title"
        className="w-full max-w-[440px] rounded-[22px] border border-line bg-surface p-[34px] shadow-panel"
      >
        <div className="mb-[30px] flex items-center gap-2.5 text-[28px] font-extrabold tracking-[-.05em]">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img alt="" height="42" src="/mill-logo.png" width="42" />
          <span>
            mill <small className="text-sm font-medium tracking-normal text-muted">studio</small>
          </span>
        </div>
        <span className={eyebrow}>Рабочее пространство</span>
        <h1 className="my-[9px] text-[28px] leading-[1.3]" id="login-title">
          Вход в Content Mill
        </h1>
        <p className="mb-[25px] text-muted">Войдите с учётной записью, выданной администратором проекта.</p>
        <LoginForm />
      </section>
    </main>
  );
}
