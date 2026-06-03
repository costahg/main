import { useMemo, useState } from "react"
import {
  CheckCircle2,
  Cloud,
  Code2,
  Database,
  FolderOpen,
  Globe2,
  Loader2,
  Server,
  Smartphone,
  XCircle,
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
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"

const API_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000"

const stackItems = [
  {
    icon: Code2,
    title: "Frontend",
    description: "React + Vite + TypeScript + Tailwind + shadcn/ui",
  },
  {
    icon: Server,
    title: "Backend",
    description: "FastAPI separado, pronto para Cloud Run",
  },
  {
    icon: Database,
    title: "Banco",
    description: "Supabase Postgres para dados relacionais",
  },
  {
    icon: FolderOpen,
    title: "Storage",
    description: "Google Drive acessado pelo backend",
  },
  {
    icon: Cloud,
    title: "Deploy",
    description: "Cloudflare Pages servindo arquivos estáticos",
  },
]

function App() {
  const [projectName, setProjectName] = useState("Meu MVP")
  const [notes, setNotes] = useState(
    "Teste visual do frontend rodando no Termux Android."
  )
  const [checked, setChecked] = useState(false)
  const [apiStatus, setApiStatus] = useState<string>("Ainda não testado")
  const [apiOk, setApiOk] = useState<boolean | null>(null)

  const previewMessage = useMemo(() => {
    return {
      name: projectName.trim() || "Projeto sem nome",
      notes: notes.trim() || "Sem observações por enquanto.",
    }
  }, [projectName, notes])

  async function testarBackend() {
    try {
      setApiStatus("Chamando backend...")

      const response = await fetch(`${API_URL}/health`)

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data = await response.json()

      setApiOk(Boolean((data as any).ok))
      setApiStatus((data as any).message ?? "Backend respondeu.")
    } catch (error) {
      setApiOk(false)
      setApiStatus(
        error instanceof Error
          ? `Erro ao chamar backend: ${error.message}`
          : "Erro desconhecido ao chamar backend."
      )
    }
  }

  function resetTest() {
    setProjectName("Meu MVP")
    setNotes("Teste visual do frontend rodando no Termux Android.")
    setChecked(false)
    setApiStatus("Ainda não testado")
    setApiOk(null)
  }

  return (
    <main className="min-h-screen bg-background text-foreground">
      <section className="mx-auto flex min-h-screen w-full max-w-6xl flex-col justify-center gap-8 px-6 py-10">
        <div className="flex flex-col gap-4 text-center sm:items-center">
          <div className="mx-auto inline-flex w-fit items-center gap-2 rounded-full border bg-card px-4 py-2 text-sm text-muted-foreground shadow-sm">
            <Smartphone className="size-4" />
            Rodando no Termux Android
          </div>

          <div className="space-y-4">
            <h1 className="text-4xl font-semibold tracking-tight sm:text-6xl">
              Frontend pronto para teste
            </h1>

            <p className="mx-auto max-w-2xl text-base leading-7 text-muted-foreground sm:text-lg">
              Esta tela valida React, estado com hooks, Tailwind, shadcn/ui,
              ícones, alias de importação, variável de ambiente e build estático
              para Cloudflare Pages.
            </p>
          </div>

          <div className="flex flex-wrap justify-center gap-2 text-sm text-muted-foreground">
            <span className="rounded-full border bg-muted/50 px-3 py-1">
              Vite
            </span>
            <span className="rounded-full border bg-muted/50 px-3 py-1">
              TypeScript
            </span>
            <span className="rounded-full border bg-muted/50 px-3 py-1">
              Tailwind
            </span>
            <span className="rounded-full border bg-muted/50 px-3 py-1">
              shadcn/ui
            </span>
            <span className="rounded-full border bg-muted/50 px-3 py-1">
              Cloudflare Pages
            </span>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-5">
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

        <div className="grid gap-6 lg:grid-cols-[1fr_0.85fr]">
          <Card>
            <CardHeader>
              <CardTitle>Formulário de teste</CardTitle>
              <CardDescription>
                Se os inputs, labels e botões aparecem bonitos, o shadcn está
                funcionando. Se o texto muda ao digitar, o estado do React está
                funcionando.
              </CardDescription>
            </CardHeader>

            <CardContent className="space-y-5">
              <div className="space-y-2">
                <Label htmlFor="project-name">Nome do projeto</Label>
                <Input
                  id="project-name"
                  value={projectName}
                  onChange={(event) => setProjectName(event.target.value)}
                  placeholder="Ex: Sistema de documentos"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="project-notes">Observações</Label>
                <Textarea
                  id="project-notes"
                  value={notes}
                  onChange={(event) => setNotes(event.target.value)}
                  placeholder="Digite uma observação rápida..."
                />
              </div>
            </CardContent>

            <CardFooter className="flex flex-col items-stretch gap-3 sm:flex-row sm:items-center sm:justify-between">
              <Button onClick={() => setChecked(true)}>
                Testar interação
              </Button>

              <Button variant="outline" onClick={resetTest}>
                Resetar
              </Button>
            </CardFooter>
          </Card>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Status do frontend</CardTitle>
                <CardDescription>
                  Aqui você confirma renderização, estado e classes.
                </CardDescription>
              </CardHeader>

              <CardContent className="space-y-4">
                <div className="rounded-lg border bg-muted/50 p-4">
                  <p className="text-sm text-muted-foreground">Projeto</p>
                  <p className="mt-1 font-medium">{previewMessage.name}</p>
                </div>

                <div className="rounded-lg border bg-muted/50 p-4">
                  <p className="text-sm text-muted-foreground">Notas</p>
                  <p className="mt-1 text-sm leading-6">
                    {previewMessage.notes}
                  </p>
                </div>

                <div className="flex items-center gap-2 rounded-lg border p-4">
                  <CheckCircle2
                    className={
                      checked
                        ? "size-5 text-green-600"
                        : "size-5 text-muted-foreground"
                    }
                  />

                  <p className="text-sm">
                    {checked
                      ? "Interação funcionando. Pode testar preview ou deploy."
                      : "Clique no botão para testar o estado do React."}
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Teste de API</CardTitle>
                <CardDescription>
                  Esse teste tenta chamar <code>/health</code> no FastAPI quando
                  você configurar a variável VITE_API_URL.
                </CardDescription>
              </CardHeader>

              <CardContent className="space-y-4">
                <div className="rounded-lg border bg-muted/50 p-4">
                  <p className="text-sm text-muted-foreground">
                    Variável detectada
                  </p>
                  <p className="mt-1 break-all text-sm font-medium">
                    {API_URL || "VITE_API_URL ainda não configurada"}
                  </p>
                </div>

                <div className="rounded-lg border bg-muted/50 p-4">
                  <p className={apiOk === false ? "text-red-500" : "text-green-500"}>
                    {apiStatus}
                  </p>
                </div>
              </CardContent>

              <CardFooter>
                <Button onClick={testarBackend}>
                  Testar backend
                </Button>
              </CardFooter>
            </Card>
          </div>
        </div>
      </section>
    </main>
  )
}

export default App
