import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Content Mill",
  description: "Платформа для подготовки и анализа короткого контента",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html className="min-w-[320px]" lang="ru">
      {/* Browser extensions can add attributes to body before hydration. */}
      <body
        suppressHydrationWarning
        className="bg-canvas font-sans text-[13px] leading-[1.6] text-ink [&_button]:cursor-pointer [&_:is(button,a,input,textarea,select):focus-visible]:outline-2 [&_:is(button,a,input,textarea,select):focus-visible]:outline-offset-[3px] [&_:is(button,a,input,textarea,select):focus-visible]:outline-accent"
      >
        {children}
      </body>
    </html>
  );
}
