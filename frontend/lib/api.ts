import type { DocType, InspectionResult } from '../types/vehicle'

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