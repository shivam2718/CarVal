'use client'
// OBD-II scanner photo: upload -> OCR proposals -> USER confirms -> evidence stored in the inspection.
// OCR output is only a proposal. Nothing becomes a finding until the user presses "Confirm".
import { useCallback, useEffect, useState } from 'react'
import type { DiagnosticEvidence, EngineAssessment, ScanContext, ScannerStatus } from '../types/vehicle'
import {
  confirmDiagnostic, diagnosticPhotoUrl, extractDiagnostic, getDiagnostics, uploadDiagnosticPhotos,
} from '../lib/api'

const DTC_RE = /^[PBCU][0-3][0-9A-F]{3}$/
const STATUSES: ScannerStatus[] = ['unknown', 'stored', 'pending', 'permanent', 'current']
const CONTEXTS: ScanContext[] = ['unknown', 'freeze_frame', 'stored', 'pending', 'permanent', 'current', 'live']
const inputCls = 'bg-gray-800 border border-gray-700 rounded px-2 py-1 text-gray-100 text-sm'

const errMsg = (e: unknown) => (e instanceof Error ? e.message : 'Something went wrong')

interface CodeRow { code: string; status: ScannerStatus }
interface ReadingRow { label: string; value: string; unit: string }

function EvidenceCard({ inspectionId, ev, onChanged }: { inspectionId: string; ev: DiagnosticEvidence; onChanged: () => void }) {
  const [codes, setCodes] = useState<CodeRow[]>(() =>
    ev.extracted_codes.map((c) => ({ code: c.code, status: (c.scanner_status ?? 'unknown') as ScannerStatus })))
  const [readings, setReadings] = useState<ReadingRow[]>(() =>
    ev.extracted_readings.map((r) => ({ label: r.label, value: r.value, unit: r.unit ?? '' })))
  const [scanContext, setScanContext] = useState<ScanContext>(ev.scan_context)
  const [noCodes, setNoCodes] = useState(ev.no_codes_visible)
  const [notes, setNotes] = useState(ev.notes.join('\n'))
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const confirmed = ev.ocr_status === 'confirmed'
  const suggestions = ev.ocr_proposals?.uncertain_codes ?? []

  async function runOcr() {
    setBusy(true); setError(null)
    try { await extractDiagnostic(inspectionId, ev.evidence_id); onChanged() }
    catch (e) { setError(errMsg(e)) } finally { setBusy(false) }
  }

  async function confirm() {
    setError(null)
    const cleaned = codes.map((c) => ({ ...c, code: c.code.trim().toUpperCase() })).filter((c) => c.code)
    const bad = cleaned.find((c) => !DTC_RE.test(c.code))
    if (bad) { setError(`"${bad.code}" is not a valid code (example: P0100)`); return }
    setBusy(true)
    try {
      await confirmDiagnostic(inspectionId, ev.evidence_id, {
        codes: cleaned.map((c) => ({ code: c.code, scanner_status: c.status })),
        readings: readings
          .filter((r) => r.label.trim() && r.value.trim())
          .map((r) => ({ label: r.label.trim(), value: r.value.trim(), unit: r.unit.trim() || null, context: scanContext })),
        scan_context: scanContext,
        no_codes_visible: noCodes && cleaned.length === 0,
        notes: notes.split('\n').map((n) => n.trim()).filter(Boolean),
      })
      onChanged()
    } catch (e) { setError(errMsg(e)) } finally { setBusy(false) }
  }

  const badge = {
    uploaded: ['Not read yet', 'text-gray-300 border-gray-500/40'],
    needs_user_confirmation: ['Needs your confirmation', 'text-yellow-300 border-yellow-500/40'],
    ocr_failed: ['OCR failed - enter manually', 'text-red-300 border-red-500/40'],
    confirmed: ['Confirmed', 'text-green-300 border-green-500/40'],
  }[ev.ocr_status]

  return (
    <div className="rounded-xl border border-cyan-500/20 bg-gray-900/60 p-5">
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <p className="text-sm text-gray-300"><span className="font-mono text-cyan-400">{ev.evidence_id}</span> · {ev.uploaded_filename}</p>
        <span className={`text-xs px-3 py-1 rounded-full border ${badge[1]}`}>{badge[0]}</span>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={diagnosticPhotoUrl(inspectionId, ev.evidence_id)} alt="Scanner screen" className="w-full max-h-96 object-contain rounded-lg bg-black" />

        <div className="space-y-4 text-sm text-gray-200">
          {(ev.ocr_status === 'uploaded' || ev.ocr_status === 'ocr_failed') && (
            <div>
              {ev.ocr_error && <p className="text-red-300 mb-2">{ev.ocr_error}</p>}
              <button onClick={runOcr} disabled={busy} className="px-3 py-1 rounded bg-cyan-700 hover:bg-cyan-600 text-white disabled:opacity-40">
                {busy ? 'Reading…' : 'Read photo (OCR)'}
              </button>
              <p className="text-gray-400 text-xs mt-1">You can also type the code(s) below without OCR.</p>
            </div>
          )}

          {ev.ocr_status === 'needs_user_confirmation' && (
            <p className="text-yellow-200 text-xs">OCR can misread characters. Compare with the photo and fix anything wrong before confirming.</p>
          )}
          {(ev.ocr_proposals?.status_keywords_seen?.length ?? 0) > 0 && (
            <p className="text-xs text-gray-400">Words seen on screen: {ev.ocr_proposals!.status_keywords_seen.join(', ')}</p>
          )}

          {suggestions.map((s) => (
            <div key={s.raw_text} className="text-xs text-yellow-200 flex items-center gap-2">
              {s.reason ?? `OCR read “${s.raw_text}”`} - did you mean {s.suggested_code}?
              <button className="px-2 py-0.5 rounded bg-gray-700 hover:bg-gray-600"
                onClick={() => setCodes((cs) => (cs.some((c) => c.code === s.suggested_code) ? cs : [...cs, { code: s.suggested_code, status: 'unknown' }]))}>
                Use {s.suggested_code}
              </button>
            </div>
          ))}

          <div>
            <p className="font-semibold text-white mb-2">Fault codes</p>
            {codes.length === 0 && <p className="text-gray-400 text-xs mb-2">No code entered.</p>}
            {codes.map((c, i) => (
              <div key={i} className="flex items-center gap-2 mb-2">
                <input className={`${inputCls} w-24 font-mono uppercase`} maxLength={5} value={c.code} placeholder="P0100"
                  onChange={(e) => setCodes((cs) => cs.map((x, j) => (j === i ? { ...x, code: e.target.value.toUpperCase() } : x)))} />
                <select className={inputCls} value={c.status}
                  onChange={(e) => setCodes((cs) => cs.map((x, j) => (j === i ? { ...x, status: e.target.value as ScannerStatus } : x)))}>
                  {STATUSES.map((s) => <option key={s} value={s}>{s === 'unknown' ? 'status: unknown' : s}</option>)}
                </select>
                <button className="text-red-300 text-xs" onClick={() => setCodes((cs) => cs.filter((_, j) => j !== i))}>remove</button>
              </div>
            ))}
            <button className="text-cyan-300 text-xs" onClick={() => setCodes((cs) => [...cs, { code: '', status: 'unknown' }])}>+ add code</button>
          </div>

          <label className="flex items-center gap-2 text-xs text-gray-300">
            <input type="checkbox" checked={noCodes} disabled={codes.some((c) => c.code.trim())} onChange={(e) => setNoCodes(e.target.checked)} />
            No readable code on this screen (this does NOT mean the car is healthy)
          </label>

          <div>
            <label className="text-xs text-gray-400 mr-2">Screen type</label>
            <select className={inputCls} value={scanContext} onChange={(e) => setScanContext(e.target.value as ScanContext)}>
              {CONTEXTS.map((c) => <option key={c} value={c}>{c.replace('_', ' ')}</option>)}
            </select>
            {scanContext === 'freeze_frame' && <p className="text-xs text-gray-400 mt-1">Freeze-frame values are a snapshot from when the fault was logged, not live data.</p>}
          </div>

          {readings.length > 0 && (
            <div>
              <p className="font-semibold text-white mb-2">Readings shown (as displayed)</p>
              {readings.map((r, i) => (
                <div key={i} className="flex items-center gap-2 mb-2">
                  <input className={`${inputCls} w-28`} value={r.label} onChange={(e) => setReadings((rs) => rs.map((x, j) => (j === i ? { ...x, label: e.target.value } : x)))} />
                  <input className={`${inputCls} w-20`} value={r.value} onChange={(e) => setReadings((rs) => rs.map((x, j) => (j === i ? { ...x, value: e.target.value } : x)))} />
                  <input className={`${inputCls} w-14`} value={r.unit} placeholder="unit" onChange={(e) => setReadings((rs) => rs.map((x, j) => (j === i ? { ...x, unit: e.target.value } : x)))} />
                  <button className="text-red-300 text-xs" onClick={() => setReadings((rs) => rs.filter((_, j) => j !== i))}>remove</button>
                </div>
              ))}
            </div>
          )}

          <textarea className={`${inputCls} w-full`} rows={2} placeholder="Notes (optional)" value={notes} onChange={(e) => setNotes(e.target.value)} />

          {error && <p className="text-red-300 text-xs">{error}</p>}
          <button onClick={confirm} disabled={busy}
            className="px-4 py-2 rounded-lg font-semibold text-white bg-gradient-to-r from-cyan-600 to-blue-600 disabled:opacity-40">
            {busy ? 'Saving…' : confirmed ? 'Update confirmed evidence' : 'Confirm these values'}
          </button>
        </div>
      </div>

      {ev.ocr_text && (
        <details className="mt-4 text-xs text-gray-400">
          <summary className="cursor-pointer">Raw OCR text</summary>
          <pre className="mt-2 whitespace-pre-wrap">{ev.ocr_text}</pre>
        </details>
      )}
    </div>
  )
}

export default function DiagnosticPanel({ inspectionId, onChanged }: { inspectionId: string; onChanged?: () => void }) {
  const [assessment, setAssessment] = useState<EngineAssessment | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    try { setAssessment(await getDiagnostics(inspectionId)); onChanged?.() } catch (e) { setError(errMsg(e)) }
  }, [inspectionId, onChanged])

  useEffect(() => { refresh() }, [refresh])

  async function handleUpload(files: FileList | null) {
    if (!files || files.length === 0) return
    setBusy(true); setError(null)
    try {
      const up = await uploadDiagnosticPhotos(inspectionId, Array.from(files))
      for (const ev of up.evidence) await extractDiagnostic(inspectionId, ev.evidence_id)
      await refresh()
    } catch (e) { setError(errMsg(e)) } finally { setBusy(false) }
  }

  const flags = assessment?.risk_flags ?? []
  return (
    <section className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <p className="text-gray-400 text-sm">No OBD adapter needed: add a photo of the scanner screen, then check the codes it read.</p>
        </div>
        <label className="px-4 py-2 rounded-lg bg-gray-800 border border-cyan-500/30 text-cyan-300 text-sm cursor-pointer hover:bg-gray-700">
          {busy ? 'Uploading…' : '+ Add scanner photo'}
          <input type="file" accept=".jpg,.jpeg,.png" multiple className="hidden" disabled={busy}
            onChange={(e) => { handleUpload(e.target.files); e.target.value = '' }} />
        </label>
      </div>

      {error && <div className="p-3 rounded-lg border border-red-500/40 bg-red-500/10 text-red-300 text-sm">{error}</div>}

      {assessment?.status === 'not_provided' && (
        <div className="p-4 rounded-lg border border-gray-600/40 bg-gray-800/40 text-gray-300 text-sm">
          No scanner data provided. Engine and electronic-system condition is <b>unknown</b> (not “healthy”).
        </div>
      )}

      {assessment?.diagnostic_evidence.map((ev) => (
        <EvidenceCard key={`${ev.evidence_id}-${ev.ocr_status}`} inspectionId={inspectionId} ev={ev} onChanged={refresh} />
      ))}

      {flags.some((f) => f.flag === 'diagnostic_code_present') && (
        <div className="rounded-xl border border-orange-400/30 bg-orange-500/10 p-5 space-y-4">
          <p className="text-white font-semibold">Confirmed codes (risk level: {assessment?.risk_level})</p>
          {flags.filter((f) => f.flag === 'diagnostic_code_present').map((f, i) => (
            <div key={`${f.code}-${i}`} className="text-sm text-gray-200">
              <p><span className="font-mono text-orange-300">{f.code}</span> - {f.description ?? 'Not in the local catalogue (look it up in a trusted reference)'}</p>
              <p className="text-xs text-gray-400">Screen: {f.scan_context?.replace('_', ' ')} · status: {f.scanner_status} · evidence: {f.evidence.join(', ')}</p>
              {(f.possible_causes?.length ?? 0) > 0 && <p className="text-xs text-gray-300 mt-1">Possible causes (not a diagnosis): {f.possible_causes!.join('; ')}</p>}
            </div>
          ))}
          {(assessment?.recommended_actions.length ?? 0) > 0 && (
            <ul className="list-disc pl-5 text-sm text-gray-200">{assessment!.recommended_actions.map((a) => <li key={a}>{a}</li>)}</ul>
          )}
        </div>
      )}

      {assessment && assessment.status !== 'not_provided' && (
        <ul className="list-disc pl-5 text-xs text-yellow-200/80">{assessment.limitations.map((l) => <li key={l}>{l}</li>)}</ul>
      )}
    </section>
  )
}