function App() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <header className="border-b border-slate-800 px-6 py-4">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xl font-bold tracking-tight text-white">AskGrid</span>
            <span className="text-xs rounded-full bg-emerald-500/15 text-emerald-300 px-2.5 py-0.5 border border-emerald-500/30">
              MVP-0
            </span>
          </div>
          <span className="text-sm text-slate-400">Don&apos;t Scroll, Just Ask.</span>
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center px-6 py-16">
        <section className="max-w-2xl text-center space-y-6">
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-white">
            Ask your spreadsheet anything.{' '}
            <span className="text-emerald-400">Verify every number.</span>
          </h1>
          <p className="text-slate-300 text-lg leading-relaxed">
            Upload a CSV, inspect an instant data profile, and ask questions in plain English.
            All calculations run deterministically in Python — never guessed by an AI.
          </p>
          <div className="flex flex-wrap justify-center gap-3 pt-2 text-xs text-slate-300">
            <span className="rounded-lg bg-slate-900 border border-slate-800 px-3 py-1.5">
              Schema-only AI prompts
            </span>
            <span className="rounded-lg bg-slate-900 border border-slate-800 px-3 py-1.5">
              Deterministic Pandas math
            </span>
            <span className="rounded-lg bg-slate-900 border border-slate-800 px-3 py-1.5">
              Ephemeral session privacy
            </span>
          </div>
        </section>
      </main>
    </div>
  )
}

export default App
