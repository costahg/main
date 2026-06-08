import { useMemo, useState, type FormEvent } from "react"
import { LoaderCircle, Send } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  ApiClientError,
  submitTravelRegistration,
  type ApiFieldErrors,
  type TravelRegistrationRequest,
} from "@/lib/api"

type FormStatus =
  | "idle"
  | "submitting"
  | "success"
  | "validation_error"
  | "unexpected_error"

type TravelRegistrationFormValues = {
  [FieldName in keyof TravelRegistrationRequest]-?: string
}

type FieldConfig = {
  name: keyof TravelRegistrationFormValues
  label: string
  type?: "date" | "email" | "tel" | "text"
  required?: boolean
  autoComplete?: string
  className?: string
}

const INITIAL_VALUES: TravelRegistrationFormValues = {
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
  rg: "",
  passaporte: "",
  departamento: "",
  dataAdmissao: "",
  dataNascimento: "",
}

const FIELD_CONFIGS: FieldConfig[] = [
  {
    name: "nomeViajante",
    label: "Nome do viajante",
    required: true,
    autoComplete: "name",
    className: "sm:col-span-2",
  },
  { name: "matricula", label: "Matrícula", required: true },
  {
    name: "solicitanteEmail",
    label: "Solicitante",
    type: "email",
    required: true,
    autoComplete: "email",
  },
  { name: "centroCusto", label: "Centro de custo", required: true },
  {
    name: "dditel",
    label: "DDI",
    type: "tel",
    required: true,
    autoComplete: "tel-country-code",
  },
  {
    name: "dddtel",
    label: "DDD",
    type: "tel",
    required: true,
    autoComplete: "tel-area-code",
  },
  {
    name: "tel",
    label: "Telefone",
    type: "tel",
    required: true,
    autoComplete: "tel-local",
  },
  { name: "cpf", label: "CPF", required: true },
  {
    name: "emailViajante",
    label: "E-mail do viajante",
    type: "email",
    required: true,
    autoComplete: "email",
  },
  { name: "cargo", label: "Cargo", required: true },
  { name: "rg", label: "RG" },
  { name: "passaporte", label: "Passaporte" },
  { name: "departamento", label: "Departamento" },
  { name: "dataAdmissao", label: "Data de admissão", type: "date", required: true },
  {
    name: "dataNascimento",
    label: "Data de nascimento",
    type: "date",
    required: true,
  },
]

const REQUIRED_FIELD_NAMES = FIELD_CONFIGS.filter((field) => field.required).map(
  (field) => field.name
)

type TravelRegistrationFormProps = {
  isLoading?: boolean
}

export function TravelRegistrationForm({
  isLoading = false,
}: TravelRegistrationFormProps) {
  const [values, setValues] = useState<TravelRegistrationFormValues>(INITIAL_VALUES)
  const [status, setStatus] = useState<FormStatus>("idle")
  const [fieldErrors, setFieldErrors] = useState<ApiFieldErrors>({})

  const requiredFieldNames = useMemo(() => new Set(REQUIRED_FIELD_NAMES), [])
  const isSubmitting = status === "submitting"

  if (isLoading) {
    return (
      <div className="text-sm text-muted-foreground" role="status">
        Carregando formulário...
      </div>
    )
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const nextFieldErrors = getRequiredFieldErrors(values, requiredFieldNames)
    if (Object.keys(nextFieldErrors).length > 0) {
      setFieldErrors(nextFieldErrors)
      setStatus("validation_error")
      return
    }

    setStatus("submitting")
    setFieldErrors({})

    try {
      await submitTravelRegistration(toTravelRegistrationRequest(values))
      setValues(INITIAL_VALUES)
      setStatus("success")
    } catch (error) {
      if (error instanceof ApiClientError && error.fields) {
        setFieldErrors(error.fields)
        setStatus("validation_error")
        return
      }

      setStatus("unexpected_error")
    }
  }

  return (
    <form
      className="grid w-full gap-5 sm:grid-cols-2"
      aria-label="Registro de viagem"
      onSubmit={handleSubmit}
      noValidate
    >
      {FIELD_CONFIGS.map((field) => {
        const error = fieldErrors[field.name]
        const fieldLabel = `${field.label}${field.required ? " *" : ""}`

        return (
          <div key={field.name} className={`space-y-2 ${field.className ?? ""}`}>
            <Label htmlFor={field.name}>{fieldLabel}</Label>
            <Input
              id={field.name}
              name={field.name}
              type={field.type ?? "text"}
              value={values[field.name]}
              required={field.required}
              autoComplete={field.autoComplete}
              aria-invalid={error ? "true" : undefined}
              aria-describedby={error ? `${field.name}-error` : undefined}
              onChange={(event) => {
                const value = event.target.value
                setValues((current) => ({ ...current, [field.name]: value }))
                setFieldErrors((current) => omitFieldError(current, field.name))
              }}
            />
            {error ? (
              <p id={`${field.name}-error`} className="text-sm text-destructive">
                {error}
              </p>
            ) : null}
          </div>
        )
      })}

      <div className="flex flex-col gap-3 pt-1 sm:col-span-2 sm:flex-row sm:items-center">
        <Button type="submit" disabled={isSubmitting} className="w-full sm:w-auto">
          {isSubmitting ? (
            <LoaderCircle className="size-4 animate-spin" aria-hidden="true" />
          ) : (
            <Send className="size-4" aria-hidden="true" />
          )}
          {isSubmitting ? "Enviando..." : "Enviar registro"}
        </Button>

        <FormMessage status={status} />
      </div>
    </form>
  )
}

function FormMessage({ status }: { status: FormStatus }) {
  if (status === "success") {
    return (
      <p className="text-sm font-medium text-emerald-700" role="status">
        Registro enviado com sucesso.
      </p>
    )
  }

  if (status === "validation_error") {
    return (
      <p className="text-sm text-muted-foreground" role="status">
        Corrija os campos destacados.
      </p>
    )
  }

  if (status === "unexpected_error") {
    return (
      <p className="text-sm text-destructive" role="alert">
        Não foi possível enviar o registro agora.
      </p>
    )
  }

  if (status === "submitting") {
    return (
      <p className="text-sm text-muted-foreground" role="status">
        Enviando registro...
      </p>
    )
  }

  return null
}

function getRequiredFieldErrors(
  values: TravelRegistrationFormValues,
  requiredFieldNames: Set<keyof TravelRegistrationFormValues>
): ApiFieldErrors {
  const errors: ApiFieldErrors = {}

  requiredFieldNames.forEach((fieldName) => {
    if (!values[fieldName].trim()) {
      errors[fieldName] = "Campo obrigatório"
    }
  })

  return errors
}

function toTravelRegistrationRequest(
  values: TravelRegistrationFormValues
): TravelRegistrationRequest {
  return {
    nomeViajante: values.nomeViajante.trim(),
    matricula: values.matricula.trim(),
    solicitanteEmail: values.solicitanteEmail.trim(),
    centroCusto: values.centroCusto.trim(),
    dditel: values.dditel.trim(),
    dddtel: values.dddtel.trim(),
    tel: values.tel.trim(),
    cpf: values.cpf.trim(),
    emailViajante: values.emailViajante.trim(),
    cargo: values.cargo.trim(),
    rg: trimOptional(values.rg),
    passaporte: trimOptional(values.passaporte),
    departamento: trimOptional(values.departamento),
    dataAdmissao: values.dataAdmissao,
    dataNascimento: values.dataNascimento,
  }
}

function trimOptional(value: string): string | null {
  const trimmedValue = value.trim()

  return trimmedValue.length > 0 ? trimmedValue : null
}

function omitFieldError(
  fieldErrors: ApiFieldErrors,
  fieldName: keyof TravelRegistrationFormValues
): ApiFieldErrors {
  if (!fieldErrors[fieldName]) {
    return fieldErrors
  }

  const remainingErrors = { ...fieldErrors }
  delete remainingErrors[fieldName]

  return remainingErrors
}
