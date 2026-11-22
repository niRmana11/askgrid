export type ColumnType = 'integer' | 'float' | 'date' | 'boolean' | 'string'
export type JsonScalar = string | number | boolean | null

export interface ColumnProfile {
    name: string
    inferred_type: ColumnType
    missing_count: number
    unique_count: number
    min_value: number | string | null
    max_value: number | string | null
    mean_value: number | null
    median_value: number | null
    top_values: string[]
}

export interface DatasetProfile {
    row_count: number
    column_count: number
    duplicate_row_count: number
    encoding: string
    delimiter: string
    date_format_note: string | null
    columns: ColumnProfile[]
    preview_rows: Record<string, JsonScalar>[]
}

export interface DatasetSessionResponse {
    session_id: string
    filename: string
    is_sample: boolean
    expires_at: string
    privacy_notice: string
    profile: DatasetProfile
}

export interface DeleteSessionResponse {
    session_id: string
    deleted: boolean
}

export type ChartType =
    | 'kpi'
    | 'bar'
    | 'horizontal_bar'
    | 'line'
    | 'histogram'
    | 'scatter'
    | 'delta'
    | 'table'

export interface CalculationAudit {
    operation: string
    columns_used: string[]
    filters_applied: string[]
    rows_scanned: number
    rows_matched: number
    nulls_excluded: number
    date_format_used: string | null
    execution_ms: number
}

export interface ChartPoint {
    label: string
    value: number
    pct_of_total: number | null
    x_value: number | null
}

export interface ChartSpec {
    chart_type: ChartType
    title: string
    x_label: string | null
    y_label: string | null
    points: ChartPoint[]
}

export interface AnalysisResponse {
    status: 'ok' | 'unsupported' | 'clarification_needed'
    headline: string
    explanation: string
    data: Record<string, unknown>
    rows: Record<string, JsonScalar>[]
    chart: ChartSpec | null
    audit: CalculationAudit | null
    suggested_alternative: string | null
}

export interface FeedbackResponse {
    recorded: boolean
    total_helpful: number
    total_unhelpful: number
}
