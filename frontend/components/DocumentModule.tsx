'use client'
// Documents module: RC / insurance / service bills in -> Document AI (OCR) -> structured fields out.
// Also lets the user check values they typed against the uploaded documents ("Verify entered details").
import { useRef, useState } from 'react'
import ModuleCard, { ErrorBox, buttonCls, errMsg } from './ModuleCard'
import {
  runDocumentExtraction, uploadDocuments, verifyDocumentFields, type VerifyResult,
} from '../lib/api'
import type { DocType } from '../types/vehicle'

const ACCEPT = '.pdf,.jpg,.jpeg,.png'
const inputCls = 'w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm focus:border-cyan-500 outline-none'

const RC_LABELS: Record<string, string> = {
  registration_number: 'Registration no.', owner: 'Owner', make: 'Make', model: 'Model', vin: 'VIN / chassis',
  manufacturing_year: 'Manufacturing year', registration_year: 'Registration year', fuel_type: 'Fuel',
  transmission: 'Transmission', engine_displacement_cc: 'Engine (cc)', power_bhp: 'Power (bhp)',
}

const VERIFY_FIELDS: Record<'rc' | 'insurance' | 'odometer', { key: string; label: string }[]> = {
  rc: [
    { key: 'registration_number', label: 'Registration number' }, { key: 'vin', label: 'VIN / chassis' },
    { key: 'make', label: 'Make' }, { key: 'model', label: 'Model' },
    { key: 'manufacturing_year', label: 'Manufacturing year' }, { key: 'registration_year', label: 'Registration year' },
    { key: 'fuel_type', label: 'Fuel type' }, { key: 'engine_displacement_cc', label: 'Engine (cc)' },
  ],
  insurance: [
    { key: 'policy_number', label: 'Policy number' }, { key: 'valid_from', label: 'Valid from' }, { key: 'valid_until', label: 'Valid until' },
  ],
  odometer: [{ key: 'odometer_reading_km', label: 'Odometer reading (km)' }],
}

const pct = (v?: number | null) => (v == null ? '—' : `${Math.round(v * 100)}%`)

function Picker({ label, hint, multiple, files, onChange, disabled }: {
  label: string; hint: string; multiple?: boolean; files: File[]; onChange: (f: File[]) => void; disabled: boolean
}) {
  return (
    <div className="rounded-xl border border-cyan-500/20 bg-gray-900/60 p-4">
      <p className="text-white font-semibold text-sm">{label}</p>
      <p className="text-gray-500 text-xs mb-2">{hint}</p>
      <input type="file" accept={ACCEPT} multiple={multiple} disabled={disabled}
        onChange={(e) => onChange(Array.from(e.target.files ?? []))} className="text-xs text-gray-300 w-full" />
      {files.length > 0 && <p className="text-cyan-400 text-xs mt-2 break-all">{files.map((f) => f.name).join(', ')}</p>}
    </div>
  )
}

function Row({ k, v, c }: { k: string; v: unknown; c?: number }) {
  const empty = v === null || v === undefined || v === ''
  return (
    <tr className="border-b border-gray-800">
      <td className="py-1.5 pr-4 text-gray-400">{k}</td>
      <td className={`py-1.5 pr-4 ${empty ? 'text-gray-600' : 'text-white font-medium'}`}>{empty ? 'not found' : String(v)}</td>
      <td className="py-1.5 text-gray-500 text-xs text-right">{c !== undefined && !empty ? pct(c) : ''}</td>
    </tr>
  )
}

function Results({ docs }: { docs: any }) {
  const rc = docs?.rc, ins = docs?.insurance, svc = docs?.service
  if (!docs) return <p className="text-gray-400 text-sm">No document results yet. Upload documents above and press “Extract information”.</p>
  return (
    <div className="space-y-5">
      {(docs.errors ?? []).map((e: any) => (
        <div key={e.file_id} className="p-3 rounded-lg border border-red-500/40 bg-red-500/10 text-red-300 text-sm">
          <b>{e.filename}</b>: {e.error}
        </div>
      ))}
      <div className="grid md:grid-cols-2 gap-5">
        {rc && (
          <div className="rounded-xl border border-cyan-500/20 bg-gray-900/60 p-4">
            <p className="font-semibold text-cyan-300 mb-2">Registration Certificate <span className="text-xs text-gray-500">· confidence {pct(rc.confidence)}</span></p>
            <table className="w-full text-sm"><tbody>
              {Object.entries(RC_LABELS).map(([k, label]) => <Row key={k} k={label} v={rc.fields?.[k]} c={rc.field_confidence?.[k]} />)}
            </tbody></table>
          </div>
        )}
        {ins && (
          <div className="rounded-xl border border-cyan-500/20 bg-gray-900/60 p-4">
            <p className="font-semibold text-cyan-300 mb-2">Insurance <span className="text-xs text-gray-500">· confidence {pct(ins.confidence)}</span></p>
            <table className="w-full text-sm"><tbody>
              <Row k="Policy number" v={ins.policy_number} /><Row k="Insurer" v={ins.insurer_name} />
              <Row k="Insured" v={ins.insured_name} /><Row k="Vehicle reg. no." v={ins.registration_number} />
              <Row k="Valid from" v={ins.valid_from} /><Row k="Valid until" v={ins.valid_until} />
              <Row k="Insured declared value" v={ins.idv != null ? `₹${ins.idv}` : null} />
            </tbody></table>
            <p className="text-sm text-gray-400 mt-3">Claims: {ins.claims?.length ? ins.claims.map((c: any) => `₹${c.amount}`).join(', ') : 'none found'}</p>
            {ins.raw_text && <details className="mt-2 text-xs text-gray-500"><summary className="cursor-pointer">Raw OCR text</summary><pre className="whitespace-pre-wrap mt-1">{ins.raw_text}</pre></details>}
          </div>
        )}
      </div>
      {svc && (
        <div className="rounded-xl border border-cyan-500/20 bg-gray-900/60 p-4 overflow-x-auto">
          <p className="font-semibold text-cyan-300 mb-2">Service history <span className="text-xs text-gray-500">· {svc.service_records.length} record(s) · confidence {pct(svc.confidence)}</span></p>
          {svc.service_records.length === 0 ? <p className="text-gray-500 text-sm">No service records recognised.</p> : (
            <table className="w-full text-sm text-gray-200">
              <thead><tr className="text-left text-gray-400 border-b border-gray-700"><th className="py-1.5">Date</th><th>Mileage (km)</th><th>Work done</th><th>Cost</th></tr></thead>
              <tbody>{svc.service_records.map((r: any) => (
                <tr key={r.service_id} className="border-b border-gray-800">
                  <td className="py-1.5">{r.date ?? '—'}</td><td>{r.mileage_km ?? '—'}</td>
                  <td>{r.work_done?.length ? r.work_done.join(', ') : '—'}</td><td>{r.cost != null ? `₹${r.cost}` : '—'}</td>
                </tr>))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  )
}

function VerifyBlock({ inspectionId, kind, title, files }: {
  inspectionId: string; kind: 'rc' | 'insurance' | 'odometer'; title: string; files: File[]
}) {
  const [values, setValues] = useState<Record<string, string>>({})
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<VerifyResult | null>(null)

  async function verify() {
    setError(null); setResult(null)
    const entered = Object.fromEntries(Object.entries(values).filter(([, v]) => v.trim()))
    if (!files.length) return setError(`Choose the ${title} file above first`)
    if (!Object.keys(entered).length) return setError('Enter at least one value to check')
    setBusy(true)
    try {
      const up = await uploadDocuments(inspectionId, files, kind as DocType)
      setResult(await verifyDocumentFields(inspectionId, entered, up.files.map((f) => f.file_id)))
    } catch (e) { setError(errMsg(e)) } finally { setBusy(false) }
  }

  return (
    <div className="rounded-xl border border-gray-700 bg-gray-900/60 p-4 space-y-3">
      <p className="font-semibold text-white text-sm">{title}</p>
      <div className="grid sm:grid-cols-2 gap-3">
        {VERIFY_FIELDS[kind].map((f) => (
          <label key={f.key} className="text-xs text-gray-400 block">
            {f.label}
            <input className={inputCls} value={values[f.key] ?? ''} onChange={(e) => setValues((v) => ({ ...v, [f.key]: e.target.value }))} />
          </label>
        ))}
      </div>
      <button className={buttonCls} disabled={busy} onClick={verify}>{busy ? 'Checking…' : 'Check against document'}</button>
      <ErrorBox message={error} />
      {result && (
        <div className="text-sm space-y-1">
          <p className={result.all_matched ? 'text-green-300' : 'text-yellow-300'}>{result.message}</p>
          {Object.entries(result.verification_results).map(([k, r]) => (
            <p key={k} className={r.found ? 'text-green-300' : 'text-red-300'}>{r.found ? '✓' : '✗'} {k}: {String(r.value)}</p>
          ))}
          {!!result.recognized_readings?.length && <p className="text-gray-400">Numbers read from image: {result.recognized_readings.join(', ')}</p>}
        </div>
      )}
    </div>
  )
}

export default function DocumentModule({ inspectionId, docs, onDone }: {
  inspectionId: string | null; docs: any; onDone: () => void
}) {
  const [rc, setRc] = useState<File[]>([])
  const [insurance, setInsurance] = useState<File[]>([])
  const [service, setService] = useState<File[]>([])
  const [odometer, setOdometer] = useState<File[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const uploaded = useRef<Record<string, string>>({}) // slot -> signature of the files already sent

  const sig = (fs: File[]) => fs.map((f) => `${f.name}:${f.size}:${f.lastModified}`).join('|')
  const any = rc.length + insurance.length + service.length > 0

  async function extract() {
    if (!inspectionId) return
    setBusy(true); setError(null)
    try {
      const slots: [DocType, File[]][] = [['rc', rc], ['insurance', insurance], ['service', service]]
      for (const [slot, fs] of slots) {
        if (fs.length && uploaded.current[slot] !== sig(fs)) {
          await uploadDocuments(inspectionId, fs, slot)
          uploaded.current[slot] = sig(fs)
        }
      }
      await runDocumentExtraction(inspectionId)
      onDone()
    } catch (e) { setError(errMsg(e)) } finally { setBusy(false) }
  }

  return (
    <ModuleCard id="documents" title="2 · Documents — information extraction"
      subtitle="Upload the RC, insurance policy and service bills. Document AI reads them (OCR) and returns structured vehicle data.">
      <div className="grid md:grid-cols-3 gap-4">
        <Picker label="RC (Registration Certificate)" hint="PDF / JPG / PNG" files={rc} onChange={setRc} disabled={busy} />
        <Picker label="Insurance policy" hint="PDF / JPG / PNG" files={insurance} onChange={setInsurance} disabled={busy} />
        <Picker label="Service bills" hint="One or more, PDF / JPG / PNG" multiple files={service} onChange={setService} disabled={busy} />
      </div>
      <button className={buttonCls} disabled={busy || !any || !inspectionId} onClick={extract}>
        {busy ? 'Reading documents…' : 'Extract information'}
      </button>
      <ErrorBox message={error} />
      <Results docs={docs} />

      <details className="rounded-xl border border-gray-700 p-4">
        <summary className="cursor-pointer text-gray-200 font-semibold text-sm">Verify details entered by the seller (optional)</summary>
        <p className="text-xs text-gray-500 my-3">Type what the seller claims and check that it really appears in the document. Uses the files chosen above.</p>
        {inspectionId && (
          <div className="space-y-4">
            <VerifyBlock inspectionId={inspectionId} kind="rc" title="RC" files={rc} />
            <VerifyBlock inspectionId={inspectionId} kind="insurance" title="Insurance" files={insurance} />
            <div className="rounded-xl border border-cyan-500/20 bg-gray-900/60 p-4">
              <p className="text-white font-semibold text-sm">Odometer photo</p>
              <p className="text-gray-500 text-xs mb-2">Photo of the dashboard odometer (JPG / PNG)</p>
              <input type="file" accept=".jpg,.jpeg,.png" onChange={(e) => setOdometer(Array.from(e.target.files ?? []))} className="text-xs text-gray-300" />
            </div>
            <VerifyBlock inspectionId={inspectionId} kind="odometer" title="Odometer reading" files={odometer} />
          </div>
        )}
      </details>
    </ModuleCard>
  )
}
