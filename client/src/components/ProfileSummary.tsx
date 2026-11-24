import type { ColumnProfile, ColumnType, DatasetSessionResponse } from '../types/api'

interface ProfileHeaderProps {
  session: DatasetSessionResponse
  isDeleting: boolean
  onDeleteSession: () => void
}

interface ColumnsExplorerProps {
  columns: ColumnProfile[]
  onAskAboutColumn: (question: string) => void
}

const HUMAN_TYPE_LABELS: Record<ColumnType, { label: string; style: string }> = {
  integer: { label: 'Number', style: 'bg-sky-500/15 text-sky-300 border-sky-500/30' },
  float: { label: 'Number', style: 'bg-indigo-500/15 text-indigo-300 border-indigo-500/30' },
  date: { label: 'Date', style: 'bg-amber-500/15 text-amber-300 border-amber-500/30' },
  boolean: { label: 'Yes / No', style: 'bg-purple-500/15 text-purple-300 border-purple-500/30' },
  string: { label: 'Text', style: 'bg-slate-700/70 text-slate-200 border-slate-600' },
}

function buildColumnQuestion(col: ColumnProfile): string {
  if (col.inferred_type === 'integer' || col.inferred_type === 'float') {
    return `Show the distribution and average of ${col.name}`
  }
  if (col.inferred_type === 'date') {
    return `Show the monthly trend using ${col.name}`
  }
  return `What are the top values in ${col.name}?`
}

export function ProfileSummary({
  session,
  isDeleting,
  onDeleteSession,
}: ProfileHeaderProps) {
  const { profile } = session
  const totalMissing = profile.columns.reduce((sum, col) => sum + col.missing_count, 0)

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-slate-800 bg-slate-900/80 px-6 py-4">
        <div className="space-y-1">
          <div className="flex flex-wrap items-center gap-2.5">
            <h2 className="text-xl font-bold text-white">{session.filename}</h2>
            {session.is_sample && (
              <span className="rounded-full bg-emerald-500/15 px-3 py-0.5 text-sm font-medium text-emerald-300 border border-emerald-500/30">
                Sample Dataset
              </span>
            )}
          </div>
          <p className="text-sm text-slate-400">
            Temporary session · Auto-deletes after 60 minutes · Only column titles are shared with
            AI
          </p>
        </div>

        <button
          type="button"
          disabled={isDeleting}
          onClick={onDeleteSession}
          className="rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-2.5 text-sm font-semibold text-rose-200 transition hover:bg-rose-500/20 disabled:opacity-50 cursor-pointer"
        >
          {isDeleting ? 'Deleting...' : 'Delete Session Data'}
        </button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <p className="text-sm text-slate-400">Total Rows</p>
          <p className="mt-1 text-2xl sm:text-3xl font-bold text-white">
            {profile.row_count.toLocaleString()}
          </p>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <p className="text-sm text-slate-400">Columns</p>
          <p className="mt-1 text-2xl sm:text-3xl font-bold text-white">{profile.column_count}</p>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <p className="text-sm text-slate-400">Missing Values</p>
          <p
            className={`mt-1 text-2xl sm:text-3xl font-bold ${
              totalMissing > 0 ? 'text-amber-300' : 'text-emerald-400'
            }`}
          >
            {totalMissing.toLocaleString()}
          </p>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <p className="text-sm text-slate-400">Duplicate Rows</p>
          <p
            className={`mt-1 text-2xl sm:text-3xl font-bold ${
              profile.duplicate_row_count > 0 ? 'text-amber-300' : 'text-emerald-400'
            }`}
          >
            {profile.duplicate_row_count.toLocaleString()}
          </p>
        </div>
      </div>
    </section>
  )
}

export function ColumnsExplorer({ columns, onAskAboutColumn }: ColumnsExplorerProps) {
  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="text-base font-semibold text-white">Columns in Your Spreadsheet</h3>
          <p className="text-sm text-slate-400">
            Click any column to ask a quick question about it automatically.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {columns.map((col) => {
          const typeBadge = HUMAN_TYPE_LABELS[col.inferred_type]
          return (
            <button
              key={col.name}
              type="button"
              onClick={() => onAskAboutColumn(buildColumnQuestion(col))}
              className="group text-left rounded-xl border border-slate-800 bg-slate-950/70 p-4 space-y-2 transition hover:border-emerald-500/60 hover:bg-slate-900 cursor-pointer"
            >
              <div className="flex items-center justify-between gap-2">
                <span
                  className="text-base font-semibold text-white truncate group-hover:text-emerald-300 transition"
                  title={col.name}
                >
                  {col.name}
                </span>
                <span
                  className={`rounded-md border px-2 py-0.5 text-xs font-medium ${typeBadge.style}`}
                >
                  {typeBadge.label}
                </span>
              </div>

              <p className="text-sm text-slate-300">
                {col.unique_count.toLocaleString()} unique ·{' '}
                <span className={col.missing_count > 0 ? 'text-amber-300' : 'text-slate-400'}>
                  {col.missing_count} missing
                </span>
              </p>

              {col.min_value !== null && col.max_value !== null ? (
                <p className="text-sm text-slate-400 truncate">
                  Range: {col.min_value} → {col.max_value}
                </p>
              ) : col.top_values.length > 0 ? (
                <p className="text-sm text-slate-400 truncate">
                  Common: {col.top_values.slice(0, 3).join(', ')}
                </p>
              ) : null}

              <p className="text-xs font-medium text-emerald-400 opacity-80 group-hover:opacity-100">
                Ask about {col.name} →
              </p>
            </button>
          )
        })}
      </div>
    </section>
  )
}
