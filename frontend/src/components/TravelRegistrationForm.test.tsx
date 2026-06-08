import { cleanup, render, screen, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { ApiClientError, submitTravelRegistration } from "@/lib/api"

import { TravelRegistrationForm } from "./TravelRegistrationForm"

vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>()

  return {
    ...actual,
    submitTravelRegistration: vi.fn(),
  }
})

const mockedSubmitTravelRegistration = vi.mocked(submitTravelRegistration)

describe("TravelRegistrationForm", () => {
  beforeEach(() => {
    mockedSubmitTravelRegistration.mockReset()
  })

  afterEach(() => {
    cleanup()
  })

  it("starts with DDI 55", () => {
    render(<TravelRegistrationForm />)

    expect(screen.getByLabelText("DDI *")).toHaveValue("55")
  })

  it("submits a valid payload and displays success", async () => {
    const user = userEvent.setup()
    mockedSubmitTravelRegistration.mockResolvedValue({ ok: true, id: "reg-1" })

    render(<TravelRegistrationForm />)

    await fillValidForm(user)
    await user.click(screen.getByRole("button", { name: "Enviar registro" }))

    expect(mockedSubmitTravelRegistration).toHaveBeenCalledWith({
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
    })
    expect(
      await screen.findByText("Registro enviado com sucesso.")
    ).toBeInTheDocument()
  })

  it("maps server validation errors to the related field", async () => {
    const user = userEvent.setup()
    mockedSubmitTravelRegistration.mockRejectedValue(
      new ApiClientError({
        status: 422,
        error: "validation_error",
        message: "Corrija os campos destacados.",
        fields: { cpf: "CPF inválido" },
      })
    )

    render(<TravelRegistrationForm />)

    await fillValidForm(user)
    await user.click(screen.getByRole("button", { name: "Enviar registro" }))

    const cpfField = screen.getByLabelText("CPF *")
    const cpfGroup = cpfField.closest("div")

    expect(await screen.findByText("CPF inválido")).toBeInTheDocument()
    expect(cpfField).toHaveAttribute("aria-invalid", "true")
    expect(cpfGroup).not.toBeNull()
    expect(within(cpfGroup as HTMLElement).getByText("CPF inválido")).toBeInTheDocument()
  })

  it("shows a generic message for unexpected errors", async () => {
    const user = userEvent.setup()
    mockedSubmitTravelRegistration.mockRejectedValue(new Error("HTTP 500 stack"))

    render(<TravelRegistrationForm />)

    await fillValidForm(user)
    await user.click(screen.getByRole("button", { name: "Enviar registro" }))

    expect(
      await screen.findByText("Não foi possível enviar o registro agora.")
    ).toBeInTheDocument()
    expect(screen.queryByText(/HTTP 500 stack/i)).not.toBeInTheDocument()
  })
})

async function fillValidForm(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByLabelText("Nome do viajante *"), "Maria Silva")
  await user.type(screen.getByLabelText("Matrícula *"), "98765")
  await user.type(screen.getByLabelText("Solicitante *"), "solicitante@empresa.com")
  await user.type(screen.getByLabelText("Centro de custo *"), "T123456")
  await user.type(screen.getByLabelText("DDD *"), "11")
  await user.type(screen.getByLabelText("Telefone *"), "999999999")
  await user.type(screen.getByLabelText("CPF *"), "52998224725")
  await user.type(screen.getByLabelText("E-mail do viajante *"), "maria@empresa.com")
  await user.type(screen.getByLabelText("Cargo *"), "Analista")
  await user.type(screen.getByLabelText("RG"), "12345678")
  await user.type(screen.getByLabelText("Passaporte"), "AB123456")
  await user.type(screen.getByLabelText("Departamento"), "Facilities")
  await user.type(screen.getByLabelText("Data de admissão *"), "2024-02-01")
  await user.type(screen.getByLabelText("Data de nascimento *"), "1990-03-10")
}
