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
  engine_assessment?: EngineAssessment
  valuation?: { status: string; message?: string }
}

export type DocType = 'rc' | 'insurance' | 'service' | 'odometer'


// ---- OBD-II diagnostic photo feature (all optional so old responses still work) ----
export type ScannerStatus = 'unknown' | 'stored' | 'pending' | 'permanent' | 'current'
export type ScanContext = 'unknown' | 'freeze_frame' | 'stored' | 'pending' | 'permanent' | 'current' | 'live'

export interface DiagnosticCode {
  code: string
  description?: string | null
  in_catalogue?: boolean
  scanner_status?: ScannerStatus
  ocr_confidence?: number | null
  entry_source?: 'ocr_confirmed' | 'user_added'
  user_confirmed: boolean
}

export interface DiagnosticReading {
  label: string
  value: string
  unit?: string | null
  context?: ScanContext
  user_confirmed: boolean
}

export interface DiagnosticEvidence {
  evidence_id: string
  source_type: string
  source_image_id: string
  uploaded_filename: string
  ocr_status: 'uploaded' | 'needs_user_confirmation' | 'ocr_failed' | 'confirmed'
  ocr_error?: string | null
  ocr_text?: string | null
  ocr_proposals?: {
    codes: { code: string; ocr_confidence: number }[]
    uncertain_codes: { raw_text: string; suggested_code: string; reason?: string }[]
    readings: DiagnosticReading[]
    status_keywords_seen: string[]
  } | null
  extracted_codes: DiagnosticCode[]
  extracted_readings: DiagnosticReading[]
  scan_context: ScanContext
  no_codes_visible: boolean
  notes: string[]
}

export interface DiagnosticRiskFlag {
  flag: string
  code?: string
  description?: string | null
  in_catalogue?: boolean
  possible_causes?: string[]
  scanner_status?: string
  scan_context?: string
  note?: string
  evidence: string[]
}

export interface EngineAssessment {
  status: 'not_provided' | 'awaiting_confirmation' | 'partially_confirmed' | 'confirmed'
  diagnostic_evidence: DiagnosticEvidence[]
  risk_level: string
  risk_flags: DiagnosticRiskFlag[]
  recommended_actions: string[]
  limitations: string[]
}