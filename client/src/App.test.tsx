import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import App from './App'

describe('App', () => {
    it('renders the AskGrid brand and core value proposition', () => {
        render(<App />)

        expect(screen.getByText('AskGrid')).toBeInTheDocument()
        expect(screen.getByText("Don't Scroll, Just Ask.")).toBeInTheDocument()
        expect(screen.getByText(/Verify every number\./i)).toBeInTheDocument()
    })
})
