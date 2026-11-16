import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Content Mill",
  description: "Платформа для подготовки и анализа короткого контента",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ru">
      <body>{children}</body>
    </html>
  );
}
