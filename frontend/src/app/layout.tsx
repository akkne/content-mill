import type { Metadata } from "next";
import { cookies } from "next/headers";
import { languageCookie } from "@/lib/interface-language";
import { InterfaceLanguageProvider } from "./interface-language";
import "./globals.css";

export const metadata: Metadata = {
  title: "Content Mill",
  description: "Платформа для подготовки и анализа короткого контента",
};

export default async function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  const language = (await cookies()).get(languageCookie)?.value === "en" ? "en" : "ru";
  return (
    <html className="min-w-[320px]" lang={language}>
      {/* Browser extensions can add attributes to body before hydration. */}
      <body
        suppressHydrationWarning
        className="bg-canvas font-sans text-[13px] leading-[1.6] text-ink [&_button]:cursor-pointer [&_:is(button,a,input,textarea,select):focus-visible]:outline-2 [&_:is(button,a,input,textarea,select):focus-visible]:outline-offset-[3px] [&_:is(button,a,input,textarea,select):focus-visible]:outline-accent"
      >
        <InterfaceLanguageProvider language={language}>{children}</InterfaceLanguageProvider>
      </body>
    </html>
  );
}
