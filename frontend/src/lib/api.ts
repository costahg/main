const API_URL = String(
  import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000"
).replace(/\/+$/, "")

const GENERIC_ERROR_MESSAGE = "Ocorreu um erro inesperado."

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

export type TravelRegistrationRequest = {
  nomeViajante: string
  matricula: string
  solicitanteEmail: string
  centroCusto: string
  dditel: string
  dddtel: string
  tel: string
  cpf: string
  emailViajante: string
  cargo: string
  rg?: string | null
  passaporte?: string | null
  departamento?: string | null
  dataAdmissao: string
  dataNascimento: string
}

export type PublicTravelRegistrationResponse = {
  ok: true
  id: string
}

export type AdminLoginRequest = {
  username: string
  password: string
}

export type AdminLoginResponse = {
  ok: true
}

export type AdminSessionResponse = {
  ok: true
  authenticated: boolean
}

export type AdminLogoutResponse = {
  ok: true
}

export type AdminTravelRegistration = {
  id: string
  dataSolicitacao: string
  nomeViajante: string
  matricula: string
  solicitanteEmail: string
  centroCusto: string
  dditel: string
  dddtel: string
  tel: string
  cpf: string
  emailViajante: string
  cargo: string
  rg: string | null
  passaporte: string | null
  departamento: string | null
  dataAdmissao: string
  dataNascimento: string
}

export type AdminTravelRegistrationsResponse = {
  ok: true
  registrations: AdminTravelRegistration[]
}

export type AdminDeleteTravelRegistrationResponse = {
  ok: true
}

export type ApiFieldErrors = Record<string, string>

export type ApiErrorCode =
  | "validation_error"
  | "invalid_credentials"
  | "rate_limit_exceeded"
  | "unauthorized"
  | "not_found"
  | "internal_error"

export class ApiClientError extends Error {
  readonly status: number
  readonly error: ApiErrorCode
  readonly fields?: ApiFieldErrors

  constructor({
    status,
    error,
    message,
    fields,
  }: {
    status: number
    error: ApiErrorCode
    message: string
    fields?: ApiFieldErrors
  }) {
    super(message)
    this.name = "ApiClientError"
    this.status = status
    this.error = error
    this.fields = fields
  }
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

export function submitTravelRegistration(
  request: TravelRegistrationRequest,
): Promise<PublicTravelRegistrationResponse> {
  return requestJson<PublicTravelRegistrationResponse>("/travel-registrations", {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify(request),
  })
}

export function loginAdmin(request: AdminLoginRequest): Promise<AdminLoginResponse> {
  return requestJson<AdminLoginResponse>("/admin/login", {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify(request),
    credentials: "include",
  })
}

export function getAdminSession(): Promise<AdminSessionResponse> {
  return requestJson<AdminSessionResponse>("/admin/session", {
    credentials: "include",
  })
}

export function logoutAdmin(): Promise<AdminLogoutResponse> {
  return requestJson<AdminLogoutResponse>("/admin/logout", {
    method: "POST",
    credentials: "include",
  })
}

export function listAdminTravelRegistrations(): Promise<AdminTravelRegistrationsResponse> {
  return requestJson<AdminTravelRegistrationsResponse>("/admin/travel-registrations", {
    credentials: "include",
  })
}

export function deleteAdminTravelRegistration(
  registrationId: string,
): Promise<AdminDeleteTravelRegistrationResponse> {
  const encodedRegistrationId = encodeURIComponent(registrationId)

  return requestJson<AdminDeleteTravelRegistrationResponse>(
    `/admin/travel-registrations/${encodedRegistrationId}`,
    {
      method: "DELETE",
      credentials: "include",
    },
  )
}

async function requestJson<TResponse>(
  path: string,
  init?: RequestInit,
): Promise<TResponse> {
  try {
    const response = await fetch(`${API_URL}${path}`, init)
    const body = await readJsonBody(response)

    if (!response.ok) {
      throw toApiClientError(response.status, body)
    }

    return body as TResponse
  } catch (error) {
    if (error instanceof ApiClientError) {
      throw error
    }

    throw new ApiClientError({
      status: 0,
      error: "internal_error",
      message: GENERIC_ERROR_MESSAGE,
    })
  }
}

function jsonHeaders(): HeadersInit {
  return { "Content-Type": "application/json" }
}

async function readJsonBody(response: Response): Promise<unknown> {
  try {
    return await response.json()
  } catch {
    return null
  }
}

function toApiClientError(status: number, body: unknown): ApiClientError {
  if (isValidationErrorBody(body)) {
    return new ApiClientError({
      status,
      error: "validation_error",
      message: "Corrija os campos destacados.",
      fields: body.fields,
    })
  }

  if (status >= 500) {
    return new ApiClientError({
      status,
      error: "internal_error",
      message: GENERIC_ERROR_MESSAGE,
    })
  }

  return new ApiClientError({
    status,
    error: getApiErrorCode(body),
    message: getApiErrorMessage(body),
  })
}

function isValidationErrorBody(
  body: unknown,
): body is { error: "validation_error"; fields: ApiFieldErrors } {
  return (
    isRecord(body) &&
    body.error === "validation_error" &&
    isFieldErrors(body.fields)
  )
}

function isFieldErrors(value: unknown): value is ApiFieldErrors {
  return (
    isRecord(value) &&
    Object.values(value).every((fieldError) => typeof fieldError === "string")
  )
}

function getApiErrorCode(body: unknown): ApiErrorCode {
  if (isRecord(body) && typeof body.error === "string" && isApiErrorCode(body.error)) {
    return body.error
  }

  return "internal_error"
}

function getApiErrorMessage(body: unknown): string {
  if (isRecord(body) && typeof body.message === "string") {
    return body.message
  }

  return GENERIC_ERROR_MESSAGE
}

function isApiErrorCode(value: string): value is ApiErrorCode {
  return [
    "validation_error",
    "invalid_credentials",
    "rate_limit_exceeded",
    "unauthorized",
    "not_found",
    "internal_error",
  ].includes(value)
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null
}
