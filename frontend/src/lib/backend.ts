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
