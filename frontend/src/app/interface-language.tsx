"use client";

import { createContext, useContext } from "react";
import { translator, type InterfaceLanguage } from "@/lib/interface-language";

const InterfaceLanguageContext = createContext<InterfaceLanguage>("ru");

export function InterfaceLanguageProvider({ language, children }: {
  language: InterfaceLanguage;
  children: React.ReactNode;
}) {
  return <InterfaceLanguageContext.Provider value={language}>{children}</InterfaceLanguageContext.Provider>;
}

export function useInterfaceLanguage() {
  return useContext(InterfaceLanguageContext);
}

export function useTranslator() {
  return translator(useInterfaceLanguage());
}
