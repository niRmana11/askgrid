import { useState } from 'react'

import {
  ApiError,
  askDatasetQuestion,
  deleteDatasetSession,
  loadSampleDataset,
  submitFeedback,
  uploadCsv,
} from './api/askgridApi'
import { AskWorkspace, type QAItem } from './components/AskWorkspace'
import { DataPreviewTable } from './components/DataPreviewTable'
import { ColumnsExplorer, ProfileSummary } from './components/ProfileSummary'
import { UploadPanel } from './components/UploadPanel'
import type { DatasetSessionResponse } from './types/api'

type WorkspaceTab = 'ask' | 'preview' | 'columns'

function App() {
  const [session, setSession] = useState<DatasetSessionResponse | null>(null)
  const [activeTab, setActiveTab] = useState<WorkspaceTab>('ask')
  const [isLoading, setIsLoading] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [qaHistory, setQaHistory] = useState<QAItem[]>([])
  const [isAsking, setIsAsking] = useState(false)
  const [askError, setAskError] = useState<string | null>(null)

  const handleUploadFile = async (file: File) => {
    setIsLoading(true)
    setErrorMessage(null)
    try {
      const result = await uploadCsv(file)
      setSession(result)
      setActiveTab('ask')
      setQaHistory([])
      setAskError(null)
    } catch (err) {
      setErrorMessage(
        err instanceof ApiError ? err.message : 'Could not reach AskGrid server. Is it running?',
      )
    } finally {
      setIsLoading(false)
    }
  }

  const handleLoadSample = async () => {
    setIsLoading(true)
    setErrorMessage(null)
    try {
      const result = await loadSampleDataset()
      setSession(result)
      setActiveTab('ask')
      setQaHistory([])
      setAskError(null)
    } catch (err) {
      setErrorMessage(
        err instanceof ApiError ? err.message : 'Could not load sample dataset. Is the API up?',
      )
    } finally {
      setIsLoading(false)
    }
  }

  const handleDeleteSession = async () => {
    if (!session) return
    setIsDeleting(true)
    setErrorMessage(null)
    try {
      await deleteDatasetSession(session.session_id)
      setSession(null)
      setActiveTab('ask')
      setQaHistory([])
      setAskError(null)
    } catch (err) {
      setErrorMessage(err instanceof ApiError ? err.message : 'Failed to delete session data.')
    } finally {
      setIsDeleting(false)
    }
  }

  const handleAsk = async (question: string) => {
    if (!session) return
    setActiveTab('ask')
    setIsAsking(true)
    setAskError(null)
    try {
      const response = await askDatasetQuestion(session.session_id, question)
      setQaHistory((prev) => [{ id: crypto.randomUUID(), question, response }, ...prev])
    } catch (err) {
      setAskError(
        err instanceof ApiError ? err.message : 'Could not complete analysis. Please try again.',
      )
    } finally {
      setIsAsking(false)
    }
  }

  const handleFeedback = async (operation: string, isHelpful: boolean) => {
    if (!session) return
    await submitFeedback(session.session_id, operation, isHelpful)
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <header className="sticky top-0 z-10 border-b border-slate-800 bg-slate-950/90 backdrop-blur px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="text-2xl font-bold tracking-tight text-white">AskGrid</span>
            <span className="text-xs font-semibold rounded-full bg-emerald-500/15 text-emerald-300 px-2.5 py-1 border border-emerald-500/30">
              Beta
            </span>
          </div>
          <span className="text-sm sm:text-base text-slate-300 font-medium">
            Don&apos;t Scroll, Just Ask.
          </span>
        </div>
      </header>

      <main className="flex-1 px-6 py-8">
        <div className="max-w-6xl mx-auto space-y-6">
          {!session ? (
            <UploadPanel
              isLoading={isLoading}
              errorMessage={errorMessage}
              onUploadFile={handleUploadFile}
              onLoadSample={handleLoadSample}
            />
          ) : (
            <>
              {errorMessage && (
                <div
                  role="alert"
                  className="rounded-xl border border-rose-500/40 bg-rose-500/10 px-5 py-4 text-base text-rose-200"
                >
                  {errorMessage}
                </div>
              )}

              <ProfileSummary
                session={session}
                isDeleting={isDeleting}
                onDeleteSession={handleDeleteSession}
              />

              <nav
                aria-label="Workspace sections"
                className="flex flex-wrap gap-2 border-b border-slate-800 pb-3"
              >
                <button
                  type="button"
                  onClick={() => setActiveTab('ask')}
                  className={`rounded-xl px-4 py-2.5 text-sm font-semibold transition cursor-pointer ${
                    activeTab === 'ask'
                      ? 'bg-emerald-500 text-slate-950'
                      : 'bg-slate-900 text-slate-300 hover:bg-slate-800 hover:text-white'
                  }`}
                >
                  Ask Questions{qaHistory.length > 0 ? ` (${qaHistory.length})` : ''}
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('preview')}
                  className={`rounded-xl px-4 py-2.5 text-sm font-semibold transition cursor-pointer ${
                    activeTab === 'preview'
                      ? 'bg-emerald-500 text-slate-950'
                      : 'bg-slate-900 text-slate-300 hover:bg-slate-800 hover:text-white'
                  }`}
                >
                  Data Preview ({session.profile.row_count.toLocaleString()} rows)
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('columns')}
                  className={`rounded-xl px-4 py-2.5 text-sm font-semibold transition cursor-pointer ${
                    activeTab === 'columns'
                      ? 'bg-emerald-500 text-slate-950'
                      : 'bg-slate-900 text-slate-300 hover:bg-slate-800 hover:text-white'
                  }`}
                >
                  Columns &amp; Types ({session.profile.column_count})
                </button>
              </nav>

              {activeTab === 'ask' && (
                <AskWorkspace
                  session={session}
                  history={qaHistory}
                  isAsking={isAsking}
                  askError={askError}
                  onAsk={handleAsk}
                  onClearHistory={() => setQaHistory([])}
                  onFeedback={handleFeedback}
                />
              )}

              {activeTab === 'preview' && <DataPreviewTable profile={session.profile} />}

              {activeTab === 'columns' && (
                <ColumnsExplorer
                  columns={session.profile.columns}
                  onAskAboutColumn={(q) => void handleAsk(q)}
                />
              )}
            </>
          )}
        </div>
      </main>

      <footer className="border-t border-slate-800/80 px-6 py-5 text-center text-sm text-slate-400">
        AskGrid Free Beta · Private, verified spreadsheet answers · Excel (.xlsx), saved history
        &amp; exports coming soon
      </footer>
    </div>
  )
}

export default App
