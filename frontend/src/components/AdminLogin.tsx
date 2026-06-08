import { useState, type FormEvent } from "react"
import { LoaderCircle, LogIn } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { loginAdmin } from "@/lib/api"

type AdminLoginProps = {
  onAuthenticated: () => void
}

const GENERIC_LOGIN_ERROR = "Não foi possível entrar com essas credenciais."

export function AdminLogin({ onAuthenticated }: AdminLoginProps) {
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [hasError, setHasError] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    setIsSubmitting(true)
    setHasError(false)

    try {
      await loginAdmin({ username: username.trim(), password })
      setPassword("")
      onAuthenticated()
    } catch {
      setHasError(true)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form
      className="space-y-4"
      aria-label="Acesso administrativo"
      onSubmit={handleSubmit}
      noValidate
    >
      <div className="space-y-2">
        <Label htmlFor="adminUser">Usuário</Label>
        <Input
          id="adminUser"
          name="adminUser"
          value={username}
          autoComplete="username"
          aria-invalid={hasError ? "true" : undefined}
          onChange={(event) => {
            setUsername(event.target.value)
            setHasError(false)
          }}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="adminPassword">Senha</Label>
        <Input
          id="adminPassword"
          name="adminPassword"
          type="password"
          value={password}
          autoComplete="current-password"
          aria-invalid={hasError ? "true" : undefined}
          onChange={(event) => {
            setPassword(event.target.value)
            setHasError(false)
          }}
        />
      </div>

      {hasError ? (
        <p className="text-sm text-destructive" role="alert">
          {GENERIC_LOGIN_ERROR}
        </p>
      ) : null}

      <Button type="submit" disabled={isSubmitting} className="w-full sm:w-auto">
        {isSubmitting ? (
          <LoaderCircle className="size-4 animate-spin" aria-hidden="true" />
        ) : (
          <LogIn className="size-4" aria-hidden="true" />
        )}
        {isSubmitting ? "Entrando..." : "Entrar"}
      </Button>
    </form>
  )
}
