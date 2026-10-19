/**
 * Inspection Results Page
 * Member 3 - Frontend
 * User-friendly results display with modern design
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
  const [activeTab, setActiveTab] = useState('overview')

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
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-cyan-400 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-xl text-cyan-300">Loading results...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center p-6">
        <div className="bg-red-500/20 backdrop-blur-sm rounded-2xl p-8 border border-red-400/30 max-w-md">
          <div className="text-red-400 text-4xl mb-4 text-center">⚠️</div>
          <p className="text-red-300 text-center text-lg font-semibold">Error: {error}</p>
        </div>
      </div>
    )
  }

  const rcData = results?.documents?.rc?.fields?.extracted_fields || {}
  const rcConfidence = results?.documents?.rc?.fields?.field_confidence || {}

  return (
    <div className="min-h-screen bg-black">
      {/* Header */}
      <div className="border-b border-cyan-500/20 backdrop-blur-md bg-black/20">
        <div className="container mx-auto px-6 py-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2">Inspection Results</h1>
              <p className="text-cyan-400 font-mono text-sm">ID: {results?.vehicle_id}</p>
            </div>
            <a
              href="/inspection"
              className="px-6 py-3 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white rounded-lg font-semibold transition-all duration-300"
            >
              ← New Inspection
            </a>
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
      </div>

      <div className="container mx-auto px-6 py-12 max-w-6xl">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <h2 className="text-3xl font-bold text-white mb-8">📊 Inspection Overview</h2>

            {/* Status Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className={`p-6 rounded-xl border ${results?.pipeline_status?.documents_processed ? 'border-green-400/30 bg-green-500/10' : 'border-gray-500/30 bg-gray-500/10'}`}>
                <div className="text-3xl mb-2">{results?.pipeline_status?.documents_processed ? '✅' : '⏳'}</div>
                <p className="text-gray-300 font-semibold">Documents</p>
                <p className={`text-sm ${results?.pipeline_status?.documents_processed ? 'text-green-300' : 'text-gray-400'}`}>
                  {results?.pipeline_status?.documents_processed ? 'Uploaded' : 'Pending'}
                </p>
              </div>

              <div className={`p-6 rounded-xl border ${results?.pipeline_status?.document_ai_completed ? 'border-green-400/30 bg-green-500/10' : 'border-gray-500/30 bg-gray-500/10'}`}>
                <div className="text-3xl mb-2">{results?.pipeline_status?.document_ai_completed ? '✅' : '⏳'}</div>
                <p className="text-gray-300 font-semibold">AI Analysis</p>
                <p className={`text-sm ${results?.pipeline_status?.document_ai_completed ? 'text-green-300' : 'text-gray-400'}`}>
                  {results?.pipeline_status?.document_ai_completed ? 'Completed' : 'Pending'}
                </p>
              </div>

              <div className={`p-6 rounded-xl border ${results?.pipeline_status?.vision_completed ? 'border-green-400/30 bg-green-500/10' : 'border-gray-500/30 bg-gray-500/10'}`}>
                <div className="text-3xl mb-2">{results?.pipeline_status?.vision_completed ? '✅' : '⏳'}</div>
                <p className="text-gray-300 font-semibold">Vision</p>
                <p className={`text-sm ${results?.pipeline_status?.vision_completed ? 'text-green-300' : 'text-gray-400'}`}>
                  {results?.pipeline_status?.vision_completed ? 'Completed' : 'Coming Soon'}
                </p>
              </div>

              <div className={`p-6 rounded-xl border ${results?.pipeline_status?.llm_completed ? 'border-green-400/30 bg-green-500/10' : 'border-gray-500/30 bg-gray-500/10'}`}>
                <div className="text-3xl mb-2">{results?.pipeline_status?.llm_completed ? '✅' : '⏳'}</div>
                <p className="text-gray-300 font-semibold">LLM</p>
                <p className={`text-sm ${results?.pipeline_status?.llm_completed ? 'text-green-300' : 'text-gray-400'}`}>
                  {results?.pipeline_status?.llm_completed ? 'Completed' : 'Pending'}
                </p>
              </div>
            </div>

            {/* Quick Summary */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="rounded-xl border border-cyan-500/20 bg-gradient-to-br from-cyan-500/10 to-blue-500/10 p-8">
                <h3 className="text-2xl font-bold text-cyan-300 mb-6">📋 Registration Certificate</h3>
                {rcData?.registration_number ? (
                  <div className="space-y-4">
                    <div className="flex justify-between items-center pb-3 border-b border-cyan-500/10">
                      <span className="text-gray-300">Registration Number</span>
                      <span className="font-bold text-cyan-300">{rcData.registration_number}</span>
                    </div>
                    {rcData.model && (
                      <div className="flex justify-between items-center pb-3 border-b border-cyan-500/10">
                        <span className="text-gray-300">Vehicle Model</span>
                        <span className="font-bold text-white">{rcData.model}</span>
                      </div>
                    )}
                    {rcData.manufacturing_year && (
                      <div className="flex justify-between items-center pb-3 border-b border-cyan-500/10">
                        <span className="text-gray-300">Manufacturing Year</span>
                        <span className="font-bold text-white">{rcData.manufacturing_year}</span>
                      </div>
                    )}
                    {rcData.fuel_type && (
                      <div className="flex justify-between items-center pb-3 border-b border-cyan-500/10">
                        <span className="text-gray-300">Fuel Type</span>
                        <span className="font-bold text-white">{rcData.fuel_type}</span>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-gray-400">No RC data extracted</p>
                )}
              </div>

              <div className="rounded-xl border border-purple-500/20 bg-gradient-to-br from-purple-500/10 to-pink-500/10 p-8">
                <h3 className="text-2xl font-bold text-purple-300 mb-6">📊 Extraction Quality</h3>
                {results?.documents?.rc?.fields?.overall_confidence ? (
                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between mb-2">
                        <span className="text-gray-300">Overall Confidence</span>
                        <span className="font-bold text-purple-300">
                          {(results.documents.rc.fields.overall_confidence * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="w-full bg-gray-700 rounded-full h-3 overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-500"
                          style={{ width: `${(results.documents.rc.fields.overall_confidence * 100)}%` }}
                        ></div>
                      </div>
                    </div>
                    <p className="text-sm text-gray-400 mt-4">
                      {results.documents.rc.fields.overall_confidence >= 0.8
                        ? '✅ High Quality - Data is reliable'
                        : results.documents.rc.fields.overall_confidence >= 0.6
                        ? '⚠️ Medium Quality - Some fields may need review'
                        : '❌ Low Quality - Consider re-uploading'}
                    </p>
                  </div>
                ) : (
                  <p className="text-gray-400">No confidence data available</p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Registration Tab */}
        {activeTab === 'registration' && (
          <div className="rounded-xl border border-cyan-500/20 bg-gradient-to-br from-cyan-500/10 to-blue-500/10 p-8">
            <h2 className="text-3xl font-bold text-cyan-300 mb-8">🚗 Registration Certificate Details</h2>
            {rcData?.registration_number ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {Object.entries(rcData).map(([key, value]) => (
                  value && (
                    <div key={key} className="pb-4 border-b border-cyan-500/10">
                      <p className="text-gray-400 text-sm mb-2 uppercase tracking-wider">
                        {key.replace(/_/g, ' ')}
                      </p>
                      <p className="text-white text-lg font-semibold">{String(value)}</p>
                      {rcConfidence[key] && rcConfidence[key] > 0 && (
                        <div className="flex items-center gap-2 mt-2">
                          <div className="flex-1 bg-gray-700 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full ${
                                rcConfidence[key] >= 0.8
                                  ? 'bg-green-500'
                                  : rcConfidence[key] >= 0.6
                                  ? 'bg-yellow-500'
                                  : 'bg-red-500'
                              }`}
                              style={{ width: `${rcConfidence[key] * 100}%` }}
                            ></div>
                          </div>
                          <span className="text-xs text-gray-400">
                            {(rcConfidence[key] * 100).toFixed(0)}%
                          </span>
                        </div>
                      )}
                    </div>
                  )
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">📋</div>
                <p className="text-gray-400 text-lg">No registration data extracted</p>
                <p className="text-gray-500 text-sm mt-2">Upload an RC certificate and run extraction</p>
              </div>
            )}
          </div>
        )}

        {/* Insurance Tab */}
        {activeTab === 'insurance' && (
          <div className="rounded-xl border border-green-500/20 bg-gradient-to-br from-green-500/10 to-emerald-500/10 p-8">
            <h2 className="text-3xl font-bold text-green-300 mb-8">🛡️ Insurance Policy Details</h2>
            {results?.documents?.insurance ? (
              <div className="space-y-4">
                <pre className="bg-black/50 p-6 rounded-lg text-green-300 text-sm overflow-auto">
                  {JSON.stringify(results.documents.insurance, null, 2)}
                </pre>
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">🛡️</div>
                <p className="text-gray-400 text-lg">No insurance data extracted</p>
                <p className="text-gray-500 text-sm mt-2">Upload an insurance policy and run extraction</p>
              </div>
            )}
          </div>
        )}

        {/* Service Tab */}
        {activeTab === 'service' && (
          <div className="rounded-xl border border-purple-500/20 bg-gradient-to-br from-purple-500/10 to-pink-500/10 p-8">
            <h2 className="text-3xl font-bold text-purple-300 mb-8">🔧 Service Records</h2>
            {results?.documents?.service ? (
              <div className="space-y-4">
                <pre className="bg-black/50 p-6 rounded-lg text-purple-300 text-sm overflow-auto">
                  {JSON.stringify(results.documents.service, null, 2)}
                </pre>
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">🔧</div>
                <p className="text-gray-400 text-lg">No service records extracted</p>
                <p className="text-gray-500 text-sm mt-2">Upload service bills and run extraction</p>
              </div>
            )}
          </div>
        )}

        {/* Raw JSON Tab */}
        {activeTab === 'raw' && (
          <div className="rounded-xl border border-gray-500/20 bg-black/50 p-8">
            <h2 className="text-3xl font-bold text-white mb-8">🔧 Raw API Response</h2>
            <div className="bg-black rounded-lg p-6 overflow-auto max-h-96">
              <pre className="text-gray-300 text-xs font-mono">
                {JSON.stringify(results, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}