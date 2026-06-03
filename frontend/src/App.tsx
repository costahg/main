function App() {
  return (
    <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-50">
      <section className="mx-auto flex min-h-[calc(100vh-5rem)] max-w-4xl flex-col items-center justify-center text-center">
        <div className="rounded-full border border-slate-700 bg-slate-900 px-4 py-2 text-sm text-slate-300">
          React + Vite + TypeScript + Tailwind
        </div>

        <h1 className="mt-8 max-w-3xl text-4xl font-bold tracking-tight sm:text-6xl">
          Frontend pronto para Cloudflare Pages
        </h1>

        <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-300">
          Esse projeto está rodando no Termux Android e será publicado como site
          estático. O backend FastAPI ficará separado no Cloud Run.
        </p>

        <div className="mt-10 flex flex-col gap-3 sm:flex-row">
          <a
            href="https://vite.dev"
            target="_blank"
            rel="noreferrer"
            className="rounded-xl bg-slate-50 px-5 py-3 font-medium text-slate-950 transition hover:bg-slate-200"
          >
            Ver Vite
          </a>

          <a
            href="https://developers.cloudflare.com/pages/"
            target="_blank"
            rel="noreferrer"
            className="rounded-xl border border-slate-700 px-5 py-3 font-medium text-slate-100 transition hover:bg-slate-900"
          >
            Cloudflare Pages
          </a>
        </div>
      </section>
    </main>
  )
}

export default App
