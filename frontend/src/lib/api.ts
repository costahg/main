const API_URL = String(
  import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000"
).replace(/\/$/, "")

export type HealthResponse = {
  ok?: boolean
  message?: string
}

export type Project = {
  id: string
  name: string
  notes: string | null
  createdAt: string
}

export type ProjectsResponse = {
  ok: boolean
  projects: Project[]
}

export function getApiUrl(): string {
  return API_URL
}

async function getJson<TResponse>(path: string): Promise<TResponse> {
  const response = await fetch(`${API_URL}${path}`)

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }

  return response.json() as Promise<TResponse>
}

export function getHealth(): Promise<HealthResponse> {
  return getJson<HealthResponse>("/health")
}

export function getProjects(): Promise<ProjectsResponse> {
  return getJson<ProjectsResponse>("/projects")
}
