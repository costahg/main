function App() {
  return (
    <main className="min-h-screen bg-slate-50 px-6 py-12 text-slate-950">
      <section className="mx-auto flex min-h-[calc(100vh-6rem)] max-w-3xl flex-col items-center justify-center text-center">
        <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
          <p className="mb-3 text-sm font-medium uppercase tracking-widest text-slate-500">
            MVP Frontend
          </p>

          <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
            React + Vite pronto no Termux
          </h1>

          <p className="mt-4 text-base leading-7 text-slate-600">
            Esse frontend está preparado para rodar localmente no Android e
            depois ser publicado no Cloudflare Pages como site estático.
          </p>

          <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:justify-center">
            <a
              href="https://vite.dev"
              target="_blank"
              rel="noreferrer"
              className="rounded-lg bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
            >
              Ver Vite
            </a>

            <a
              href="https://developers.cloudflare.com/pages/"
              target="_blank"
              rel="noreferrer"
              className="rounded-lg border border-slate-300 px-5 py-3 text-sm font-semibold text-slate-900 transition hover:bg-slate-100"
            >
              Cloudflare Pages
            </a>
          </div>
        </div>
      </section>
    </main>
  )
}

export default App
