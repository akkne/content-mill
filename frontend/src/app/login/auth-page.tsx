import { getTranslator } from "@/lib/server-language";
import Link from "next/link";
import { eyebrow } from "@/app/ui-styles";
import { LoginForm } from "./login-form";

export async function AuthPage({ register = false }: { register?: boolean }) {
  const t = await getTranslator();
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
        <span className={eyebrow}>{t("Рабочее пространство", "Workspace")}</span>
        <h1 className="my-[9px] text-[28px] leading-[1.3]" id="login-title">
          {register ? t("Регистрация в Content Mill", "Register for Content Mill") : t("Вход в Content Mill", "Sign in to Content Mill")}
        </h1>
        <LoginForm register={register} />
        <Link className="mt-5 inline-block underline underline-offset-4" href={register ? "/login" : "/register"}>
          {register ? t("Уже есть аккаунт? Войти", "Already have an account? Sign in") : t("Создать аккаунт", "Create account")}
        </Link>
      </section>
    </main>
  );
}
