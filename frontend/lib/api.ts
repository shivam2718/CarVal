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

export function uploadImages(id: string, files: File[]) {
  const fd = new FormData()
  files.forEach((f) => fd.append('files', f))
  return request(`/inspection/${id}/images`, { method: 'POST', body: fd })
}

export function uploadDocuments(id: string, files: File[], docType: DocType) {
  const fd = new FormData()
  files.forEach((f) => fd.append('files', f))
  fd.append('doc_type', docType)
  return request(`/inspection/${id}/documents`, { method: 'POST', body: fd })
}

export const runVision = (id: string) =>
  request<{ total_damages: number }>(`/inspection/${id}/vision`, { method: 'POST' })

export const runDocumentExtraction = (id: string) =>
  request(`/inspection/${id}/documents/extract`, { method: 'POST' })

export const getInspection = (id: string) => request<InspectionResult>(`/inspection/${id}`)

export const annotatedImageUrl = (id: string, imageId: string) =>
  `${API_URL}/inspection/${id}/images/${imageId}/annotated`
export const originalImageUrl = (id: string, imageId: string) =>
  `${API_URL}/inspection/${id}/images/${imageId}`

// ---- OBD-II diagnostic photo feature ----
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
  return request<{ evidence: DiagnosticEvidence[] }>(`/inspection/${id}/diagnostics/photos`, { method: 'POST', body: fd })
}

export const extractDiagnostic = (id: string, evidenceId: string) =>
  request<{ evidence: DiagnosticEvidence; manual_entry_required: boolean }>(
    `/inspection/${id}/diagnostics/extract/${evidenceId}`, { method: 'POST' })

export const confirmDiagnostic = (id: string, evidenceId: string, body: ConfirmDiagnosticBody) =>
  request<{ evidence: DiagnosticEvidence; engine_assessment: EngineAssessment }>(
    `/inspection/${id}/diagnostics/confirm/${evidenceId}`,
    { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })

export const getDiagnostics = (id: string) => request<EngineAssessment>(`/inspection/${id}/diagnostics`)

export const diagnosticPhotoUrl = (id: string, evidenceId: string) =>
  `${API_URL}/inspection/${id}/diagnostics/photos/${evidenceId}`