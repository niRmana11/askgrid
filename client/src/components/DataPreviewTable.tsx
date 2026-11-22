import type { DatasetProfile } from '../types/api'

interface DataPreviewTableProps {
    profile: DatasetProfile
}

export function DataPreviewTable({ profile }: DataPreviewTableProps) {
    const columnNames = profile.columns.map((c) => c.name)

    return (
        <section className="rounded-2xl border border-slate-800 bg-slate-900/60 overflow-hidden">
            <div className="border-b border-slate-800 px-5 py-3 flex items-center justify-between">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Data Preview (First {profile.preview_rows.length} of {profile.row_count.toLocaleString()}{' '}
                    Rows)
                </h3>
            </div>
            <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                    <thead className="bg-slate-950/80 text-slate-300 border-b border-slate-800">
                        <tr>
                            {columnNames.map((name) => (
                                <th key={name} className="px-4 py-2.5 font-semibold whitespace-nowrap">
                                    {name}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/70">
                        {profile.preview_rows.map((row, rowIdx) => (
                            <tr key={rowIdx} className="hover:bg-slate-800/40">
                                {columnNames.map((col) => {
                                    const val = row[col]
                                    return (
                                        <td key={col} className="px-4 py-2 whitespace-nowrap text-slate-200">
                                            {val === null || val === undefined ? (
                                                <span className="italic text-slate-500">null</span>
                                            ) : (
                                                String(val)
                                            )}
                                        </td>
                                    )
                                })}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </section>
    )
}
