import type { ColumnType, DatasetSessionResponse } from '../types/api'

interface ProfileSummaryProps {
    session: DatasetSessionResponse
    isDeleting: boolean
    onDeleteSession: () => void
}

const TYPE_BADGE_STYLES: Record<ColumnType, string> = {
    integer: 'bg-sky-500/15 text-sky-300 border-sky-500/30',
    float: 'bg-indigo-500/15 text-indigo-300 border-indigo-500/30',
    date: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
    boolean: 'bg-purple-500/15 text-purple-300 border-purple-500/30',
    string: 'bg-slate-700/60 text-slate-200 border-slate-600',
}

export function ProfileSummary({
    session,
    isDeleting,
    onDeleteSession,
}: ProfileSummaryProps) {
    const { profile } = session
    const totalMissing = profile.columns.reduce((sum, col) => sum + col.missing_count, 0)

    return (
        <section className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-800 bg-slate-900/70 px-5 py-4">
                <div className="space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                        <h2 className="text-lg font-semibold text-white">{session.filename}</h2>
                        {session.is_sample && (
                            <span className="rounded-full bg-emerald-500/15 px-2.5 py-0.5 text-xs text-emerald-300 border border-emerald-500/30">
                                Sample Dataset
                            </span>
                        )}
                    </div>
                    <p className="text-xs text-slate-400">
                        Encoding: <span className="text-slate-200">{profile.encoding}</span> · Delimiter:{' '}
                        <span className="text-slate-200">{JSON.stringify(profile.delimiter)}</span>
                        {profile.date_format_note ? (
                            <>
                                {' '}
                                · Dates: <span className="text-slate-200">{profile.date_format_note}</span>
                            </>
                        ) : null}
                    </p>
                </div>

                <button
                    type="button"
                    disabled={isDeleting}
                    onClick={onDeleteSession}
                    className="rounded-lg border border-rose-500/40 bg-rose-500/10 px-4 py-2 text-xs font-semibold text-rose-200 transition hover:bg-rose-500/20 disabled:opacity-50 cursor-pointer"
                >
                    {isDeleting ? 'Deleting...' : 'Delete Session Data'}
                </button>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
                    <p className="text-xs text-slate-400">Rows</p>
                    <p className="mt-1 text-2xl font-bold text-white">
                        {profile.row_count.toLocaleString()}
                    </p>
                </div>
                <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
                    <p className="text-xs text-slate-400">Columns</p>
                    <p className="mt-1 text-2xl font-bold text-white">{profile.column_count}</p>
                </div>
                <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
                    <p className="text-xs text-slate-400">Missing Cells</p>
                    <p
                        className={`mt-1 text-2xl font-bold ${totalMissing > 0 ? 'text-amber-300' : 'text-emerald-400'
                            }`}
                    >
                        {totalMissing.toLocaleString()}
                    </p>
                </div>
                <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
                    <p className="text-xs text-slate-400">Duplicate Rows</p>
                    <p
                        className={`mt-1 text-2xl font-bold ${profile.duplicate_row_count > 0 ? 'text-amber-300' : 'text-emerald-400'
                            }`}
                    >
                        {profile.duplicate_row_count.toLocaleString()}
                    </p>
                </div>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 space-y-3">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Detected Schema (Sent to AI — Zero Raw Rows)
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
                    {profile.columns.map((col) => (
                        <div
                            key={col.name}
                            className="rounded-xl border border-slate-800 bg-slate-950/70 px-3 py-2.5 text-xs space-y-1"
                        >
                            <div className="flex items-center justify-between gap-2">
                                <span className="font-semibold text-white truncate" title={col.name}>
                                    {col.name}
                                </span>
                                <span
                                    className={`rounded-md border px-1.5 py-0.5 text-[10px] font-medium ${TYPE_BADGE_STYLES[col.inferred_type]
                                        }`}
                                >
                                    {col.inferred_type}
                                </span>
                            </div>
                            <p className="text-slate-400">
                                {col.unique_count} unique · {col.missing_count} missing
                            </p>
                            {col.min_value !== null && col.max_value !== null ? (
                                <p className="text-slate-500 truncate">
                                    Range: {col.min_value} → {col.max_value}
                                </p>
                            ) : col.top_values.length > 0 ? (
                                <p className="text-slate-500 truncate">
                                    Top: {col.top_values.slice(0, 3).join(', ')}
                                </p>
                            ) : null}
                        </div>
                    ))}
                </div>
            </div>
        </section>
    )
}
