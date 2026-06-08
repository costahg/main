import { cleanup, render, screen, waitFor, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import {
  ApiClientError,
  deleteAdminTravelRegistration,
  listAdminTravelRegistrations,
  type AdminTravelRegistration,
} from "@/lib/api"

import { AdminRegistrationsTable } from "./AdminRegistrationsTable"

vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>()

  return {
    ...actual,
    listAdminTravelRegistrations: vi.fn(),
    deleteAdminTravelRegistration: vi.fn(),
  }
})

const mockedListAdminTravelRegistrations = vi.mocked(listAdminTravelRegistrations)
const mockedDeleteAdminTravelRegistration = vi.mocked(deleteAdminTravelRegistration)
const writeText = vi.fn<Clipboard["writeText"]>()

describe("AdminRegistrationsTable", () => {
  beforeEach(() => {
    mockedListAdminTravelRegistrations.mockReset()
    mockedDeleteAdminTravelRegistration.mockReset()
    writeText.mockReset()
    Object.defineProperty(globalThis.navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    })
    Object.defineProperty(window.navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    })
  })

  afterEach(() => {
    cleanup()
  })

  it("shows a loading state while registrations are being fetched", () => {
    mockedListAdminTravelRegistrations.mockReturnValue(new Promise(() => undefined))

    render(<AdminRegistrationsTable />)

    expect(screen.getByRole("status")).toHaveTextContent("Carregando registros...")
  })

  it("shows a controlled error when the admin list fails", async () => {
    mockedListAdminTravelRegistrations.mockRejectedValue(
      new ApiClientError({
        status: 500,
        error: "internal_error",
        message: "stack trace",
      })
    )

    render(<AdminRegistrationsTable />)

    expect(
      await screen.findByText("Não foi possível carregar os registros.")
    ).toBeInTheDocument()
    expect(screen.queryByText("stack trace")).not.toBeInTheDocument()
  })

  it("shows an empty table state when there are no registrations", async () => {
    mockedListAdminTravelRegistrations.mockResolvedValue({
      ok: true,
      registrations: [],
    })

    render(<AdminRegistrationsTable />)

    expect(await screen.findByText("Nenhum registro encontrado.")).toBeInTheDocument()
  })

  it("renders the required columns and row actions", async () => {
    mockedListAdminTravelRegistrations.mockResolvedValue({
      ok: true,
      registrations: [registration],
    })

    render(<AdminRegistrationsTable />)

    const table = await screen.findByRole("table", {
      name: "Registros de viagem",
    })
    const headers = within(table).getAllByRole("columnheader")

    expect(headers.map((header) => header.textContent)).toEqual([
      "Nome do Viajante",
      "Matrícula",
      "Data de Solicitação",
      "Solicitante",
      "Centro de Custo",
      "DDI",
      "DDD",
      "Telefone",
      "CPF",
      "Email do Viajante",
      "Cargo",
      "RG",
      "Passaporte",
      "Departamento",
      "Data de Admissão",
      "Data de Nascimento",
      "Ações",
    ])
    expect(within(table).getByText("Maria Silva")).toBeInTheDocument()
    expect(within(table).getByRole("button", { name: "Copiar" })).toHaveClass(
      "bg-blue-700"
    )
    expect(within(table).getByRole("button", { name: "Excluir" })).toBeEnabled()
    expect(within(table).getByRole("button", { name: "Enviar email" })).toBeDisabled()
    expect(within(table).getByRole("button", { name: "Enviar email" })).toHaveAttribute(
      "title",
      "Ainda não implementado"
    )
  })

  it("copies LemonTech text and shows visual feedback", async () => {
    const user = userEvent.setup()
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    })
    mockedListAdminTravelRegistrations.mockResolvedValue({
      ok: true,
      registrations: [registration],
    })
    writeText.mockResolvedValue(undefined)

    render(<AdminRegistrationsTable />)

    await user.click(await screen.findByRole("button", { name: "Copiar" }))

    await waitFor(() => {
      expect(writeText).toHaveBeenCalledWith(
        [
          "Nome: Maria Silva",
          "Centro de Custo: T123456",
          "Matrícula: 98765",
          "DDI: 55",
          "DDD: 11",
          "Telefone: 999999999",
          "CPF: 52998224725",
          "RG: 12345678",
          "Email: maria@empresa.com",
          "Cargo: Analista",
          "Passaporte: AB123456",
          "Departamento: Facilities",
          "Data de Admissão: 01/02/2024",
          "Data de Nascimento: 10/03/1990",
        ].join("\n")
      )
    })
    expect(await screen.findByRole("button", { name: "Copiado" })).toBeInTheDocument()
  })

  it("deletes a registration and removes its row", async () => {
    const user = userEvent.setup()
    mockedListAdminTravelRegistrations.mockResolvedValue({
      ok: true,
      registrations: [registration],
    })
    mockedDeleteAdminTravelRegistration.mockResolvedValue({ ok: true })

    render(<AdminRegistrationsTable />)

    await screen.findByText("Maria Silva")
    await user.click(screen.getByRole("button", { name: "Excluir" }))

    expect(mockedDeleteAdminTravelRegistration).toHaveBeenCalledWith("reg-1")
    await waitFor(() => {
      expect(screen.queryByText("Maria Silva")).not.toBeInTheDocument()
    })
    expect(screen.getByText("Nenhum registro encontrado.")).toBeInTheDocument()
  })
})

const registration: AdminTravelRegistration = {
  id: "reg-1",
  dataSolicitacao: "2026-06-07T12:00:00Z",
  nomeViajante: "Maria Silva",
  matricula: "98765",
  solicitanteEmail: "solicitante@empresa.com",
  centroCusto: "T123456",
  dditel: "55",
  dddtel: "11",
  tel: "999999999",
  cpf: "52998224725",
  emailViajante: "maria@empresa.com",
  cargo: "Analista",
  rg: "12345678",
  passaporte: "AB123456",
  departamento: "Facilities",
  dataAdmissao: "2024-02-01",
  dataNascimento: "1990-03-10",
}
