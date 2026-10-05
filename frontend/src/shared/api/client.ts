export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public fields: Record<string, string[]> = {},
  ) {
    super(message);
  }
}

let epoch = 0;
export function invalidateSessionRequests() {
  epoch++;
}

export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const started = epoch;
  const headers = new Headers(options.headers);
  if (options.body) headers.set("Content-Type", "application/json");
  if (options.method && !["GET", "HEAD"].includes(options.method)) {
    const csrf = await fetch("/api/v1/auth/csrf/", {
      credentials: "same-origin",
      signal: options.signal,
      cache: "no-store",
    });
    if (!csrf.ok)
      throw new ApiError(
        csrf.status,
        "csrf_failed",
        "No se pudo validar la sesión. Intenta otra vez.",
      );
    const { csrfToken } = await csrf.json();
    headers.set("X-CSRFToken", csrfToken);
  }
  if (started !== epoch)
    throw new DOMException("Session changed", "AbortError");
  const response = await fetch("/api/v1/" + path, {
    ...options,
    headers,
    credentials: "same-origin",
    cache: "no-store",
  });
  const data = await response.json();
  if (started !== epoch)
    throw new DOMException("Session changed", "AbortError");
  if (!response.ok)
    throw new ApiError(
      response.status,
      data.error?.code ?? "request_failed",
      data.error?.message ?? "No se pudo completar la solicitud.",
      data.error?.fields,
    );
  return data as T;
}
