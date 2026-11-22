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
        <section className="max-w-3xl mx-auto space-y-6">
            <div className="text-center space-y-3">
                <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-white">
                    Ask your spreadsheet anything.{' '}
                    <span className="text-emerald-400">Verify every number.</span>
                </h1>
                <p className="text-slate-300 text-base sm:text-lg leading-relaxed">
                    Upload a CSV or try our sample dataset. All math runs deterministically in Python —
                    never guessed by an AI.
                </p>
            </div>

            <div
                onDragOver={(e) => {
                    e.preventDefault()
                    setIsDragging(true)
                }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={handleDrop}
                className={`rounded-2xl border-2 border-dashed p-8 text-center transition-colors ${isDragging
                        ? 'border-emerald-400 bg-emerald-500/10'
                        : 'border-slate-700 bg-slate-900/70 hover:border-slate-500'
                    }`}
            >
                <p className="text-lg font-medium text-white">Drop your CSV file here</p>
                <p className="text-sm text-slate-400 mt-1">
                    Supports UTF-8 / Windows-1252, comma/semicolon/tab delimiters, currency &amp; DD/MM/YYYY
                    dates (max 10 MB, 100k rows)
                </p>

                <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
                    <label
                        htmlFor="csv-file-input"
                        className={`inline-flex items-center rounded-lg bg-emerald-500 px-5 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-emerald-400 ${isLoading ? 'opacity-60 pointer-events-none' : 'cursor-pointer'
                            }`}
                    >
                        {isLoading ? 'Processing CSV...' : 'Choose CSV File'}
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
                        className="rounded-lg border border-slate-700 bg-slate-800 px-5 py-2.5 text-sm font-medium text-slate-100 transition hover:border-emerald-500/60 hover:text-white disabled:opacity-50 cursor-pointer"
                    >
                        Try Sample Dataset
                    </button>
                </div>
            </div>

            {errorMessage && (
                <div
                    role="alert"
                    className="rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-200"
                >
                    {errorMessage}
                </div>
            )}

            <div className="rounded-xl border border-slate-800 bg-slate-900/50 px-5 py-4 text-xs sm:text-sm text-slate-300 space-y-1">
                <p className="font-semibold text-emerald-300">Privacy &amp; AI Processing Notice</p>
                <p>
                    Only your dataset schema (column names and inferred types) is sent to the AI model —{' '}
                    <strong className="text-white">never raw spreadsheet rows</strong>. Uploaded files live
                    in temporary session storage, auto-delete after 60 minutes, and can be deleted
                    immediately anytime. Avoid uploading confidential production files during beta.
                </p>
            </div>
        </section>
    )
}
