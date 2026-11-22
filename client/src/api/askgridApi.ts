import type {
    AnalysisResponse,
    DatasetSessionResponse,
    DeleteSessionResponse,
    FeedbackResponse,
} from '../types/api'

const API_BASE =
    (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, '') ||
    'http://127.0.0.1:8000'

export class ApiError extends Error {
    status: number

    constructor(message: string, status: number) {
        super(message)
        this.name = 'ApiError'
        this.status = status
    }
}

async function parseResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
        let detail = `Request failed (${response.status})`
        try {
            const errorBody = (await response.json()) as { detail?: string }
            if (typeof errorBody.detail === 'string' && errorBody.detail.trim()) {
                detail = errorBody.detail
            }
        } catch {
            // Fallback to HTTP status message when response body is not JSON
        }
        throw new ApiError(detail, response.status)
    }
    return (await response.json()) as T
}

export async function uploadCsv(file: File): Promise<DatasetSessionResponse> {
    const formData = new FormData()
    formData.append('file', file)
    const response = await fetch(`${API_BASE}/api/v1/datasets/upload`, {
        method: 'POST',
        body: formData,
    })
    return parseResponse<DatasetSessionResponse>(response)
}

export async function loadSampleDataset(): Promise<DatasetSessionResponse> {
    const response = await fetch(`${API_BASE}/api/v1/datasets/sample`, {
        method: 'POST',
    })
    return parseResponse<DatasetSessionResponse>(response)
}

export async function deleteDatasetSession(sessionId: string): Promise<DeleteSessionResponse> {
    const response = await fetch(`${API_BASE}/api/v1/datasets/${sessionId}`, {
        method: 'DELETE',
    })
    return parseResponse<DeleteSessionResponse>(response)
}

export async function askDatasetQuestion(
    sessionId: string,
    question: string,
): Promise<AnalysisResponse> {
    const response = await fetch(`${API_BASE}/api/v1/datasets/${sessionId}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
    })
    return parseResponse<AnalysisResponse>(response)
}

export async function submitFeedback(
    sessionId: string,
    operation: string,
    isHelpful: boolean,
): Promise<FeedbackResponse> {
    const response = await fetch(`${API_BASE}/api/v1/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            session_id: sessionId,
            operation,
            is_helpful: isHelpful,
        }),
    })
    return parseResponse<FeedbackResponse>(response)
}
