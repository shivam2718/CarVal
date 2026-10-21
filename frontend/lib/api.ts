import type {
  DocType, InspectionResult, EngineAssessment, DiagnosticEvidence, ScanContext, ScannerStatus,
} from '../types/vehicle'

export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, init)
  if (!res.ok) {
    let detail = res.statusText
    try { detail = (await res.json()).detail ?? detail } catch {}
    throw new Error(`${res.status}: ${typeof detail === 'string' ? detail : JSON.stringify(detail)}`)
  }
  return res.json() as Promise<T>
}

export const createInspection = () =>
  request<{ inspection_id: string }>('/inspection', { method: 'POST' })

// ---- Vision module ----
export function uploadImages(id: string, files: File[]) {
  const fd = new FormData()
  files.forEach((f) => fd.append('files', f))
  return request(`/inspection/${id}/vision/images`, { method: 'POST', body: fd })
}

export const runVision = (id: string) =>
  request<{ total_damages: number }>(`/inspection/${id}/vision/analyze`, { method: 'POST' })

// ---- Documents module ----
export function uploadDocuments(id: string, files: File[], docType: DocType) {
  const fd = new FormData()
  files.forEach((f) => fd.append('files', f))
  fd.append('doc_type', docType)
  fd.append('replace', 'true') // re-uploading a slot replaces what was there
  return request<{ files: { file_id: string }[] }>(`/inspection/${id}/documents`, { method: 'POST', body: fd })
}

export const runDocumentExtraction = (id: string) =>
  request(`/inspection/${id}/documents/extract`, { method: 'POST' })

export interface VerifyResult {
  all_matched: boolean
  message: string
  verification_results: Record<string, { value: string; found: boolean; message: string }>
  recognized_readings?: string[]
  extraction_errors?: { filename: string; error: string }[]
}

export const verifyDocumentFields = (id: string, fields: Record<string, string>, documentIds: string[]) =>
  request<VerifyResult>(`/inspection/${id}/documents/verify`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ fields, document_ids: documentIds }),
  })

// ---- Valuation module (stub) ----
export const getValuation = (id: string) =>
  request<{ status: string; message: string }>(`/inspection/${id}/valuation`)

export const getInspection = (id: string) => request<InspectionResult>(`/inspection/${id}`)

export const annotatedImageUrl = (id: string, imageId: string) =>
  `${API_URL}/inspection/${id}/vision/images/${imageId}/annotated`
export const originalImageUrl = (id: string, imageId: string) =>
  `${API_URL}/inspection/${id}/vision/images/${imageId}`

// ---- OBD-II module ----
export interface ConfirmDiagnosticBody {
  codes: { code: string; scanner_status: ScannerStatus }[]
  readings: { label: string; value: string; unit?: string | null; context: ScanContext }[]
  scan_context: ScanContext
  no_codes_visible: boolean
  notes: string[]
}

export function uploadDiagnosticPhotos(id: string, files: File[]) {
  const fd = new FormData()
  files.forEach((f) => fd.append('files', f))
  return request<{ evidence: DiagnosticEvidence[] }>(`/inspection/${id}/obd/photos`, { method: 'POST', body: fd })
}

export const extractDiagnostic = (id: string, evidenceId: string) =>
  request<{ evidence: DiagnosticEvidence; manual_entry_required: boolean }>(
    `/inspection/${id}/obd/extract/${evidenceId}`, { method: 'POST' })

export const confirmDiagnostic = (id: string, evidenceId: string, body: ConfirmDiagnosticBody) =>
  request<{ evidence: DiagnosticEvidence; engine_assessment: EngineAssessment }>(
    `/inspection/${id}/obd/confirm/${evidenceId}`,
    { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })

export const getDiagnostics = (id: string) => request<EngineAssessment>(`/inspection/${id}/obd`)

export const diagnosticPhotoUrl = (id: string, evidenceId: string) =>
  `${API_URL}/inspection/${id}/obd/photos/${evidenceId}`