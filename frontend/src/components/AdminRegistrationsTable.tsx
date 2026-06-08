import { useCallback, useEffect, useState } from "react"
import { Check, ClipboardCopy, LoaderCircle, Mail, Trash2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  deleteAdminTravelRegistration,
  listAdminTravelRegistrations,
  type AdminTravelRegistration,
} from "@/lib/api"
import { formatLemonTechTravelRegistration } from "@/lib/format"

type TableStatus = "loading" | "ready" | "error"

const COLUMNS: Array<{
  header: string
  render: (registration: AdminTravelRegistration) => string
}> = [
  { header: "Nome do Viajante", render: (registration) => registration.nomeViajante },
  { header: "Matrícula", render: (registration) => registration.matricula },
  {
    header: "Data de Solicitação",
    render: (registration) => formatVisualDate(registration.dataSolicitacao),
  },
  { header: "Solicitante", render: (registration) => registration.solicitanteEmail },
  { header: "Centro de Custo", render: (registration) => registration.centroCusto },
  { header: "DDI", render: (registration) => registration.dditel },
  { header: "DDD", render: (registration) => registration.dddtel },
  { header: "Telefone", render: (registration) => registration.tel },
  { header: "CPF", render: (registration) => registration.cpf },
  { header: "Email do Viajante", render: (registration) => registration.emailViajante },
  { header: "Cargo", render: (registration) => registration.cargo },
  { header: "RG", render: (registration) => registration.rg ?? "" },
  { header: "Passaporte", render: (registration) => registration.passaporte ?? "" },
  { header: "Departamento", render: (registration) => registration.departamento ?? "" },
  {
    header: "Data de Admissão",
    render: (registration) => formatVisualDate(registration.dataAdmissao),
  },
  {
    header: "Data de Nascimento",
    render: (registration) => formatVisualDate(registration.dataNascimento),
  },
]

export function AdminRegistrationsTable() {
  const [status, setStatus] = useState<TableStatus>("loading")
  const [registrations, setRegistrations] = useState<AdminTravelRegistration[]>([])
  const [copiedRegistrationId, setCopiedRegistrationId] = useState<string | null>(null)
  const [deletingRegistrationId, setDeletingRegistrationId] = useState<string | null>(
    null
  )
  const [actionError, setActionError] = useState<string | null>(null)

  useEffect(() => {
    let isActive = true

    async function loadRegistrations() {
      setStatus("loading")

      try {
        const response = await listAdminTravelRegistrations()

        if (isActive) {
          setRegistrations(response.registrations)
          setStatus("ready")
        }
      } catch {
        if (isActive) {
          setStatus("error")
        }
      }
    }

    void loadRegistrations()

    return () => {
      isActive = false
    }
  }, [])

  const handleCopy = useCallback(async (registration: AdminTravelRegistration) => {
    setActionError(null)

    try {
      await navigator.clipboard.writeText(formatLemonTechTravelRegistration(registration))
      setCopiedRegistrationId(registration.id)
    } catch {
      setActionError("Não foi possível copiar o registro.")
    }
  }, [])

  const handleDelete = useCallback(async (registrationId: string) => {
    setActionError(null)
    setDeletingRegistrationId(registrationId)

    try {
      await deleteAdminTravelRegistration(registrationId)
      setRegistrations((current) =>
        current.filter((registration) => registration.id !== registrationId)
      )
    } catch {
      setActionError("Não foi possível excluir o registro.")
    } finally {
      setDeletingRegistrationId(null)
    }
  }, [])

  if (status === "loading") {
    return (
      <div className="border-y py-5 text-sm text-muted-foreground" role="status">
        Carregando registros...
      </div>
    )
  }

  if (status === "error") {
    return (
      <div className="border-y py-5 text-sm text-destructive" role="alert">
        Não foi possível carregar os registros.
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {actionError ? (
        <p className="text-sm text-destructive" role="alert">
          {actionError}
        </p>
      ) : null}

      {registrations.length === 0 ? (
        <div className="border-y py-5 text-sm text-muted-foreground">
          Nenhum registro encontrado.
        </div>
      ) : (
        <div className="overflow-x-auto border-y">
          <table
            className="min-w-[1680px] text-left text-sm"
            aria-label="Registros de viagem"
          >
            <thead className="bg-muted/60 text-xs font-semibold uppercase text-muted-foreground">
              <tr>
                {COLUMNS.map((column) => (
                  <th key={column.header} scope="col" className="px-3 py-3">
                    {column.header}
                  </th>
                ))}
                <th scope="col" className="px-3 py-3">
                  Ações
                </th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {registrations.map((registration) => (
                <tr key={registration.id} className="align-top">
                  {COLUMNS.map((column) => (
                    <td key={column.header} className="px-3 py-3">
                      {column.render(registration)}
                    </td>
                  ))}
                  <td className="px-3 py-3">
                    <div className="flex min-w-72 flex-wrap gap-2">
                      <Button
                        type="button"
                        className="bg-blue-700 text-white hover:bg-blue-800"
                        onClick={() => void handleCopy(registration)}
                      >
                        {copiedRegistrationId === registration.id ? (
                          <Check className="size-4" aria-hidden="true" />
                        ) : (
                          <ClipboardCopy className="size-4" aria-hidden="true" />
                        )}
                        {copiedRegistrationId === registration.id ? "Copiado" : "Copiar"}
                      </Button>

                      <Button
                        type="button"
                        variant="outline"
                        disabled={deletingRegistrationId === registration.id}
                        onClick={() => void handleDelete(registration.id)}
                      >
                        {deletingRegistrationId === registration.id ? (
                          <LoaderCircle
                            className="size-4 animate-spin"
                            aria-hidden="true"
                          />
                        ) : (
                          <Trash2 className="size-4" aria-hidden="true" />
                        )}
                        Excluir
                      </Button>

                      <Button
                        type="button"
                        variant="outline"
                        disabled
                        title="Ainda não implementado"
                      >
                        <Mail className="size-4" aria-hidden="true" />
                        Enviar email
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function formatVisualDate(value: string): string {
  const isoDateMatch = /^(\d{4})-(\d{2})-(\d{2})/.exec(value)

  if (!isoDateMatch) {
    return value
  }

  const [, year, month, day] = isoDateMatch

  return `${day}/${month}/${year}`
}
