import { useState } from 'react'

import type { AnalysisResponse } from '../types/api'
import { ResultChart } from './ResultChart'

interface ResultCardProps {
  question: string
  response: AnalysisResponse
  onFeedback: (operation: string, isHelpful: boolean) => Promise<void>
}

const HUMAN_OP_LABELS: Record<string, string> = {
  describe_dataset: 'Dataset Overview',
  aggregate: 'Summary Calculation',
  group_aggregate: 'Grouped Breakdown',
  top_n: 'Top / Bottom Ranking',
  filter_rows: 'Filtered Row Lookup',
  time_series: 'Trend Over Time',
  compare: 'Side-by-Side Comparison',
  distribution: 'Value Distribution',
  correlation: 'Relationship (Correlation)',
  quality_report: 'Data Quality Check',
}

export function ResultCard({ question, response, onFeedback }: ResultCardProps) {
  const [showAudit, setShowAudit] = useState(false)
  const [rated, setRated] = useState<'up' | 'down' | null>(null)
  const [copied, setCopied] = useState(false)

  const handleRate = async (isHelpful: boolean) => {
    const op = response.audit?.operation ?? response.status
    setRated(isHelpful ? 'up' : 'down')
    try {
      await onFeedback(op, isHelpful)
    } catch {
      // Non-blocking feedback error
    }
  }

  const handleCopy = async () => {
    const text = `${response.headline}\n${response.explanation}`
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 1800)
    } catch {
      // Clipboard API may be unavailable in restricted contexts
    }
  }

  const badge =
    response.status === 'ok'
      ? {
          label: 'Verified Answer',
          cls: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
        }
      : response.status === 'clarification_needed'
        ? {
            label: 'Needs Clarification',
            cls: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
          }
        : {
            label: 'Not Supported Yet',
            cls: 'bg-slate-700/70 text-slate-200 border-slate-600',
          }

  return (
    <article className="rounded-2xl border border-slate-800 bg-slate-900/75 p-6 space-y-5 shadow-lg shadow-black/20">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm font-medium text-slate-300">
          <span className="text-slate-500 mr-1">You asked:</span>
          &ldquo;{question}&rdquo;
        </p>
        <div className="flex items-center gap-2">
          <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${badge.cls}`}>
            {badge.label}
          </span>
          <button
            type="button"
            onClick={() => void handleCopy()}
            className="rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-1 text-xs font-medium text-slate-300 transition hover:border-slate-500 hover:text-white cursor-pointer"
          >
            {copied ? 'Copied!' : 'Copy'}
          </button>
        </div>
      </div>

      <div className="space-y-1.5">
        <h3 className="text-xl sm:text-2xl font-bold text-white leading-snug">
          {response.headline}
        </h3>
        <p className="text-base text-slate-300 leading-relaxed">{response.explanation}</p>
        {response.suggested_alternative && (
          <p className="text-sm text-emerald-300 pt-1">
            Tip: {response.suggested_alternative}
          </p>
        )}
      </div>

      <ResultChart chart={response.chart} rows={response.rows} data={response.data} />

      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-800 pt-4">
        {response.audit ? (
          <button
            type="button"
            onClick={() => setShowAudit((prev) => !prev)}
            className="text-sm font-medium text-emerald-400 hover:text-emerald-300 transition cursor-pointer"
          >
            {showAudit ? 'Hide' : 'Show'} how this was calculated
          </button>
        ) : (
          <span />
        )}

        <div className="flex items-center gap-2 text-sm text-slate-400">
          <span>Was this accurate?</span>
          <button
            type="button"
            disabled={rated !== null}
            onClick={() => void handleRate(true)}
            aria-label="Mark answer helpful"
            className={`rounded-lg border px-3 py-1.5 text-sm font-medium transition cursor-pointer ${
              rated === 'up'
                ? 'border-emerald-400 bg-emerald-500/20 text-emerald-200'
                : 'border-slate-700 hover:border-emerald-500/60 text-slate-200 disabled:opacity-50'
            }`}
          >
            Correct
          </button>
          <button
            type="button"
            disabled={rated !== null}
            onClick={() => void handleRate(false)}
            aria-label="Mark answer wrong"
            className={`rounded-lg border px-3 py-1.5 text-sm font-medium transition cursor-pointer ${
              rated === 'down'
                ? 'border-rose-400 bg-rose-500/20 text-rose-200'
                : 'border-slate-700 hover:border-rose-500/60 text-slate-200 disabled:opacity-50'
            }`}
          >
            Wrong
          </button>
        </div>
      </div>

      {showAudit && response.audit && (
        <div className="rounded-xl border border-slate-800 bg-slate-950/90 p-4 text-sm text-slate-300 grid grid-cols-1 sm:grid-cols-2 gap-3">
          <p>
            <span className="text-slate-400">Method:</span>{' '}
            <span className="font-medium text-emerald-300">
              {HUMAN_OP_LABELS[response.audit.operation] ?? response.audit.operation}
            </span>
          </p>
          <p>
            <span className="text-slate-400">Columns used:</span>{' '}
            <span className="text-white">{response.audit.columns_used.join(', ') || 'All'}</span>
          </p>
          <p>
            <span className="text-slate-400">Rows checked:</span>{' '}
            <span className="text-white">
              {response.audit.rows_matched.toLocaleString()} of{' '}
              {response.audit.rows_scanned.toLocaleString()}
            </span>
          </p>
          <p>
            <span className="text-slate-400">Missing values skipped:</span>{' '}
            <span className="text-white">{response.audit.nulls_excluded}</span>
          </p>
          <p className="sm:col-span-2">
            <span className="text-slate-400">Filters applied:</span>{' '}
            <span className="text-white">
              {response.audit.filters_applied.length > 0
                ? response.audit.filters_applied.join(' AND ')
                : 'None (entire spreadsheet)'}
            </span>
          </p>
          {response.audit.date_format_used && (
            <p className="sm:col-span-2">
              <span className="text-slate-400">Date format recognized:</span>{' '}
              <span className="text-white">{response.audit.date_format_used}</span>
            </p>
          )}
        </div>
      )}
    </article>
  )
}
