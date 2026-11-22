import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import App from './App'
import type { DatasetSessionResponse } from './types/api'

const MOCK_SESSION: DatasetSessionResponse = {
    session_id: '11111111-2222-4333-8444-555555555555',
    filename: 'orders_sample.csv',
    is_sample: true,
    expires_at: '2026-11-22T20:00:00+00:00',
    privacy_notice: 'Only column names and types are sent to AI.',
    profile: {
        row_count: 24,
        column_count: 2,
        duplicate_row_count: 0,
        encoding: 'utf-8-sig',
        delimiter: ',',
        date_format_note: 'ISO (YYYY-MM-DD)',
        columns: [
            {
                name: 'order_id',
                inferred_type: 'string',
                missing_count: 0,
                unique_count: 24,
                min_value: null,
                max_value: null,
                mean_value: null,
                median_value: null,
                top_values: ['ORD-1001'],
            },
            {
                name: 'revenue',
                inferred_type: 'float',
                missing_count: 0,
                unique_count: 22,
                min_value: 7000,
                max_value: 122400,
                mean_value: 40007.92,
                median_value: 32150,
                top_values: [],
            },
        ],
        preview_rows: [{ order_id: 'ORD-1001', revenue: 7000 }],
    },
}

afterEach(() => {
    vi.restoreAllMocks()
})

describe('App dataset workspace', () => {
    it('renders upload panel, sample button, and AI privacy notice', () => {
        render(<App />)

        expect(screen.getByText('AskGrid')).toBeInTheDocument()
        expect(screen.getByText('Try Sample Dataset')).toBeInTheDocument()
        expect(screen.getByText(/Privacy & AI Processing Notice/i)).toBeInTheDocument()
    })

    it('loads sample dataset, displays profile/preview, and deletes session cleanly', async () => {
        const fetchMock = vi
            .fn()
            .mockResolvedValueOnce({
                ok: true,
                json: async () => MOCK_SESSION,
            })
            .mockResolvedValueOnce({
                ok: true,
                json: async () => ({ session_id: MOCK_SESSION.session_id, deleted: true }),
            })
        vi.stubGlobal('fetch', fetchMock)

        render(<App />)
        fireEvent.click(screen.getByRole('button', { name: 'Try Sample Dataset' }))

        await waitFor(() => {
            expect(screen.getByText('orders_sample.csv')).toBeInTheDocument()
        })
        expect(screen.getByText('ORD-1001')).toBeInTheDocument()
        expect(screen.getAllByText('revenue')).toHaveLength(2)

        fireEvent.click(screen.getByRole('button', { name: 'Delete Session Data' }))
        await waitFor(() => {
            expect(screen.getByText('Drop your CSV file here')).toBeInTheDocument()
        })
    })

    it('displays a friendly error banner when API returns an error', async () => {
        vi.stubGlobal(
            'fetch',
            vi.fn().mockResolvedValueOnce({
                ok: false,
                status: 400,
                json: async () => ({ detail: 'Binary file detected.' }),
            }),
        )

        render(<App />)
        fireEvent.click(screen.getByRole('button', { name: 'Try Sample Dataset' }))

        await waitFor(() => {
            expect(screen.getByRole('alert')).toHaveTextContent('Binary file detected.')
        })
    })
})
