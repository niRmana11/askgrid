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
            'Is there a correlation between discount percentage and order quantity?',
        ]
    }
    const cols = session.profile.columns
    const numCol = cols.find((c) => c.inferred_type === 'float' || c.inferred_type === 'integer')
    const catCol = cols.find((c) => c.inferred_type === 'string')
    const dateCol = cols.find((c) => c.inferred_type === 'date')

    const suggestions = ['Check for missing values, duplicates, or numeric outliers']
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
        <section className="space-y-5">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                    <h3 className="text-sm font-semibold text-white">Ask a Question About Your Data</h3>
                    <span className="text-[11px] text-slate-400">
                        Schema-only AI routing · Deterministic Pandas execution
                    </span>
                </div>

                <form onSubmit={(e) => void handleSubmit(e)} className="flex flex-col sm:flex-row gap-3">
                    <input
                        type="text"
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        disabled={isAsking}
                        placeholder="e.g., Show revenue and percentage share by category..."
                        aria-label="Ask a question about your dataset"
                        className="flex-1 rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white placeholder-slate-500 focus:border-emerald-400 focus:outline-none disabled:opacity-60"
                    />
                    <button
                        type="submit"
                        disabled={isAsking || question.trim().length < 2}
                        className="rounded-xl bg-emerald-500 px-6 py-3 text-sm font-semibold text-slate-950 transition hover:bg-emerald-400 disabled:opacity-50 cursor-pointer"
                    >
                        {isAsking ? 'Calculating...' : 'Ask'}
                    </button>
                </form>

                <div className="flex flex-wrap gap-2">
                    {suggestions.map((item) => (
                        <button
                            key={item}
                            type="button"
                            disabled={isAsking}
                            onClick={() => void onAsk(item)}
                            className="rounded-full border border-slate-700 bg-slate-950/70 px-3 py-1.5 text-xs text-slate-300 transition hover:border-emerald-500/60 hover:text-emerald-200 disabled:opacity-50 cursor-pointer"
                        >
                            {item}
                        </button>
                    ))}
                </div>

                {askError && (
                    <div
                        role="alert"
                        className="rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-200"
                    >
                        {askError}
                    </div>
                )}
            </div>

            {history.length > 0 && (
                <div className="space-y-4">
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
