import { LoginForm } from "./login-form";

export default function LoginPage() {
  return (
    <main className="login-page">
      <section aria-labelledby="login-title" className="login-card">
        <div className="login-brand">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img alt="" height="42" src="/mill-logo.png" width="42" />
          <span>mill <small>studio</small></span>
        </div>
        <span className="eyebrow">Рабочее пространство</span>
        <h1 id="login-title">Вход в Content Mill</h1>
        <p>Войдите с учётной записью, выданной администратором проекта.</p>
        <LoginForm />
      </section>
    </main>
  );
}
