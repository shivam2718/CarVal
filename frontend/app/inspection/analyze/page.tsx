'use client'
// Review 2 demo flow: images + RC/insurance/service docs -> backend -> Vision + Document AI -> results page
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  createInspection, uploadImages, uploadDocuments, runVision, runDocumentExtraction,
} from '../../../lib/api'

type Step = 'idle' | 'creating' | 'uploading' | 'analyzing' | 'done'

export default function AnalyzePage() {
  const router = useRouter()
  const [images, setImages] = useState<File[]>([])
  const [rc, setRc] = useState<File[]>([])
  const [insurance, setInsurance] = useState<File[]>([])
  const [service, setService] = useState<File[]>([])
  const [step, setStep] = useState<Step>('idle')
  const [error, setError] = useState<string | null>(null)
  const [warnings, setWarnings] = useState<string[]>([])

  const hasDocs = rc.length + insurance.length + service.length > 0
  const busy = step !== 'idle' && step !== 'done'
  const canRun = (images.length > 0 || hasDocs) && !busy

  async function handleAnalyze() {
    setError(null); setWarnings([])
    try {
      setStep('creating')
      const { inspection_id: id } = await createInspection()

      setStep('uploading')
      if (images.length) await uploadImages(id, images)
      if (rc.length) await uploadDocuments(id, rc, 'rc')
      if (insurance.length) await uploadDocuments(id, insurance, 'insurance')
      if (service.length) await uploadDocuments(id, service, 'service')

      setStep('analyzing')
      // Vision and Document AI are independent -> run in parallel; one failing must not block the other
      const jobs: Promise<unknown>[] = []
      const names: string[] = []
      if (images.length) { jobs.push(runVision(id)); names.push('Vision') }
      if (hasDocs) { jobs.push(runDocumentExtraction(id)); names.push('Document AI') }
      const settled = await Promise.allSettled(jobs)
      const failed = settled
        .map((s, i) => (s.status === 'rejected' ? `${names[i]}: ${(s.reason as Error).message}` : null))
        .filter(Boolean) as string[]
      if (failed.length === settled.length) throw new Error(failed.join(' | '))
      setWarnings(failed)

      setStep('done')
      router.push(`/results/${id}`)
    } catch (e) {
      setError((e as Error).message)
      setStep('idle')
    }
  }

  const Picker = ({ label, hint, accept, multiple, files, onChange }: {
    label: string; hint: string; accept: string; multiple?: boolean; files: File[]; onChange: (f: File[]) => void
  }) => (
    <div className="rounded-xl border border-cyan-500/20 bg-gray-900/60 p-5">
      <p className="text-white font-semibold">{label}</p>
      <p className="text-gray-400 text-xs mb-3">{hint}</p>
      <input
        type="file" accept={accept} multiple={multiple} disabled={busy}
        onChange={(e) => onChange(Array.from(e.target.files ?? []))}
        className="text-sm text-gray-300"
      />
      {files.length > 0 && <p className="text-cyan-400 text-xs mt-2">{files.map((f) => f.name).join(', ')}</p>}
    </div>
  )

  const stepText: Record<Step, string> = {
    idle: 'Analyze Vehicle', creating: 'Creating inspection…', uploading: 'Uploading files…',
    analyzing: 'Running Vision + Document AI…', done: 'Done',
  }

  return (
    <main className="min-h-screen bg-black py-12">
      <div className="container mx-auto px-6 max-w-3xl space-y-6">
        <h1 className="text-4xl font-bold text-white">New Vehicle Inspection</h1>
        <Picker label="Car images" hint="JPG / PNG, up to 10 MB each (front, rear, sides, damage close-ups)"
          accept=".jpg,.jpeg,.png" multiple files={images} onChange={setImages} />
        <Picker label="RC (Registration Certificate)" hint="PDF / JPG / PNG"
          accept=".pdf,.jpg,.jpeg,.png" files={rc} onChange={setRc} />
        <Picker label="Insurance policy" hint="PDF / JPG / PNG"
          accept=".pdf,.jpg,.jpeg,.png" files={insurance} onChange={setInsurance} />
        <Picker label="Service bills" hint="PDF / JPG / PNG, one or more"
          accept=".pdf,.jpg,.jpeg,.png" multiple files={service} onChange={setService} />

        {error && <div className="p-4 rounded-lg border border-red-500/40 bg-red-500/10 text-red-300 text-sm">{error}</div>}
        {warnings.length > 0 && (
          <div className="p-4 rounded-lg border border-yellow-500/40 bg-yellow-500/10 text-yellow-300 text-sm">
            Partial result: {warnings.join(' | ')}
          </div>
        )}

        <button
          onClick={handleAnalyze} disabled={!canRun}
          className="w-full py-4 rounded-lg font-semibold text-white bg-gradient-to-r from-cyan-600 to-blue-600
                     hover:from-cyan-500 hover:to-blue-500 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {stepText[step]}
        </button>
      </div>
    </main>
  )
}