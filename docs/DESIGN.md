# DESIGN.md — Техническая спецификация токенов и компонентов

Этот документ содержит готовые CSS-переменные, правила отступов и классы компонентов для реализации светлой дизайн-системы в однофайловом прототипе.

## 1. CSS Design Tokens (`:root`)

```css
:root {
  /* Backgrounds */
  --bg-canvas: #F8F9FB;
  --bg-surface: #FFFFFF;
  --bg-subtle: #F1F4F9;
  --bg-hover: #E2E8F0;

  /* Borders */
  --border-light: #E2E8F0;
  --border-medium: #CBD5E1;

  /* Text */
  --text-primary: #0F172A;
  --text-secondary: #475569;
  --text-muted: #94A3B8;
  --text-on-accent: #FFFFFF;

  /* Brand & Accents */
  --accent-primary: #4F46E5;
  --accent-primary-hover: #4338CA;
  --accent-primary-soft: #EEF2FF;

  --accent-creative: #EA580C;
  --accent-creative-soft: #FFF7ED;

  /* Semantics */
  --status-success-text: #059669;
  --status-success-bg: #ECFDF5;
  --status-warning-text: #D97706;
  --status-warning-bg: #FFFBEB;
  --status-info-text: #2563EB;
  --status-info-bg: #EFF6FF;

  /* Shadows */
  --shadow-xs: 0 1px 2px rgba(15, 23, 42, 0.04);
  --shadow-sm: 0 2px 8px -2px rgba(15, 23, 42, 0.06), 0 1px 3px rgba(15, 23, 42, 0.04);
  --shadow-md: 0 10px 25px -5px rgba(15, 23, 42, 0.08), 0 4px 10px -2px rgba(15, 23, 42, 0.03);
  --shadow-accent: 0 4px 14px rgba(79, 70, 229, 0.25);

  /* Radii */
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-full: 9999px;

  /* Layout */
  --sidebar-width: 256px;
  --topbar-height: 60px;
}
```

## 2. Спецификация компонентов

### Карточка (`Card`)
* **Фон:** `var(--bg-surface)`
* **Граница:** `1px solid var(--border-light)`
* **Скругление:** `var(--radius-lg)` (`16px`)
* **Тень:** `var(--shadow-sm)`
* **Внутренний отступ:** `20px` (стандарт), `24px` (крупные виджеты).

### Кнопки (`Buttons`)
* **`.btn-primary`:** `background: var(--accent-primary)`, `color: #FFF`, `border-radius: var(--radius-md)`, `padding: 10px 18px`, `font-weight: 600`, `box-shadow: var(--shadow-accent)`.
* **`.btn-creative`:** `background: var(--accent-creative)`, `color: #FFF` (используется для кнопок «Повторить формулу» и «Запустить генерацию»).
* **`.btn-secondary`:** `background: var(--bg-surface)`, `border: 1px solid var(--border-light)`, `color: var(--text-primary)`.
* **`.btn-ghost`:** `background: transparent`, `color: var(--text-secondary)`, hover: `background: var(--bg-subtle)`.

### Бейджи и теги (`Badges`)
* **Множитель виральности (`.badge-viral`):** `background: var(--accent-creative-soft)`, `color: var(--accent-creative)`, `border: 1px solid #FED7AA`, `font-weight: 700`, `font-size: 12px`, `padding: 2px 8px`, `border-radius: var(--radius-full)`.
* **Тег скилла AI (`.skill-tag`):** `font-family: 'JetBrains Mono'`, `font-size: 12px`, `background: var(--accent-primary-soft)`, `color: var(--accent-primary)`, `padding: 2px 8px`, `border-radius: 6px`.

### Визуализация воронки (Funnel Component)
* Горизонтальный flex-контейнер из 3–4 шагов, разделённых шевронами (`→`) с коэффициентом конверсии (`CTR 2.4%`, `CR 3.1%`).
* Внутри каждого шага: прогресс-бар высотой `6px` с заливкой `var(--accent-primary)` на фоне `var(--bg-subtle)`.

### Анимации и микровзаимодействия (для интерактивного MVP)
* Плавный переход между экранами (`opacity 0 -> 1`, `transform: translateY(4px) -> 0`, `duration: 180ms`).
* Пульсирующий индикатор (`@keyframes pulse`) у активного AI-агента в списке парсинга ниши.
* Имитация потоковой генерации (поочерёдное загорание галочек в чек-листе и плавный рост процентов от `0%` до `100%` за 3–4 секунды).