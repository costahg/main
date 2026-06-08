import { describe, expect, it } from "vitest"

import type { AdminTravelRegistration } from "./api"
import { formatLemonTechTravelRegistration } from "./format"

describe("formatLemonTechTravelRegistration", () => {
  it("formats an admin travel registration as the contracted LemonTech text block", () => {
    const registration: AdminTravelRegistration = {
      id: "3c3e31d6-1533-4c03-b6ed-fdb752215cc2",
      dataSolicitacao: "2026-06-08T12:30:00Z",
      nomeViajante: "Maria Silva",
      matricula: "98765",
      solicitanteEmail: "solicitante@empresa.com",
      centroCusto: "T123456",
      dditel: "55",
      dddtel: "11",
      tel: "999999999",
      cpf: "12345678901",
      emailViajante: "maria@empresa.com",
      cargo: "Analista",
      rg: "12345678",
      passaporte: "AB123456",
      departamento: "Facilities",
      dataAdmissao: "2024-02-01",
      dataNascimento: "1990-03-10",
    }

    expect(formatLemonTechTravelRegistration(registration)).toBe(
      [
        "Nome: Maria Silva",
        "Centro de Custo: T123456",
        "Matrícula: 98765",
        "DDI: 55",
        "DDD: 11",
        "Telefone: 999999999",
        "CPF: 12345678901",
        "RG: 12345678",
        "Email: maria@empresa.com",
        "Cargo: Analista",
        "Passaporte: AB123456",
        "Departamento: Facilities",
        "Data de Admissão: 01/02/2024",
        "Data de Nascimento: 10/03/1990",
      ].join("\n"),
    )
  })
})
