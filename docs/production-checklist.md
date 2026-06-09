# Checklist de produção do MVP de registros de viagem

## Backend Cloud Run

- Definir `DATABASE_URL` apontando para o Supabase Postgres correto.
- Definir `ADMIN_USERNAME`.
- Definir `ADMIN_PASSWORD_HASH` no formato PBKDF2 gerado pelo script do backend.
- Definir `ENCRYPTION_KEY` como chave Fernet válida, gerada fora do repositório.
- Definir `SESSION_SECRET` com valor forte e exclusivo do ambiente.
- Confirmar `ADMIN_SESSION_TTL_SECONDS` com TTL curto.
- Confirmar `RATE_LIMIT_WINDOW_SECONDS` com janela coerente para envio público e login admin.
- Confirmar `ALLOWED_ORIGINS` sem wildcard e sem barra final.
- Em produção, permitir somente `https://tigrify.site` e `https://www.tigrify.site`.

## Frontend Cloudflare Pages

- Definir `VITE_API_URL` como URL base pública do backend, sem rota fixa no final.
- Confirmar que `VITE_API_URL` não termina com barra.
- Não adicionar segredo, token, senha, hash, chave de criptografia ou chave de sessão em variável `VITE_`.

## Validação pós-deploy

- Validar `/health`.
- Validar `/db-health`.
- Enviar um registro público de teste.
- Fazer login admin.
- Consultar `/admin/session`.
- Listar registros em `/admin/travel-registrations`.
- Excluir o registro de teste pelo endpoint admin.
- Confirmar no frontend admin que a listagem, cópia LemonTech, exclusão e botão `Enviar email` desabilitado funcionam.

## Fora do MVP

- Não habilitar envio real de e-mail nesta versão.
- Não adicionar OAuth, Google APIs, uploads ou dashboard avançado nesta versão.
- Não escrever diretamente no Supabase pelo frontend.
