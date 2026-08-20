// Typed API client (issue #26). Requests go to "/api/..." — relative paths,
// proxied by Vite's dev server (see vite.config.ts) to the FastAPI backend,
// so calls are same-origin from the browser's point of view. No OpenAPI
// codegen; types are hand-written to match the backend's Pydantic schemas.

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });

  if (!response.ok) {
    throw new ApiError(response.status, `${init?.method ?? "GET"} ${path} failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}
