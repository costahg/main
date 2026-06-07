import { useMemo, useState } from "react"
import {
  CheckCircle2,
  Cloud,
  Code2,
  Database,
  Loader2,
  Server,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  getApiUrl,
  getHealth,
  getProjects,
  type Project,
} from "@/lib/api"

type RequestStatus = "idle" | "loading" | "success" | "error"

const stackItems = [
  {
    icon: Code2,
    title: "Frontend",
    description: "React estático com Vite no Cloudflare Pages.",
  },
  {
    icon: Server,
    title: "Backend",
    description: "FastAPI separado rodando no Cloud Run.",
  },
  {
    icon: Database,
    title: "Banco",
    description: "Supabase Postgres acessado somente pelo backend.",
  },
  {
    icon: Cloud,
    title: "Deploy",
    description: "Fluxo provado entre domínio, API e banco.",
  },
]

function App() {
  const [healthStatus, setHealthStatus] = useState<RequestStatus>("idle")
  const [databaseStatus, setDatabaseStatus] = useState<RequestStatus>("idle")
  const [healthMessage, setHealthMessage] = useState("Ainda não testado.")
  const [databaseMessage, setDatabaseMessage] = useState("Ainda não testado.")
  const [projects, setProjects] = useState<Project[]>([])

  const apiUrl = useMemo(() => getApiUrl(), [])

  async function testBackend() {
    try {
      setHealthStatus("loading")
      setHealthMessage("Chamando /health...")

      const data = await getHealth()

      setHealthStatus(data.ok ? "success" : "error")
      setHealthMessage(data.message ?? "Backend respondeu.")
    } catch (error) {
      setHealthStatus("error")
      setHealthMessage(getErrorMessage(error))
    }
  }

  async function testProjects() {
    try {
      setDatabaseStatus("loading")
      setDatabaseMessage("Chamando /projects...")
      setProjects([])

      const data = await getProjects()

      setProjects(data.projects)
      setDatabaseStatus(data.ok ? "success" : "error")
      setDatabaseMessage(
        data.projects.length > 0
          ? `${data.projects.length} projeto(s) carregado(s) do Supabase.`
          : "A API respondeu, mas ainda não há projetos."
      )
    } catch (error) {
      setDatabaseStatus("error")
      setDatabaseMessage(getErrorMessage(error))
    }
  }

  return (
    <main className="min-h-screen bg-background text-foreground">
      <section className="mx-auto flex min-h-screen w-full max-w-6xl flex-col justify-center gap-8 px-6 py-10">
        <header className="space-y-4 text-center">
          <div className="mx-auto inline-flex w-fit items-center gap-2 rounded-full border bg-card px-4 py-2 text-sm text-muted-foreground shadow-sm">
            <CheckCircle2 className="size-4" />
            Tigrify, fatia vertical de banco
          </div>

          <div className="space-y-3">
            <h1 className="text-4xl font-semibold tracking-tight sm:text-6xl">
              Frontend, backend e banco conectados
            </h1>

            <p className="mx-auto max-w-2xl text-base leading-7 text-muted-foreground sm:text-lg">
              Esta tela valida o caminho completo: Cloudflare Pages chama o
              Cloud Run, o FastAPI consulta o Supabase e o frontend mostra os
              dados reais.
            </p>
          </div>
        </header>

        <div className="grid gap-4 md:grid-cols-4">
          {stackItems.map((item) => {
            const Icon = item.icon

            return (
              <Card key={item.title}>
                <CardHeader>
                  <div className="mb-2 flex size-10 items-center justify-center rounded-lg border bg-muted">
                    <Icon className="size-5" />
                  </div>

                  <CardTitle>{item.title}</CardTitle>
                  <CardDescription>{item.description}</CardDescription>
                </CardHeader>
              </Card>
            )
          })}
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <StatusCard
            title="Teste do backend"
            description="Chama /health para confirmar que o FastAPI respondeu."
            status={healthStatus}
            message={healthMessage}
            buttonLabel="Testar backend"
            onClick={testBackend}
          />

          <StatusCard
            title="Teste do banco"
            description="Chama /projects para carregar dados reais do Supabase."
            status={databaseStatus}
            message={databaseMessage}
            buttonLabel="Carregar projetos"
            onClick={testProjects}
          />
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Configuração detectada</CardTitle>
            <CardDescription>
              O frontend usa VITE_API_URL como URL base da API.
            </CardDescription>
          </CardHeader>

          <CardContent>
            <p className="break-all rounded-lg border bg-muted/50 p-4 text-sm">
              {apiUrl}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Projetos vindos do Supabase</CardTitle>
            <CardDescription>
              Lista carregada pelo backend. O frontend não acessa o banco
              diretamente.
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-3">
            {projects.length === 0 ? (
              <p className="rounded-lg border bg-muted/50 p-4 text-sm text-muted-foreground">
                Nenhum projeto carregado ainda.
              </p>
            ) : (
              projects.map((project) => (
                <article
                  key={project.id}
                  className="rounded-lg border bg-muted/50 p-4"
                >
                  <h2 className="font-medium">{project.name}</h2>

                  <p className="mt-2 text-sm leading-6 text-muted-foreground">
                    {project.notes ?? "Sem observações."}
                  </p>

                  <p className="mt-3 break-all text-xs text-muted-foreground">
                    ID: {project.id}
                  </p>
                </article>
              ))
            )}
          </CardContent>
        </Card>
      </section>
    </main>
  )
}

type StatusCardProps = {
  title: string
  description: string
  status: RequestStatus
  message: string
  buttonLabel: string
  onClick: () => Promise<void>
}

function StatusCard({
  title,
  description,
  status,
  message,
  buttonLabel,
  onClick,
}: StatusCardProps) {
  const isLoading = status === "loading"

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>

      <CardContent>
        <p className={getStatusClassName(status)}>{message}</p>
      </CardContent>

      <CardFooter>
        <Button disabled={isLoading} onClick={onClick}>
          {isLoading ? (
            <>
              <Loader2 className="mr-2 size-4 animate-spin" />
              Testando...
            </>
          ) : (
            buttonLabel
          )}
        </Button>
      </CardFooter>
    </Card>
  )
}

function getStatusClassName(status: RequestStatus): string {
  const baseClassName = "rounded-lg border bg-muted/50 p-4 text-sm"

  if (status === "success") {
    return `${baseClassName} text-green-600`
  }

  if (status === "error") {
    return `${baseClassName} text-red-500`
  }

  return `${baseClassName} text-muted-foreground`
}

function getErrorMessage(error: unknown): string {
  return error instanceof Error
    ? `Erro: ${error.message}`
    : "Erro desconhecido."
}

export default App
