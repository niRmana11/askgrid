import { useState, type FormEvent } from 'react'

import type { AnalysisResponse, DatasetSessionResponse } from '../types/api'
import { ResultCard } from './ResultCard'

export interface QAItem {
  id: string
  question: string
  response: AnalysisResponse
}

interface AskWorkspaceProps {
  session: DatasetSessionResponse
  history: QAItem[]
  isAsking: boolean
  askError: string | null
  onAsk: (question: string) => Promise<void>
  onClearHistory: () => void
  onFeedback: (operation: string, isHelpful: boolean) => Promise<void>
}

function buildSuggestedQuestions(session: DatasetSessionResponse): string[] {
  if (session.is_sample) {
    return [
      'What is the total revenue?',
      'Show revenue and percentage share by category',
      'Top 3 customers by spend in Colombo',
      'Show monthly revenue trend',
      'Compare September 2026 vs October 2026 revenue',
      'Check for missing values, duplicates, or outliers',
    ]
  }
  const cols = session.profile.columns
  const numCol = cols.find((c) => c.inferred_type === 'float' || c.inferred_type === 'integer')
  const catCol = cols.find((c) => c.inferred_type === 'string')
  const dateCol = cols.find((c) => c.inferred_type === 'date')

  const suggestions = ['Check for missing values, duplicates, or outliers']
  if (numCol) suggestions.push(`What is the total and average ${numCol.name}?`)
  if (numCol && catCol) suggestions.push(`Top 5 ${catCol.name} by total ${numCol.name}`)
  if (numCol && dateCol) suggestions.push(`Show monthly ${numCol.name} trend`)
  return suggestions
}

export function AskWorkspace({
  session,
  history,
  isAsking,
  askError,
  onAsk,
  onClearHistory,
  onFeedback,
}: AskWorkspaceProps) {
  const [question, setQuestion] = useState('')
  const suggestions = buildSuggestedQuestions(session)

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const trimmed = question.trim()
    if (trimmed.length < 2 || isAsking) return
    setQuestion('')
    await onAsk(trimmed)
  }

  return (
    <section className="space-y-6">
      <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h3 className="text-lg font-bold text-white">Ask a Question in Plain English</h3>
            <p className="text-sm text-slate-400">
              Verified calculations directly on your spreadsheet — your rows stay private.
            </p>
          </div>
          {history.length > 0 && (
            <button
              type="button"
              onClick={onClearHistory}
              className="rounded-lg border border-slate-700 px-3 py-1.5 text-sm font-medium text-slate-300 transition hover:border-slate-500 hover:text-white cursor-pointer"
            >
              Clear Answers ({history.length})
            </button>
          )}
        </div>

        <form onSubmit={(e) => void handleSubmit(e)} className="flex flex-col sm:flex-row gap-3">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={isAsking}
            placeholder="e.g., Which product generated the highest revenue last month?"
            aria-label="Ask a question about your dataset"
            className="flex-1 rounded-xl border border-slate-700 bg-slate-950 px-4 py-3.5 text-base text-white placeholder-slate-400 focus:border-emerald-400 focus:outline-none disabled:opacity-60"
          />
          <button
            type="submit"
            disabled={isAsking || question.trim().length < 2}
            className="rounded-xl bg-emerald-500 px-7 py-3.5 text-base font-semibold text-slate-950 shadow-lg shadow-emerald-500/15 transition hover:bg-emerald-400 disabled:opacity-50 cursor-pointer"
          >
            {isAsking ? 'Calculating...' : 'Ask'}
          </button>
        </form>

        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Try a quick question
          </p>
          <div className="flex flex-wrap gap-2">
            {suggestions.map((item) => (
              <button
                key={item}
                type="button"
                disabled={isAsking}
                onClick={() => void onAsk(item)}
                className="rounded-full border border-slate-700 bg-slate-950/80 px-4 py-2 text-sm text-slate-200 transition hover:border-emerald-400 hover:bg-emerald-500/10 hover:text-emerald-200 disabled:opacity-50 cursor-pointer"
              >
                {item}
              </button>
            ))}
          </div>
        </div>

        {askError && (
          <div
            role="alert"
            className="rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-base text-rose-200"
          >
            {askError}
          </div>
        )}
      </div>

      {isAsking && (
        <div
          aria-live="polite"
          className="rounded-2xl border border-emerald-500/30 bg-slate-900/70 p-6 space-y-3 animate-pulse"
        >
          <div className="flex items-center gap-3 text-base font-medium text-emerald-300">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-400" />
            Understanding your question &amp; verifying numbers...
          </div>
          <div className="h-4 w-3/4 rounded bg-slate-800" />
          <div className="h-32 w-full rounded-xl bg-slate-800/70" />
        </div>
      )}

      {history.length > 0 && (
        <div className="space-y-5">
          {history.map((item) => (
            <ResultCard
              key={item.id}
              question={item.question}
              response={item.response}
              onFeedback={onFeedback}
            />
          ))}
        </div>
      )}
    </section>
  )
}
