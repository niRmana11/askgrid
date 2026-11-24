import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import type { ChartSpec, JsonScalar } from '../types/api'

interface ResultChartProps {
  chart: ChartSpec | null
  rows: Record<string, JsonScalar>[]
  data: Record<string, unknown>
}

interface OutlierEntry {
  count?: number
  lower_fence?: number
  upper_fence?: number
  sample_values?: number[]
}

const TOOLTIP_STYLE = {
  backgroundColor: '#0f172a',
  border: '1px solid #334155',
  borderRadius: '0.75rem',
  color: '#f8fafc',
  fontSize: '13px',
  padding: '8px 12px',
}

function QualityReportView({ data }: { data: Record<string, unknown> }) {
  const missingByCol =
    typeof data.missing_by_col === 'object' && data.missing_by_col !== null
      ? (data.missing_by_col as Record<string, number>)
      : {}
  const negativeCounts =
    typeof data.negative_counts === 'object' && data.negative_counts !== null
      ? (data.negative_counts as Record<string, number>)
      : {}
  const outliers =
    typeof data.iqr_outliers === 'object' && data.iqr_outliers !== null
      ? (data.iqr_outliers as Record<string, OutlierEntry>)
      : {}

  const missingEntries = Object.entries(missingByCol)
  const negativeEntries = Object.entries(negativeCounts)
  const outlierEntries = Object.entries(outliers)
  const exactDuplicates = typeof data.exact_duplicates === 'number' ? data.exact_duplicates : 0

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4 space-y-2">
        <p className="text-sm font-semibold text-white">Missing Values</p>
        {missingEntries.length === 0 ? (
          <p className="text-sm text-emerald-400">No missing values found.</p>
        ) : (
          <ul className="space-y-1 text-sm text-slate-300">
            {missingEntries.map(([col, count]) => (
              <li key={col} className="flex justify-between gap-2">
                <span className="truncate">{col}</span>
                <span className="font-semibold text-amber-300">{count}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4 space-y-2">
        <p className="text-sm font-semibold text-white">Duplicates &amp; Negatives</p>
        <p className="text-sm text-slate-300">
          Duplicate rows:{' '}
          <span
            className={`font-semibold ${
              exactDuplicates > 0 ? 'text-amber-300' : 'text-emerald-400'
            }`}
          >
            {exactDuplicates}
          </span>
        </p>
        {negativeEntries.length === 0 ? (
          <p className="text-sm text-slate-400">No negative numbers detected.</p>
        ) : (
          <ul className="space-y-1 text-sm text-slate-300">
            {negativeEntries.map(([col, count]) => (
              <li key={col} className="flex justify-between gap-2">
                <span className="truncate">Negative {col}</span>
                <span className="font-semibold text-amber-300">{count}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4 space-y-2">
        <p className="text-sm font-semibold text-white">Unusual Values (Outliers)</p>
        {outlierEntries.length === 0 ? (
          <p className="text-sm text-emerald-400">No unusual extreme numbers found.</p>
        ) : (
          <ul className="space-y-2 text-sm text-slate-300">
            {outlierEntries.map(([col, info]) => (
              <li key={col}>
                <div className="flex justify-between gap-2">
                  <span className="font-medium text-white truncate">{col}</span>
                  <span className="font-semibold text-amber-300">{info.count ?? 0} found</span>
                </div>
                {info.sample_values && info.sample_values.length > 0 && (
                  <p className="text-xs text-slate-400 mt-0.5">
                    Examples: {info.sample_values.map((v) => v.toLocaleString()).join(', ')}
                  </p>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

export function ResultChart({ chart, rows, data }: ResultChartProps) {
  if (!chart) return null

  if (chart.chart_type === 'kpi' && chart.points.length > 0) {
    const point = chart.points[0]
    return (
      <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-6 py-5">
        <p className="text-sm font-medium uppercase tracking-wide text-emerald-300">
          {chart.title}
        </p>
        <p className="mt-1.5 text-3xl sm:text-4xl font-bold text-white">
          {point.value.toLocaleString()}
        </p>
      </div>
    )
  }

  if (chart.chart_type === 'delta' && chart.points.length === 2) {
    const [first, second] = chart.points
    const diff = typeof data.diff === 'number' ? data.diff : second.value - first.value
    const pct = typeof data.pct_change === 'number' ? data.pct_change : null
    const isPositive = diff >= 0
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
            <p className="text-sm text-slate-400">{first.label}</p>
            <p className="mt-1 text-2xl font-bold text-white">{first.value.toLocaleString()}</p>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
            <p className="text-sm text-slate-400">{second.label}</p>
            <p className="mt-1 text-2xl font-bold text-white">{second.value.toLocaleString()}</p>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
            <p className="text-sm text-slate-400">Difference</p>
            <p
              className={`mt-1 text-2xl font-bold ${
                isPositive ? 'text-emerald-400' : 'text-rose-400'
              }`}
            >
              {diff >= 0 ? '+' : ''}
              {diff.toLocaleString()}
              {pct !== null ? ` (${pct >= 0 ? '+' : ''}${pct}%)` : ''}
            </p>
          </div>
        </div>
        <div className="h-60 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chart.points} margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="label" stroke="#cbd5e1" fontSize={13} />
              <YAxis stroke="#cbd5e1" fontSize={13} />
              <Tooltip contentStyle={TOOLTIP_STYLE} />
              <Bar dataKey="value" fill="#10b981" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    )
  }

  if (chart.chart_type === 'table') {
    if (rows.length > 0) {
      const cols = Object.keys(rows[0])
      return (
        <div className="overflow-x-auto rounded-xl border border-slate-800">
          <table className="w-full text-left text-sm border-collapse">
            <thead className="bg-slate-950 text-slate-200 border-b border-slate-800">
              <tr>
                {cols.map((col) => (
                  <th key={col} className="px-4 py-3 font-semibold whitespace-nowrap">
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/70">
              {rows.map((row, idx) => (
                <tr key={idx} className="hover:bg-slate-800/40">
                  {cols.map((col) => (
                    <td key={col} className="px-4 py-2.5 whitespace-nowrap text-slate-200">
                      {row[col] === null || row[col] === undefined ? (
                        <span className="italic text-slate-500">empty</span>
                      ) : (
                        String(row[col])
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )
    }
    return <QualityReportView data={data} />
  }

  if (chart.points.length === 0) return null

  if (chart.chart_type === 'horizontal_bar') {
    return (
      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chart.points}
            layout="vertical"
            margin={{ top: 8, right: 24, left: 24, bottom: 8 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis type="number" stroke="#cbd5e1" fontSize={13} />
            <YAxis type="category" dataKey="label" stroke="#cbd5e1" fontSize={13} width={140} />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Bar dataKey="value" fill="#10b981" radius={[0, 8, 8, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    )
  }

  if (chart.chart_type === 'line') {
    return (
      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chart.points} margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="label" stroke="#cbd5e1" fontSize={13} />
            <YAxis stroke="#cbd5e1" fontSize={13} />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Line
              type="monotone"
              dataKey="value"
              stroke="#10b981"
              strokeWidth={3}
              dot={{ r: 5, fill: '#34d399' }}
              activeDot={{ r: 7 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    )
  }

  if (chart.chart_type === 'scatter') {
    return (
      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis
              type="number"
              dataKey="x_value"
              name={chart.x_label ?? 'X'}
              stroke="#cbd5e1"
              fontSize={13}
            />
            <YAxis
              type="number"
              dataKey="value"
              name={chart.y_label ?? 'Y'}
              stroke="#cbd5e1"
              fontSize={13}
            />
            <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ strokeDasharray: '3 3' }} />
            <Scatter data={chart.points} fill="#34d399" />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    )
  }

  // Default: vertical bar chart (bar & histogram)
  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chart.points} margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis dataKey="label" stroke="#cbd5e1" fontSize={13} />
          <YAxis stroke="#cbd5e1" fontSize={13} />
          <Tooltip contentStyle={TOOLTIP_STYLE} />
          <Bar dataKey="value" fill="#10b981" radius={[8, 8, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
