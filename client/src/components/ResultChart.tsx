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

const TOOLTIP_STYLE = {
    backgroundColor: '#0f172a',
    border: '1px solid #334155',
    borderRadius: '0.75rem',
    color: '#f1f5f9',
    fontSize: '12px',
}

export function ResultChart({ chart, rows, data }: ResultChartProps) {
    if (!chart) return null

    if (chart.chart_type === 'kpi' && chart.points.length > 0) {
        const point = chart.points[0]
        return (
            <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-5">
                <p className="text-xs uppercase tracking-wider text-emerald-300">{chart.title}</p>
                <p className="mt-1 text-3xl font-bold text-white">{point.value.toLocaleString()}</p>
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
                        <p className="text-xs text-slate-400">{first.label}</p>
                        <p className="mt-1 text-xl font-bold text-white">{first.value.toLocaleString()}</p>
                    </div>
                    <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
                        <p className="text-xs text-slate-400">{second.label}</p>
                        <p className="mt-1 text-xl font-bold text-white">{second.value.toLocaleString()}</p>
                    </div>
                    <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
                        <p className="text-xs text-slate-400">Change</p>
                        <p
                            className={`mt-1 text-xl font-bold ${isPositive ? 'text-emerald-400' : 'text-rose-400'
                                }`}
                        >
                            {diff >= 0 ? '+' : ''}
                            {diff.toLocaleString()}
                            {pct !== null ? ` (${pct >= 0 ? '+' : ''}${pct}%)` : ''}
                        </p>
                    </div>
                </div>
                <div className="h-56 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={chart.points} margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                            <XAxis dataKey="label" stroke="#94a3b8" fontSize={12} />
                            <YAxis stroke="#94a3b8" fontSize={12} />
                            <Tooltip contentStyle={TOOLTIP_STYLE} />
                            <Bar dataKey="value" fill="#10b981" radius={[6, 6, 0, 0]} />
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
                    <table className="w-full text-left text-xs border-collapse">
                        <thead className="bg-slate-950 text-slate-300 border-b border-slate-800">
                            <tr>
                                {cols.map((col) => (
                                    <th key={col} className="px-3 py-2 font-semibold whitespace-nowrap">
                                        {col}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/70">
                            {rows.map((row, idx) => (
                                <tr key={idx} className="hover:bg-slate-800/40">
                                    {cols.map((col) => (
                                        <td key={col} className="px-3 py-2 whitespace-nowrap text-slate-200">
                                            {row[col] === null || row[col] === undefined ? (
                                                <span className="italic text-slate-500">null</span>
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
        return (
            <pre className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950 p-4 text-xs text-slate-200">
                {JSON.stringify(data, null, 2)}
            </pre>
        )
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
                        <XAxis type="number" stroke="#94a3b8" fontSize={12} />
                        <YAxis type="category" dataKey="label" stroke="#94a3b8" fontSize={12} width={120} />
                        <Tooltip contentStyle={TOOLTIP_STYLE} />
                        <Bar dataKey="value" fill="#10b981" radius={[0, 6, 6, 0]} />
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
                        <XAxis dataKey="label" stroke="#94a3b8" fontSize={12} />
                        <YAxis stroke="#94a3b8" fontSize={12} />
                        <Tooltip contentStyle={TOOLTIP_STYLE} />
                        <Line
                            type="monotone"
                            dataKey="value"
                            stroke="#10b981"
                            strokeWidth={2.5}
                            dot={{ r: 4, fill: '#34d399' }}
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
                            stroke="#94a3b8"
                            fontSize={12}
                        />
                        <YAxis
                            type="number"
                            dataKey="value"
                            name={chart.y_label ?? 'Y'}
                            stroke="#94a3b8"
                            fontSize={12}
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
                    <XAxis dataKey="label" stroke="#94a3b8" fontSize={12} />
                    <YAxis stroke="#94a3b8" fontSize={12} />
                    <Tooltip contentStyle={TOOLTIP_STYLE} />
                    <Bar dataKey="value" fill="#10b981" radius={[6, 6, 0, 0]} />
                </BarChart>
            </ResponsiveContainer>
        </div>
    )
}
