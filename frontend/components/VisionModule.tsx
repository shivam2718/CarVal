'use client'
// Vision module: car photos in -> YOLOv8 damage detection (boxes, class, confidence) out.
import { useState } from 'react'
import DamageViewer from './DamageViewer'
import ModuleCard, { ErrorBox, buttonCls, errMsg } from './ModuleCard'
import { runVision, uploadImages } from '../lib/api'
import type { ImageResult } from '../types/vehicle'

export default function VisionModule({ inspectionId, results, onDone }: {
  inspectionId: string | null; results: ImageResult[]; onDone: () => void
}) {
  const [files, setFiles] = useState<File[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [total, setTotal] = useState<number | null>(null)

  async function run() {
    if (!inspectionId || !files.length) return
    setBusy(true); setError(null)
    try {
      await uploadImages(inspectionId, files)
      setTotal((await runVision(inspectionId)).total_damages)
      setFiles([])
      onDone()
    } catch (e) { setError(errMsg(e)) } finally { setBusy(false) }
  }

  return (
    <ModuleCard id="vision" title="1 · Vision — damage detection"
      subtitle="Upload car photos (front, rear, sides, close-ups). YOLOv8 finds dent, scratch, crack, glass, lamp and tire damage.">
      <div className="flex items-center gap-4 flex-wrap">
        <input type="file" accept=".jpg,.jpeg,.png" multiple disabled={busy}
          onChange={(e) => setFiles(Array.from(e.target.files ?? []))} className="text-sm text-gray-300" />
        <button className={buttonCls} disabled={busy || !files.length || !inspectionId} onClick={run}>
          {busy ? 'Detecting damage…' : 'Detect damage'}
        </button>
      </div>
      <p className="text-xs text-gray-500">JPG / PNG, up to 10 MB each. Running again adds the new photos to the earlier ones.</p>
      <ErrorBox message={error} />
      {total !== null && !error && <p className="text-green-300 text-sm">✓ Analysis complete — {total} damage(s) found in this run.</p>}
      {inspectionId && <DamageViewer inspectionId={inspectionId} results={results} />}
    </ModuleCard>
  )
}
