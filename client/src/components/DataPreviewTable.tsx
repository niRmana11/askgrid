import { useState } from 'react'

import type { DatasetProfile } from '../types/api'

interface DataPreviewTableProps {
  profile: DatasetProfile
}

export function DataPreviewTable({ profile }: DataPreviewTableProps) {
  const [search, setSearch] = useState('')
  const columnNames = profile.columns.map((c) => c.name)

  const query = search.trim().toLowerCase()
  const visibleRows = query
    ? profile.preview_rows.filter((row) =>
        columnNames.some((col) => {
          const val = row[col]
          return val !== null && val !== undefined && String(val).toLowerCase().includes(query)
        }),
      )
    : profile.preview_rows

  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/60 overflow-hidden">
      <div className="border-b border-slate-800 px-5 py-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-white">Spreadsheet Preview</h3>
          <p className="text-sm text-slate-400">
            Showing {visibleRows.length} of the first {profile.preview_rows.length} rows (total{' '}
            {profile.row_count.toLocaleString()} rows)
          </p>
        </div>

        <input
          type="search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Quick filter preview rows..."
          aria-label="Filter preview rows"
          className="w-full sm:w-64 rounded-xl border border-slate-700 bg-slate-950 px-3.5 py-2 text-sm text-white placeholder-slate-400 focus:border-emerald-400 focus:outline-none"
        />
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm border-collapse">
          <thead className="bg-slate-950/90 text-slate-200 border-b border-slate-800">
            <tr>
              {columnNames.map((name) => (
                <th key={name} className="px-4 py-3 font-semibold whitespace-nowrap">
                  {name}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/70">
            {visibleRows.length === 0 ? (
              <tr>
                <td
                  colSpan={columnNames.length}
                  className="px-4 py-8 text-center text-sm text-slate-400"
                >
                  No preview rows match &ldquo;{search}&rdquo;.
                </td>
              </tr>
            ) : (
              visibleRows.map((row, rowIdx) => (
                <tr key={rowIdx} className="hover:bg-slate-800/40 transition-colors">
                  {columnNames.map((col) => {
                    const val = row[col]
                    return (
                      <td key={col} className="px-4 py-3 whitespace-nowrap text-slate-200">
                        {val === null || val === undefined ? (
                          <span className="italic text-slate-500">empty</span>
                        ) : (
                          String(val)
                        )}
                      </td>
                    )
                  })}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  )
}
