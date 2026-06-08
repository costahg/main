import { afterEach, describe, expect, it, vi } from "vitest"
import type { AdminTravelRegistration, TravelRegistrationRequest } from "./api"

type ApiModule = typeof import("./api")

function jsonResponse(
  status: number,
  body: unknown,
): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: vi.fn().mockResolvedValue(body),
  } as unknown as Response
}

async function loadApi(apiUrl = "https://api.example.com/"): Promise<ApiModule> {
  vi.resetModules()
  vi.stubEnv("VITE_API_URL", apiUrl)

  return import("./api")
}

describe("api client", () => {
  afterEach(() => {
    vi.unstubAllEnvs()
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  it("preserves VITE_API_URL as base URL without trailing slash", async () => {
    const api = await loadApi("https://api.example.com/")

    expect(api.getApiUrl()).toBe("https://api.example.com")
  })

  it("submits public travel registration without admin credentials", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(200, { ok: true, id: "registration-id" }))
    vi.stubGlobal("fetch", fetchMock)
    const api = await loadApi()

    const request: TravelRegistrationRequest = {
      nomeViajante: "Maria de Souza",
      matricula: "98765",
      solicitanteEmail: "solicitante@empresa.com",
      centroCusto: "T123456",
      dditel: "55",
      dddtel: "11",
      tel: "999999999",
      cpf: "52998224725",
      emailViajante: "maria.souza@empresa.com",
      cargo: "Analista Senior",
      rg: "12345678",
      passaporte: "AB123456",
      departamento: "Operacoes Comerciais",
      dataAdmissao: "2024-02-01",
      dataNascimento: "1990-03-10",
    }

    await expect(api.submitTravelRegistration(request)).resolves.toEqual({
      ok: true,
      id: "registration-id",
    })
    expect(fetchMock).toHaveBeenCalledWith(
      "https://api.example.com/travel-registrations",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(request),
      },
    )
  })

  it("converts backend validation errors into field errors", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse(422, {
          ok: false,
          error: "validation_error",
          fields: { cpf: "CPF invalido" },
        }),
      ),
    )
    const api = await loadApi()

    await expect(
      api.submitTravelRegistration({
        nomeViajante: "",
        matricula: "",
        solicitanteEmail: "",
        centroCusto: "",
        dditel: "55",
        dddtel: "",
        tel: "",
        cpf: "",
        emailViajante: "",
        cargo: "",
        dataAdmissao: "",
        dataNascimento: "",
      }),
    ).rejects.toMatchObject({
      error: "validation_error",
      fields: { cpf: "CPF invalido" },
      status: 422,
    })
  })

  it("uses included credentials for all admin calls", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(200, { ok: true }))
      .mockResolvedValueOnce(jsonResponse(200, { ok: true, authenticated: true }))
      .mockResolvedValueOnce(jsonResponse(200, { ok: true }))
      .mockResolvedValueOnce(jsonResponse(200, { ok: true, registrations: [] }))
      .mockResolvedValueOnce(jsonResponse(200, { ok: true }))
    vi.stubGlobal("fetch", fetchMock)
    const api = await loadApi()

    await api.loginAdmin({ username: "admin", password: "password" })
    await api.getAdminSession()
    await api.logoutAdmin()
    await api.listAdminTravelRegistrations()
    await api.deleteAdminTravelRegistration("registration/id")

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      "https://api.example.com/admin/login",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: "admin", password: "password" }),
        credentials: "include",
      },
    )
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      "https://api.example.com/admin/session",
      { credentials: "include" },
    )
    expect(fetchMock).toHaveBeenNthCalledWith(
      3,
      "https://api.example.com/admin/logout",
      { method: "POST", credentials: "include" },
    )
    expect(fetchMock).toHaveBeenNthCalledWith(
      4,
      "https://api.example.com/admin/travel-registrations",
      { credentials: "include" },
    )
    expect(fetchMock).toHaveBeenNthCalledWith(
      5,
      "https://api.example.com/admin/travel-registrations/registration%2Fid",
      { method: "DELETE", credentials: "include" },
    )
  })

  it("lists typed admin travel registrations", async () => {
    const registrations: AdminTravelRegistration[] = [
      {
        id: "registration-id",
        dataSolicitacao: "2026-06-07T12:00:00+00:00",
        nomeViajante: "Maria de Souza",
        matricula: "98765",
        solicitanteEmail: "solicitante@empresa.com",
        centroCusto: "T123456",
        dditel: "55",
        dddtel: "11",
        tel: "999999999",
        cpf: "52998224725",
        emailViajante: "maria.souza@empresa.com",
        cargo: "Analista Senior",
        rg: null,
        passaporte: "AB123456",
        departamento: null,
        dataAdmissao: "2024-02-01",
        dataNascimento: "1990-03-10",
      },
    ]
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse(200, { ok: true, registrations })),
    )
    const api = await loadApi()

    await expect(api.listAdminTravelRegistrations()).resolves.toEqual({
      ok: true,
      registrations,
    })
  })

  it("returns a generic client error for unexpected failures", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(500, {})))
    const api = await loadApi()

    await expect(api.listAdminTravelRegistrations()).rejects.toMatchObject({
      error: "internal_error",
      message: "Ocorreu um erro inesperado.",
      status: 500,
    })
  })
})
