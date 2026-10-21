import ModuleCard from './ModuleCard'
import type { InspectionResult } from '../types/vehicle'

const LABELS: [string, string][] = [
  ['registration_number', 'Registration no.'], ['owner', 'Owner'], ['make', 'Make'], ['model', 'Model'], ['vin', 'VIN / chassis'],
  ['manufacturing_year', 'Manufactured'], ['registration_year', 'Registered'], ['fuel_type', 'Fuel'], ['engine_cc', 'Engine (cc)'],
]

// Combined result: the common Vehicle JSON from every module (vehicle_schema_v1.json).
export default function VehicleSummary({ data }: { data: InspectionResult | null }) {
  const v: any = { ...(data?.vehicle ?? {}), engine_cc: data?.vehicle?.engine?.displacement_cc }
  const ps = data?.pipeline_status ?? {}
  const damages = (data?.vision?.damage_detection.image_results ?? []).reduce((n, r) => n + r.damages.length, 0)
  const ins = data?.documents?.insurance
  const svc = data?.documents?.service?.service_records ?? []
  const chip = (ok: boolean, text: string) => (
    <span className={`text-xs px-3 py-1 rounded-full border ${ok ? 'border-green-500/40 text-green-300' : 'border-gray-600 text-gray-400'}`}>{ok ? '✓' : '○'} {text}</span>
  )

  return (
    <ModuleCard id="summary" title="Vehicle summary" subtitle="Everything the modules found, combined into one vehicle record.">
      <div className="flex gap-2 flex-wrap">
        {chip(!!ps.vision_completed, 'Vision')}
        {chip(!!ps.document_ai_completed, 'Documents')}
        {chip(!!ps.diagnostics_confirmed, 'OBD-II confirmed')}
        {chip(false, 'Valuation (Review 3)')}
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {LABELS.map(([k, label]) => (
          <div key={k}>
            <p className="text-xs text-gray-500">{label}</p>
            <p className={v[k] ? 'text-white font-medium' : 'text-gray-600'}>{v[k] ?? '—'}</p>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
        <div><p className="text-xs text-gray-500">Damages detected</p><p className="text-white font-medium">{data?.vision ? damages : '—'}</p></div>
        <div><p className="text-xs text-gray-500">Insurance valid until</p><p className="text-white font-medium">{ins?.valid_until ?? '—'}</p></div>
        <div><p className="text-xs text-gray-500">Service records</p><p className="text-white font-medium">{data?.documents?.service ? svc.length : '—'}</p></div>
        <div><p className="text-xs text-gray-500">Latest odometer in bills</p><p className="text-white font-medium">{svc.length ? `${Math.max(...svc.map((r: any) => r.mileage_km ?? 0)).toLocaleString()} km` : '—'}</p></div>
        <div><p className="text-xs text-gray-500">Insured declared value</p><p className="text-white font-medium">{ins?.idv != null ? `₹${ins.idv.toLocaleString()}` : '—'}</p></div>
        <div><p className="text-xs text-gray-500">Engine risk (OBD-II)</p><p className="text-white font-medium">{data?.engine_assessment?.risk_level ?? '—'}</p></div>
      </div>
      <details className="text-xs text-gray-400">
        <summary className="cursor-pointer">Full vehicle JSON</summary>
        <pre className="mt-2 max-h-96 overflow-auto bg-black/60 p-3 rounded">{JSON.stringify(data, null, 2)}</pre>
      </details>
    </ModuleCard>
  )
}
