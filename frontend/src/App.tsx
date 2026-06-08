import { useCallback, useEffect, useState } from "react"
import { LockKeyhole, LogOut, Plane } from "lucide-react"

import { AdminLogin } from "@/components/AdminLogin"
import { AdminRegistrationsTable } from "@/components/AdminRegistrationsTable"
import { TravelRegistrationForm } from "@/components/TravelRegistrationForm"
import { Button } from "@/components/ui/button"
import { getAdminSession, logoutAdmin } from "@/lib/api"

type AppScreen = "public_form" | "admin_login" | "admin_viewer"

function App() {
  const [screen, setScreen] = useState<AppScreen>("public_form")

  const openAdminViewer = useCallback(() => {
    setScreen("admin_viewer")
  }, [])

  const openAdminLogin = useCallback(async () => {
    try {
      const session = await getAdminSession()

      if (session.authenticated) {
        setScreen("admin_viewer")
        return
      }
    } catch {
      // Session checks only restore UI state; backend routes remain authoritative.
    }

    setScreen("admin_login")
  }, [])

  const handleLogout = useCallback(async () => {
    try {
      await logoutAdmin()
    } finally {
      setScreen("public_form")
    }
  }, [])

  useEffect(() => {
    let isActive = true

    async function restoreAdminSession() {
      try {
        const session = await getAdminSession()

        if (isActive && session.authenticated) {
          setScreen("admin_viewer")
        }
      } catch {
        if (isActive) {
          setScreen("public_form")
        }
      }
    }

    void restoreAdminSession()

    return () => {
      isActive = false
    }
  }, [])

  return (
    <main className="min-h-screen bg-background text-foreground">
      <div className="mx-auto flex min-h-screen w-full max-w-4xl flex-col px-5 py-6 sm:px-8">
        <AppHeader onOpenAdminLogin={openAdminLogin} />

        <section className="flex flex-1 items-center py-8">
          {screen === "public_form" ? <PublicFormShell /> : null}
          {screen === "admin_login" ? (
            <AdminLoginShell onAuthenticated={openAdminViewer} />
          ) : null}
          {screen === "admin_viewer" ? (
            <AdminViewerShell onLogout={handleLogout} />
          ) : null}
        </section>
      </div>
    </main>
  )
}

type AppHeaderProps = {
  onOpenAdminLogin: () => void
}

function AppHeader({ onOpenAdminLogin }: AppHeaderProps) {
  return (
    <header className="flex items-center justify-between gap-4">
      <button
        type="button"
        aria-label="Abrir login administrativo"
        className="flex size-12 items-center justify-center rounded-full border bg-foreground text-background shadow-sm transition-colors hover:bg-foreground/85 focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none"
        onClick={onOpenAdminLogin}
      >
        <span aria-hidden="true" className="text-base font-semibold">
          T
        </span>
      </button>

      <p className="text-sm font-medium text-muted-foreground">Tigrify</p>
    </header>
  )
}

function PublicFormShell() {
  return (
    <div className="w-full">
      <div className="mb-8 space-y-2">
        <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
          <Plane className="size-4" />
          Cadastro operacional
        </div>

        <h1 className="text-3xl font-semibold tracking-normal sm:text-4xl">
          Registro de viagem
        </h1>

        <p className="max-w-2xl text-base leading-7 text-muted-foreground">
          Informe os dados principais para iniciar uma solicitação.
        </p>
      </div>

      <TravelRegistrationForm />
    </div>
  )
}

type AdminLoginShellProps = {
  onAuthenticated: () => void
}

function AdminLoginShell({ onAuthenticated }: AdminLoginShellProps) {
  return (
    <div className="w-full max-w-sm">
      <div className="mb-6 space-y-2">
        <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
          <LockKeyhole className="size-4" />
          Área restrita
        </div>

        <h1 className="text-3xl font-semibold tracking-normal">
          Acesso administrativo
        </h1>
      </div>

      <AdminLogin onAuthenticated={onAuthenticated} />
    </div>
  )
}

type AdminViewerShellProps = {
  onLogout: () => void
}

function AdminViewerShell({ onLogout }: AdminViewerShellProps) {
  return (
    <div className="w-full space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
            <LockKeyhole className="size-4" />
            Sessão administrativa
          </div>

          <h1 className="text-3xl font-semibold tracking-normal">
            Registros administrativos
          </h1>
        </div>

        <Button type="button" variant="outline" onClick={onLogout}>
          <LogOut className="size-4" aria-hidden="true" />
          Sair
        </Button>
      </div>

      <AdminRegistrationsTable />
    </div>
  )
}

export default App
