import { useState, type ChangeEvent, type DragEvent } from 'react'

interface UploadPanelProps {
  isLoading: boolean
  errorMessage: string | null
  onUploadFile: (file: File) => void
  onLoadSample: () => void
}

export function UploadPanel({
  isLoading,
  errorMessage,
  onUploadFile,
  onLoadSample,
}: UploadPanelProps) {
  const [isDragging, setIsDragging] = useState(false)

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      onUploadFile(file)
      event.target.value = ''
    }
  }

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setIsDragging(false)
    const file = event.dataTransfer.files?.[0]
    if (file) {
      onUploadFile(file)
    }
  }

  return (
    <section className="max-w-3xl mx-auto space-y-8 py-4">
      <div className="text-center space-y-4">
        <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-4 py-1.5 text-sm font-medium text-emerald-300">
          <span className="h-2 w-2 rounded-full bg-emerald-400" />
          Private · Accurate · Free Beta
        </div>
        <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-white leading-tight">
          Ask your spreadsheet anything.{' '}
          <span className="text-emerald-400">Trust every number.</span>
        </h1>
        <p className="text-slate-300 text-lg sm:text-xl leading-relaxed max-w-2xl mx-auto">
          Upload a CSV file and ask questions in plain English. Get instant charts, exact
          calculations, and a clear explanation of how every answer was found.
        </p>
      </div>

      <div
        onDragOver={(e) => {
          e.preventDefault()
          setIsDragging(true)
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={`rounded-2xl border-2 border-dashed p-10 text-center transition-all duration-200 ${
          isDragging
            ? 'border-emerald-400 bg-emerald-500/10 scale-[1.01]'
            : 'border-slate-700 bg-slate-900/70 hover:border-emerald-500/50 hover:bg-slate-900'
        }`}
      >
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-300">
          <svg
            className="h-7 w-7"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.8}
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
            />
          </svg>
        </div>

        <p className="text-xl font-semibold text-white">Drop your CSV file here</p>
        <p className="text-base text-slate-400 mt-1.5">
          Works with standard CSV spreadsheets up to 10 MB (100,000 rows)
        </p>

        <div className="mt-7 flex flex-wrap items-center justify-center gap-4">
          <label
            htmlFor="csv-file-input"
            className={`inline-flex items-center rounded-xl bg-emerald-500 px-6 py-3 text-base font-semibold text-slate-950 shadow-lg shadow-emerald-500/15 transition hover:bg-emerald-400 ${
              isLoading ? 'opacity-60 pointer-events-none' : 'cursor-pointer'
            }`}
          >
            {isLoading ? 'Loading your spreadsheet...' : 'Choose CSV File'}
          </label>
          <input
            id="csv-file-input"
            type="file"
            accept=".csv,text/csv"
            disabled={isLoading}
            onChange={handleFileChange}
            className="sr-only"
          />

          <button
            type="button"
            disabled={isLoading}
            onClick={onLoadSample}
            className="rounded-xl border border-slate-600 bg-slate-800 px-6 py-3 text-base font-semibold text-white transition hover:border-emerald-400 hover:bg-slate-700 disabled:opacity-50 cursor-pointer"
          >
            Try Sample Dataset
          </button>
        </div>
      </div>

      {errorMessage && (
        <div
          role="alert"
          className="rounded-xl border border-rose-500/40 bg-rose-500/10 px-5 py-4 text-base text-rose-200"
        >
          {errorMessage}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 space-y-1.5">
          <p className="text-base font-semibold text-white">Exact Answers</p>
          <p className="text-sm text-slate-300 leading-relaxed">
            Every total, chart, and percentage is calculated directly from your data — never
            guessed.
          </p>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 space-y-1.5">
          <p className="text-base font-semibold text-white">Your Rows Stay Private</p>
          <p className="text-sm text-slate-300 leading-relaxed">
            Only column titles are used to understand your question — never your actual spreadsheet
            rows.
          </p>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 space-y-1.5">
          <p className="text-base font-semibold text-white">Temporary by Design</p>
          <p className="text-sm text-slate-300 leading-relaxed">
            Files auto-delete after 60 minutes, or instantly in one click whenever you finish.
          </p>
        </div>
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900/40 px-5 py-4 text-sm text-slate-300 leading-relaxed">
        <span className="font-semibold text-emerald-300">Privacy &amp; AI Processing Notice: </span>
        To understand your questions, AskGrid shares only your column names and data types with the
        AI — <strong className="text-white">never raw spreadsheet rows</strong>. Avoid uploading
        confidential business records during this free beta.
      </div>
    </section>
  )
}
