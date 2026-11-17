export async function getBackendStatus(): Promise<"online" | "offline"> {
  try {
    const response = await fetch(
      `${process.env.BACKEND_URL ?? "http://localhost:8000"}/health`,
      { cache: "no-store" },
    );
    return response.ok ? "online" : "offline";
  } catch {
    return "offline";
  }
}

export type CurrentUser = {
  id: string;
  display_name: string;
  projects: { id: string; name: string; role: string }[];
};

export type TokenPair = {
  access_token: string;
  access_expires_at: string;
  refresh_token: string;
  refresh_expires_at: string;
};

export function backendUrl(path: string): string {
  return `${process.env.BACKEND_URL ?? "http://localhost:8000"}${path}`;
}

export async function fetchCurrentUser(accessToken: string): Promise<CurrentUser | null> {
  try {
    const response = await fetch(backendUrl("/api/v1/me"), {
      headers: { Authorization: `Bearer ${accessToken}` },
      cache: "no-store",
    });
    return response.ok ? (await response.json()) as CurrentUser : null;
  } catch {
    return null;
  }
}
