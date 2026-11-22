import { useState } from 'react'

import type { AnalysisResponse } from '../types/api'
import { ResultChart } from './ResultChart'

interface ResultCardProps {
    question: string
    response: AnalysisResponse
    onFeedback: (operation: string, isHelpful: boolean) => Promise<void>
}

export function ResultCard({ question, response, onFeedback }: ResultCardProps) {
    const [showAudit, setShowAudit] = useState(false)
    const [rated, setRated] = useState<'up' | 'down' | null>(null)

    const handleRate = async (isHelpful: boolean) => {
        const op = response.audit?.operation ?? response.status
        setRated(isHelpful ? 'up' : 'down')
        try {
            await onFeedback(op, isHelpful)
        } catch {
            // Non-blocking feedback error
        }
    }

    const badge =
        response.status === 'ok'
            ? { label: 'Verified Python Math', cls: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30' }
            : response.status === 'clarification_needed'
                ? { label: 'Clarification Needed', cls: 'bg-amber-500/15 text-amber-300 border-amber-500/30' }
                : { label: 'Unsupported', cls: 'bg-slate-700/60 text-slate-200 border-slate-600' }

    return (
        <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 space-y-4">
            <div className="flex flex-wrap items-start justify-between gap-2">
                <p className="text-xs font-medium text-slate-400">Q: &ldquo;{question}&rdquo;</p>
                <span className={`rounded-full border px-2.5 py-0.5 text-[11px] font-medium ${badge.cls}`}>
                    {badge.label}
                </span>
            </div>

            <div className="space-y-1">
                <h3 className="text-lg sm:text-xl font-bold text-white">{response.headline}</h3>
                <p className="text-sm text-slate-300">{response.explanation}</p>
                {response.suggested_alternative && (
                    <p className="text-xs text-emerald-300 pt-1">
                        Suggestion: {response.suggested_alternative}
                    </p>
                )}
            </div>

            <ResultChart chart={response.chart} rows={response.rows} data={response.data} />

            <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-800 pt-3">
                {response.audit ? (
                    <button
                        type="button"
                        onClick={() => setShowAudit((prev) => !prev)}
                        className="text-xs font-medium text-emerald-400 hover:text-emerald-300 cursor-pointer"
                    >
                        {showAudit ? 'Hide' : 'Show'} how this was calculated ({response.audit.execution_ms} ms)
                    </button>
                ) : (
                    <span />
                )}

                <div className="flex items-center gap-2 text-xs text-slate-400">
                    <span>Helpful?</span>
                    <button
                        type="button"
                        disabled={rated !== null}
                        onClick={() => void handleRate(true)}
                        aria-label="Mark answer helpful"
                        className={`rounded-md border px-2.5 py-1 transition cursor-pointer ${rated === 'up'
                                ? 'border-emerald-400 bg-emerald-500/20 text-emerald-200'
                                : 'border-slate-700 hover:border-slate-500 text-slate-300 disabled:opacity-50'
                            }`}
                    >
                        Correct
                    </button>
                    <button
                        type="button"
                        disabled={rated !== null}
                        onClick={() => void handleRate(false)}
                        aria-label="Mark answer wrong"
                        className={`rounded-md border px-2.5 py-1 transition cursor-pointer ${rated === 'down'
                                ? 'border-rose-400 bg-rose-500/20 text-rose-200'
                                : 'border-slate-700 hover:border-slate-500 text-slate-300 disabled:opacity-50'
                            }`}
                    >
                        Wrong
                    </button>
                </div>
            </div>

            {showAudit && response.audit && (
                <div className="rounded-xl border border-slate-800 bg-slate-950/90 p-4 text-xs text-slate-300 grid grid-cols-1 sm:grid-cols-2 gap-2">
                    <p>
                        <span className="text-slate-500">Operation:</span>{' '}
                        <code className="text-emerald-300">{response.audit.operation}</code>
                    </p>
                    <p>
                        <span className="text-slate-500">Columns Used:</span>{' '}
                        {response.audit.columns_used.join(', ') || 'None'}
                    </p>
                    <p>
                        <span className="text-slate-500">Rows Matched:</span>{' '}
                        {response.audit.rows_matched.toLocaleString()} /{' '}
                        {response.audit.rows_scanned.toLocaleString()}
                    </p>
                    <p>
                        <span className="text-slate-500">Nulls Excluded:</span>{' '}
                        {response.audit.nulls_excluded}
                    </p>
                    <p className="sm:col-span-2">
                        <span className="text-slate-500">Filters Applied:</span>{' '}
                        {response.audit.filters_applied.length > 0
                            ? response.audit.filters_applied.join(' AND ')
                            : 'None'}
                    </p>
                    {response.audit.date_format_used && (
                        <p className="sm:col-span-2">
                            <span className="text-slate-500">Date Format Used:</span>{' '}
                            {response.audit.date_format_used}
                        </p>
                    )}
                </div>
            )}
        </article>
    )
}
