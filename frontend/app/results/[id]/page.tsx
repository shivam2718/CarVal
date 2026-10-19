/**
 * Inspection Results Page
 * Member 3 - Frontend
 * Display combined Vision + Document AI results
 */

'use client'

import { useEffect, useState } from 'react'
import DamageViewer from '../../../components/DamageViewer'

interface InspectionResult {
  vehicle_id: string
  vision: any
  documents: any
  pipeline_status: any
  [key: string]: any
}

export default function ResultsPage({ params }: { params: { id: string } }) {
  const [results, setResults] = useState<InspectionResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const apiUrl = process.env.NEXT_PUBLIC_API_URL

  useEffect(() => {
    const fetchResults = async () => {
      try {
        const response = await fetch(`${apiUrl}/inspection/${params.id}`)
        if (!response.ok) throw new Error('Failed to fetch results')
        const data = await response.json()
        setResults(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred')
      } finally {
        setLoading(false)
      }
    }

    fetchResults()
  }, [params.id, apiUrl])

  if (loading) {
    return (
      <main className="min-h-screen bg-gray-50 py-12">
        <div className="container mx-auto px-4 text-center">
          <p className="text-xl text-gray-600">Loading results...</p>
        </div>
      </main>
    )
  }

  if (error) {
    return (
      <main className="min-h-screen bg-gray-50 py-12">
        <div className="container mx-auto px-4">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
            Error: {error}
          </div>
        </div>
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-gray-50 py-12">
      <div className="container mx-auto px-4 max-w-4xl">
        <h1 className="text-4xl font-bold text-gray-900 mb-8">
          Inspection Results
        </h1>

        {/* Vehicle Summary */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            Vehicle Summary
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div>
              <p className="text-gray-600 text-sm">Vehicle ID</p>
              <p className="font-bold text-gray-900">{results?.vehicle_id}</p>
            </div>
            <div>
              <p className="text-gray-600 text-sm">Inspection Status</p>
              <p className="font-bold text-indigo-600">In Progress</p>
            </div>
          </div>
        </div>

        {/* Vision Results */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            📸 Damage Detection Results
          </h2>
          {results?.pipeline_status?.vision_completed ? (
            <div className="text-green-600">
              ✓ Vision analysis completed
            </div>
          ) : (
            <div className="text-gray-600">
              Waiting for vision service results...
            </div>
          )}
          <div className="mt-4">
            <DamageViewer
              inspectionId={params.id}
              results={results?.vision?.damage_detection?.image_results ?? []}
            />
          </div>
        </div>

        {/* Document Results */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            📄 Document Extraction Results
          </h2>
          {results?.pipeline_status?.document_ai_completed ? (
            <div className="text-green-600">
              ✓ Document extraction completed
            </div>
          ) : (
            <div className="text-gray-600">
              Waiting for document AI results...
            </div>
          )}
          <pre className="bg-gray-100 p-4 rounded mt-4 text-sm overflow-auto max-h-64">
            {JSON.stringify(results?.documents, null, 2)}
          </pre>
        </div>

        {/* Raw JSON */}
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            Complete Vehicle JSON
          </h2>
          <pre className="bg-gray-100 p-4 rounded text-sm overflow-auto max-h-96">
            {JSON.stringify(results, null, 2)}
          </pre>
        </div>

        {/* Navigation */}
        <div className="mt-8">
          <a
            href="/inspection"
            className="inline-block bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700"
          >
            ← New Inspection
          </a>
        </div>
      </div>
    </main>
  )
}
