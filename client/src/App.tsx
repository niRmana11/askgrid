import { useState } from 'react'

import { ApiError, deleteDatasetSession, loadSampleDataset, uploadCsv } from './api/askgridApi'
import { DataPreviewTable } from './components/DataPreviewTable'
import { ProfileSummary } from './components/ProfileSummary'
import { UploadPanel } from './components/UploadPanel'
import type { DatasetSessionResponse } from './types/api'

function App() {
  const [session, setSession] = useState<DatasetSessionResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const handleUploadFile = async (file: File) => {
    setIsLoading(true)
    setErrorMessage(null)
    try {
      const result = await uploadCsv(file)
      setSession(result)
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
    } catch (err) {
      setErrorMessage(err instanceof ApiError ? err.message : 'Failed to delete session data.')
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <header className="border-b border-slate-800 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xl font-bold tracking-tight text-white">AskGrid</span>
            <span className="text-xs rounded-full bg-emerald-500/15 text-emerald-300 px-2.5 py-0.5 border border-emerald-500/30">
              MVP-0
            </span>
          </div>
          <span className="text-sm text-slate-400">Don&apos;t Scroll, Just Ask.</span>
        </div>
      </header>

      <main className="flex-1 px-6 py-10">
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
                  className="rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-200"
                >
                  {errorMessage}
                </div>
              )}
              <ProfileSummary
                session={session}
                isDeleting={isDeleting}
                onDeleteSession={handleDeleteSession}
              />
              <DataPreviewTable profile={session.profile} />
            </>
          )}
        </div>
      </main>
    </div>
  )
}

export default App
