import { NextRequest, NextResponse } from "next/server";

import { backendUrl, type TokenPair } from "@/lib/backend";
import { accessCookie, cookieOptions, refreshCookie } from "@/lib/session";

import { isInterfaceLanguage, languageCookie, languageCookieOptions } from "@/lib/interface-language";

export async function proxy(request: NextRequest) {
  // Preserve bookmarks to the original home-page language switch.
  const lang = request.nextUrl.searchParams.get("lang");
  if (request.method === "GET" && request.nextUrl.pathname === "/" && isInterfaceLanguage(lang)) {
    const url = request.nextUrl.clone();
    url.searchParams.delete("lang");
    const response = NextResponse.redirect(url);
    response.cookies.set(languageCookie, lang, languageCookieOptions);
    return response;
  }
  const access = request.cookies.get(accessCookie)?.value;
  if (access) {
    try {
      const check = await fetch(backendUrl("/api/v1/me"), {
        headers: { Authorization: `Bearer ${access}` },
        cache: "no-store",
      });
      if (check.ok) return NextResponse.next();
    } catch {
      return NextResponse.next();
    }
  }

  const refresh = request.cookies.get(refreshCookie)?.value;
  if (!refresh) return NextResponse.redirect(new URL("/login", request.url));
  try {
    const result = await fetch(backendUrl("/api/v1/auth/refresh"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refresh }),
      cache: "no-store",
    });
    if (result.ok) {
      const tokens = await result.json() as TokenPair;
      request.cookies.set(accessCookie, tokens.access_token);
      request.cookies.set(refreshCookie, tokens.refresh_token);
      const response = NextResponse.next({ request });
      response.cookies.set(accessCookie, tokens.access_token, cookieOptions(tokens.access_expires_at));
      response.cookies.set(refreshCookie, tokens.refresh_token, cookieOptions(tokens.refresh_expires_at));
      return response;
    }
  } catch {
    return NextResponse.next();
  }
  const response = NextResponse.redirect(new URL("/login", request.url));
  response.cookies.delete(accessCookie);
  response.cookies.delete(refreshCookie);
  return response;
}

export const config = { matcher: ["/", "/admin/:path*", "/projects/:path*", "/knowledge/:path*", "/contents/:path*", "/videos/:path*"] };
