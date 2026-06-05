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
      <section className="mx-auto flex min-h-screen w-full max-w-7xl flex-col gap-8 px-5 py-6 sm:px-8 lg:px-10">
        <div className="overflow-hidden rounded-[2rem] border border-primary/20 bg-primary text-primary-foreground shadow-2xl shadow-primary/20">
          <div className="bg-[radial-gradient(circle_at_top_right,rgba(127,191,255,0.38),transparent_34%),linear-gradient(135deg,rgba(0,76,154,1),rgba(0,48,112,1))] px-6 py-10 sm:px-10 sm:py-14 lg:px-14">
            <div className="mx-auto flex max-w-5xl flex-col items-center gap-6 text-center">
              <div className="inline-flex w-fit items-center gap-2 rounded-full border border-white/25 bg-white/12 px-4 py-2 text-sm text-white shadow-sm backdrop-blur">
                <CheckCircle2 className="size-4 text-info" />
                Tigrify, fatia vertical de banco
              </div>

              <div className="space-y-4">
                <h1 className="max-w-4xl text-balance text-4xl font-semibold tracking-tight sm:text-5xl lg:text-6xl">
                  Frontend, backend e banco conectados
                </h1>

                <p className="mx-auto max-w-2xl text-base leading-7 text-white/82 sm:text-lg">
                  Cloudflare Pages chama o Cloud Run, o FastAPI consulta o
                  Supabase e o frontend mostra dados reais.
                </p>
              </div>

              <div className="flex flex-col gap-3 sm:flex-row">
                <Button
                  className="bg-surface text-primary hover:bg-surface/90"
                  onClick={testBackend}
                >
                  Testar backend
                </Button>

                <Button
                  className="border border-white/30 bg-white/10 text-white hover:bg-white/18"
                  onClick={testProjects}
                >
                  Carregar projetos
                </Button>
              </div>
            </div>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-4">
          {stackItems.map((item) => {
            const Icon = item.icon

            return (
              <Card
                key={item.title}
                className="border-primary/15 bg-card shadow-sm transition hover:-translate-y-0.5 hover:border-primary/35 hover:shadow-md"
              >
                <CardHeader>
                  <div className="mb-2 flex size-11 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-sm shadow-primary/25">
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

        <Card className="border-primary/15 bg-card">
          <CardHeader>
            <CardTitle>Configuração detectada</CardTitle>
            <CardDescription>
              O frontend usa VITE_API_URL como URL base da API.
            </CardDescription>
          </CardHeader>

          <CardContent>
            <p className="break-all rounded-xl border border-primary/10 bg-primary/5 p-4 text-sm text-primary">
              {apiUrl}
            </p>
          </CardContent>
        </Card>

        <Card className="border-primary/15 bg-card">
          <CardHeader>
            <CardTitle>Projetos vindos do Supabase</CardTitle>
            <CardDescription>
              Lista carregada pelo backend. O frontend não acessa o banco
              diretamente.
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-3">
            {projects.length === 0 ? (
              <p className="rounded-xl border border-primary/10 bg-primary/5 p-4 text-sm text-muted-foreground">
                Nenhum projeto carregado ainda.
              </p>
            ) : (
              projects.map((project) => (
                <article
                  key={project.id}
                  className="rounded-xl border border-primary/15 bg-surface p-4 shadow-sm"
                >
                  <h2 className="font-medium text-primary">{project.name}</h2>

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
    <Card className="border-primary/15 bg-card shadow-sm">
      <CardHeader className="border-b border-primary/10">
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>

      <CardContent className="pt-6">
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
  const baseClassName = "rounded-xl border p-4 text-sm"

  if (status === "success") {
    return `${baseClassName} border-success/25 bg-success/10 text-success`
  }

  if (status === "error") {
    return `${baseClassName} border-danger/25 bg-danger/10 text-danger`
  }

  if (status === "loading") {
    return `${baseClassName} border-info/35 bg-info/10 text-primary`
  }

  return `${baseClassName} border-primary/10 bg-primary/5 text-muted-foreground`
}

function getErrorMessage(error: unknown): string {
  return error instanceof Error
    ? `Erro: ${error.message}`
    : "Erro desconhecido."
}

export default App
