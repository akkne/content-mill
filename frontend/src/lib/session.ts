import { cookies } from "next/headers";

import type { TokenPair } from "./backend";

export const accessCookie = "mill_access";
export const refreshCookie = "mill_refresh";

export function cookieOptions(expires: string) {
  return {
    httpOnly: true,
    secure: process.env.SESSION_COOKIE_SECURE !== "false" && process.env.NODE_ENV === "production",
    sameSite: "strict" as const,
    path: "/",
    expires: new Date(expires),
  };
}

export async function setSession(tokens: TokenPair) {
  const store = await cookies();
  store.set(accessCookie, tokens.access_token, cookieOptions(tokens.access_expires_at));
  store.set(refreshCookie, tokens.refresh_token, cookieOptions(tokens.refresh_expires_at));
}

export async function clearSession() {
  const store = await cookies();
  store.delete(accessCookie);
  store.delete(refreshCookie);
}
