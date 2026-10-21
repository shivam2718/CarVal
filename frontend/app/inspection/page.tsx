'use client'
// One page for the whole Review 2 flow: every module's input and its result live here.
// Vision / Documents / OBD-II work independently; Valuation is a stub; the summary combines them.
import { useCallback, useEffect, useState } from 'react'
import VisionModule from '../../components/VisionModule'
import DocumentModule from '../../components/DocumentModule'
import DiagnosticPanel from '../../components/DiagnosticPanel'
import ValuationModule from '../../components/ValuationModule'
import VehicleSummary from '../../components/VehicleSummary'
import ModuleCard, { ErrorBox, errMsg } from '../../components/ModuleCard'
import { createInspection, getInspection } from '../../lib/api'
import type { InspectionResult } from '../../types/vehicle'

const NAV = [['vision', 'Vision'], ['documents', 'Documents'], ['obd', 'OBD-II'], ['valuation', 'Valuation'], ['summary', 'Summary']]

export default function InspectionPage() {
  const [id, setId] = useState<string | null>(null)
  const [data, setData] = useState<InspectionResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [session, setSession] = useState(0) // bumping this remounts the modules for a fresh inspection

  useEffect(() => {
    let cancelled = false
    setId(null); setData(null); setError(null)
    createInspection()
      .then((r) => { if (!cancelled) setId(r.inspection_id) })
      .catch((e) => { if (!cancelled) setError(`Could not reach the backend: ${errMsg(e)}`) })
    return () => { cancelled = true }
  }, [session])

  const refresh = useCallback(async () => {
    if (!id) return
    try { setData(await getInspection(id)) } catch (e) { setError(errMsg(e)) }
  }, [id])

  useEffect(() => { refresh() }, [refresh])

  return (
    <div className="min-h-screen bg-black">
      <header className="sticky top-0 z-20 border-b border-cyan-500/20 backdrop-blur-md bg-black/70">
        <div className="container mx-auto px-6 py-4 max-w-5xl flex items-center justify-between gap-4 flex-wrap">
          <div>
            <a href="/" className="text-xs text-cyan-400 hover:underline">← CarVal home</a>
            <h1 className="text-2xl font-bold text-white">Vehicle Inspection</h1>
            <p className="text-xs font-mono text-gray-500">{id ? `Inspection ${id}` : 'Starting inspection…'}</p>
          </div>
          <nav className="flex gap-2 flex-wrap text-sm">
            {NAV.map(([anchor, label]) => (
              <a key={anchor} href={`#${anchor}`} className="px-3 py-1 rounded-full border border-cyan-500/30 text-cyan-300 hover:bg-cyan-500/10">{label}</a>
            ))}
            <button onClick={() => setSession((s) => s + 1)} className="px-3 py-1 rounded-full border border-gray-600 text-gray-300 hover:bg-gray-800">
              New inspection
            </button>
          </nav>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8 max-w-5xl space-y-8" key={session}>
        <ErrorBox message={error} />
        <VisionModule inspectionId={id} results={data?.vision?.damage_detection.image_results ?? []} onDone={refresh} />
        <DocumentModule inspectionId={id} docs={data?.documents ?? null} onDone={refresh} />
        <ModuleCard id="obd" title="3 · OBD-II — engine diagnostics"
          subtitle="Photograph a scanner screen that already shows fault codes. CarVal reads it; you confirm it.">
          {id && <DiagnosticPanel inspectionId={id} onChanged={refresh} />}
        </ModuleCard>
        <ValuationModule status={data?.valuation?.status} />
        <VehicleSummary data={data} />
      </main>
    </div>
  )
}
