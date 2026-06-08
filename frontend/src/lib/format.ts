import type { AdminTravelRegistration } from "./api"

export function formatLemonTechTravelRegistration(
  registration: AdminTravelRegistration,
): string {
  return [
    ["Nome", registration.nomeViajante],
    ["Centro de Custo", registration.centroCusto],
    ["Matrícula", registration.matricula],
    ["DDI", registration.dditel],
    ["DDD", registration.dddtel],
    ["Telefone", registration.tel],
    ["CPF", registration.cpf],
    ["RG", registration.rg],
    ["Email", registration.emailViajante],
    ["Cargo", registration.cargo],
    ["Passaporte", registration.passaporte],
    ["Departamento", registration.departamento],
    ["Data de Admissão", formatVisualDate(registration.dataAdmissao)],
    ["Data de Nascimento", formatVisualDate(registration.dataNascimento)],
  ]
    .map(([label, value]) => `${label}: ${value ?? ""}`)
    .join("\n")
}

function formatVisualDate(value: string): string {
  const isoDateMatch = /^(\d{4})-(\d{2})-(\d{2})/.exec(value)

  if (!isoDateMatch) {
    return value
  }

  const [, year, month, day] = isoDateMatch

  return `${day}/${month}/${year}`
}
