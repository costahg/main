import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import {
  ApiClientError,
  getAdminSession,
  loginAdmin,
  logoutAdmin,
} from "@/lib/api"

import App from "./App"

vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>()

  return {
    ...actual,
    getAdminSession: vi.fn(),
    loginAdmin: vi.fn(),
    logoutAdmin: vi.fn(),
  }
})

const mockedGetAdminSession = vi.mocked(getAdminSession)
const mockedLoginAdmin = vi.mocked(loginAdmin)
const mockedLogoutAdmin = vi.mocked(logoutAdmin)

describe("App main screen state", () => {
  beforeEach(() => {
    mockedGetAdminSession.mockReset()
    mockedLoginAdmin.mockReset()
    mockedLogoutAdmin.mockReset()
    mockedGetAdminSession.mockResolvedValue({ ok: true, authenticated: false })
    mockedLogoutAdmin.mockResolvedValue({ ok: true })
  })

  afterEach(() => {
    cleanup()
  })

  it("renders a circular top logo and switches from public form to admin login on click", async () => {
    const user = userEvent.setup()

    render(<App />)

    const header = screen.getByRole("banner")
    const logoButton = screen.getByRole("button", {
      name: "Abrir login administrativo",
    })

    expect(header).toContainElement(logoButton)
    expect(logoButton).toHaveClass("rounded-full")
    expect(
      screen.getByRole("heading", { name: "Registro de viagem" })
    ).toBeInTheDocument()

    await user.click(logoButton)

    expect(
      screen.getByRole("heading", { name: "Acesso administrativo" })
    ).toBeInTheDocument()
    expect(
      screen.queryByRole("heading", { name: "Registro de viagem" })
    ).not.toBeInTheDocument()
  })

  it("sends valid admin credentials and opens the viewer", async () => {
    const user = userEvent.setup()
    mockedLoginAdmin.mockResolvedValue({ ok: true })

    render(<App />)

    await user.click(
      screen.getByRole("button", { name: "Abrir login administrativo" })
    )
    await user.type(screen.getByLabelText("Usuário"), "admin")
    await user.type(screen.getByLabelText("Senha"), "senha-segura")
    await user.click(screen.getByRole("button", { name: "Entrar" }))

    expect(mockedLoginAdmin).toHaveBeenCalledWith({
      username: "admin",
      password: "senha-segura",
    })
    expect(
      await screen.findByRole("heading", { name: "Registros administrativos" })
    ).toBeInTheDocument()
  })

  it("shows a generic error when admin credentials are invalid", async () => {
    const user = userEvent.setup()
    mockedLoginAdmin.mockRejectedValue(
      new ApiClientError({
        status: 401,
        error: "invalid_credentials",
        message: "Credenciais inválidas.",
      })
    )

    render(<App />)

    await user.click(
      screen.getByRole("button", { name: "Abrir login administrativo" })
    )
    await user.type(screen.getByLabelText("Usuário"), "admin")
    await user.type(screen.getByLabelText("Senha"), "errada")
    await user.click(screen.getByRole("button", { name: "Entrar" }))

    expect(
      await screen.findByText("Não foi possível entrar com essas credenciais.")
    ).toBeInTheDocument()
    expect(screen.queryByText("Credenciais inválidas.")).not.toBeInTheDocument()
    expect(
      screen.queryByRole("heading", { name: "Registros administrativos" })
    ).not.toBeInTheDocument()
  })

  it("opens the viewer when the existing admin session is valid", async () => {
    mockedGetAdminSession.mockResolvedValue({ ok: true, authenticated: true })

    render(<App />)

    expect(
      await screen.findByRole("heading", { name: "Registros administrativos" })
    ).toBeInTheDocument()
  })

  it("calls logout and leaves the viewer", async () => {
    const user = userEvent.setup()
    mockedGetAdminSession.mockResolvedValue({ ok: true, authenticated: true })

    render(<App />)

    await screen.findByRole("heading", { name: "Registros administrativos" })
    await user.click(screen.getByRole("button", { name: "Sair" }))

    expect(mockedLogoutAdmin).toHaveBeenCalled()
    expect(
      await screen.findByRole("heading", { name: "Registro de viagem" })
    ).toBeInTheDocument()
    expect(
      screen.queryByRole("heading", { name: "Registros administrativos" })
    ).not.toBeInTheDocument()
  })
})
