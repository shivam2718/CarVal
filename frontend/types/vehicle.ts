// Mirrors schemas/vehicle_schema_v1.json (only the parts used in Review 2).
// Add new fields as optional so older responses keep working.

export interface BBox { x1: number; y1: number; x2: number; y2: number }

export interface Damage {
  damage_id: string
  type: string            // dent | scratch | crack | glass | lamp | tire
  confidence: number
  bbox: BBox
  severity: string | null
  affected_part: string | null
  evidence: string[]      // image IDs
}

export interface ImageResult { image_id: string; damages: Damage[] }

export interface VisionData {
  damage_detection: { model: string | null; image_results: ImageResult[] }
  odometer: { detected: boolean; value_km: number | null; confidence: number | null; image_id: string | null; evidence: string[] }
}

export interface VehicleSummary {
  registration_number?: string | null
  vin?: string | null
  model?: string | null
  manufacturing_year?: number | null
  registration_year?: number | null
  fuel_type?: string | null
  transmission?: string | null
  owner?: string | null
  engine?: { displacement_cc?: number | null; power_bhp?: number | null }
}

export interface InputFile { file_id: string; filename: string; size?: number; content_type?: string; doc_type?: string }

export interface InspectionResult {
  schema_version: string
  vehicle_id: string
  vehicle: VehicleSummary
  input_files: { images: InputFile[]; documents: InputFile[] }
  vision: VisionData | null
  documents: any | null      // rc / insurance / service / service_history
  pipeline_status: Record<string, boolean>
}

export type DocType = 'rc' | 'insurance' | 'service'