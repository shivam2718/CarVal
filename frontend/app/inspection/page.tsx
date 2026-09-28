/**
 * Vehicle Inspection Page
 * Member 3 - Frontend
 * Upload car images and documents
 */

'use client'

import { useState } from 'react'

export default function InspectionPage() {
  const [inspectionId, setInspectionId] = useState<string | null>(null)
  const [images, setImages] = useState<File[]>([])
  const [documents, setDocuments] = useState<File[]>([])
  const [loading, setLoading] = useState(false)

  const apiUrl = process.env.NEXT_PUBLIC_API_URL

  const handleCreateInspection = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${apiUrl}/inspection`, {
        method: 'POST',
      })
      const data = await response.json()
      setInspectionId(data.inspection_id)
      alert(`Inspection created: ${data.inspection_id}`)
    } catch (error) {
      console.error('Error creating inspection:', error)
      alert('Failed to create inspection')
    } finally {
      setLoading(false)
    }
  }

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setImages(Array.from(e.target.files))
    }
  }

  const handleDocumentUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setDocuments(Array.from(e.target.files))
    }
  }

  const handleAnalyze = async () => {
    if (!inspectionId) {
      alert('Please create an inspection first')
      return
    }

    try {
      setLoading(true)
      
      // Upload images
      if (images.length > 0) {
        const formData = new FormData()
        images.forEach((file) => formData.append('files', file))
        
        await fetch(`${apiUrl}/inspection/${inspectionId}/images`, {
          method: 'POST',
          body: formData,
        })
      }

      // Upload documents
      if (documents.length > 0) {
        const formData = new FormData()
        documents.forEach((file) => formData.append('files', file))
        
        await fetch(`${apiUrl}/inspection/${inspectionId}/documents`, {
          method: 'POST',
          body: formData,
        })
      }

      // Run vision analysis
      await fetch(`${apiUrl}/inspection/${inspectionId}/vision`, {
        method: 'POST',
      })

      // Run document extraction
      await fetch(`${apiUrl}/inspection/${inspectionId}/documents/extract`, {
        method: 'POST',
      })

      alert('Analysis started!')
    } catch (error) {
      console.error('Error during analysis:', error)
      alert('Failed to analyze')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-gray-50 py-12">
      <div className="container mx-auto px-4 max-w-2xl">
        <h1 className="text-4xl font-bold text-gray-900 mb-8">
          Vehicle Inspection
        </h1>

        {/* Create Inspection */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Step 1: Create Inspection
          </h2>
          {!inspectionId ? (
            <button
              onClick={handleCreateInspection}
              disabled={loading}
              className="w-full bg-indigo-600 text-white px-6 py-3 rounded-lg hover:bg-indigo-700 disabled:bg-gray-400"
            >
              {loading ? 'Creating...' : 'Create New Inspection'}
            </button>
          ) : (
            <div className="text-green-600 font-bold">
              ✓ Inspection ID: {inspectionId}
            </div>
          )}
        </div>

        {inspectionId && (
          <>
            {/* Upload Images */}
            <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                Step 2: Upload Car Images
              </h2>
              <input
                type="file"
                multiple
                accept="image/*"
                onChange={handleImageUpload}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
              />
              {images.length > 0 && (
                <p className="text-green-600 mt-2">✓ {images.length} image(s) selected</p>
              )}
            </div>

            {/* Upload Documents */}
            <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                Step 3: Upload Documents
              </h2>
              <p className="text-gray-600 mb-4">RC, Insurance, Service Bills</p>
              <input
                type="file"
                multiple
                accept=".pdf,.jpg,.jpeg,.png"
                onChange={handleDocumentUpload}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
              />
              {documents.length > 0 && (
                <p className="text-green-600 mt-2">✓ {documents.length} document(s) selected</p>
              )}
            </div>

            {/* Analyze Button */}
            <div className="bg-white rounded-lg shadow-lg p-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                Step 4: Analyze
              </h2>
              <button
                onClick={handleAnalyze}
                disabled={loading || (images.length === 0 && documents.length === 0)}
                className="w-full bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 disabled:bg-gray-400"
              >
                {loading ? 'Analyzing...' : 'Start Analysis'}
              </button>
              <p className="text-sm text-gray-600 mt-4">
                <a
                  href={`/results/${inspectionId}`}
                  className="text-indigo-600 hover:underline"
                >
                  View Results
                </a>
              </p>
            </div>
          </>
        )}
      </div>
    </main>
  )
}
