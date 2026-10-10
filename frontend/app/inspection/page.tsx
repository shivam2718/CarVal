/**
 * Vehicle Inspection Page - Document Verification
 * Verify each document independently: Fill fields → Upload → Verify
 */

'use client'

import { useState } from 'react'

export default function InspectionPage() {
  const [inspectionId, setInspectionId] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [verifying, setVerifying] = useState<string | null>(null)

  // RC Fields
  const [rcFields, setRcFields] = useState({
    registration_number: "",
    model: "",
    manufacturing_year: "",
    fuel_type: "",
    vin: "",
  })
  const [rcFile, setRcFile] = useState<File | null>(null)
  const [rcResults, setRcResults] = useState<any>(null)

  // Insurance Fields
  const [insuranceFields, setInsuranceFields] = useState({
    policy_number: "",
    valid_from: "",
    valid_until: "",
  })
  const [insuranceFile, setInsuranceFile] = useState<File | null>(null)
  const [insuranceResults, setInsuranceResults] = useState<any>(null)

  // Service Fields
  const [serviceFields, setServiceFields] = useState({
    claimed_mileage_km: "",
    accident_history: "",
  })
  const [serviceFiles, setServiceFiles] = useState<File[]>([])
  const [serviceResults, setServiceResults] = useState<any>(null)

  const apiUrl = process.env.NEXT_PUBLIC_API_URL

  const handleCreateInspection = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${apiUrl}/inspection`, { method: 'POST' })
      if (!response.ok) throw new Error('Failed to create inspection')
      const data = await response.json()
      setInspectionId(data.inspection_id)
      console.log('✓ Inspection created:', data.inspection_id)
    } catch (error) {
      console.error('Error:', error)
      alert(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`)
    } finally {
      setLoading(false)
    }
  }

  const verifyDocument = async (docType: 'rc' | 'insurance' | 'service') => {
    if (!inspectionId) {
      alert('Please create inspection first')
      return
    }

    let fields, file, files
    if (docType === 'rc') {
      fields = rcFields
      file = rcFile
      if (!file) {
        alert('Please upload RC document')
        return
      }
    } else if (docType === 'insurance') {
      fields = insuranceFields
      file = insuranceFile
      if (!file) {
        alert('Please upload Insurance document')
        return
      }
    } else {
      fields = serviceFields
      files = serviceFiles
      if (files.length === 0) {
        alert('Please upload at least one Service document')
        return
      }
    }

    try {
      setVerifying(docType)
      const formData = new FormData()
      
      if (docType === 'service') {
        serviceFiles.forEach(f => formData.append('files', f))
      } else {
        formData.append('files', file!)
      }

      // Upload document
      console.log(`📤 Uploading ${docType} document(s)...`)
      const uploadRes = await fetch(`${apiUrl}/inspection/${inspectionId}/documents`, {
        method: 'POST',
        body: formData,
      })

      if (!uploadRes.ok) throw new Error('Upload failed')
      console.log('✓ Document(s) uploaded')

      // Verify fields
      console.log(`🔍 Verifying ${docType} fields...`)
      const verifyRes = await fetch(`${apiUrl}/inspection/${inspectionId}/verify-fields`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(fields),
      })

      if (!verifyRes.ok) throw new Error('Verification failed')
      const result = await verifyRes.json()
      
      console.log(`✓ ${docType} verification complete:`, result)

      if (docType === 'rc') {
        setRcResults(result)
      } else if (docType === 'insurance') {
        setInsuranceResults(result)
      } else {
        setServiceResults(result)
      }

      if (result.all_matched) {
        alert(`✅ ${docType.toUpperCase()} verified successfully!`)
      } else {
        alert(`⚠️ Some fields not found in ${docType} document`)
      }
    } catch (error) {
      console.error('Error:', error)
      alert(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`)
    } finally {
      setVerifying(null)
    }
  }

  const handleRcFieldChange = (field: string, value: string) => {
    setRcFields(prev => ({ ...prev, [field]: value }))
  }

  const handleInsuranceFieldChange = (field: string, value: string) => {
    setInsuranceFields(prev => ({ ...prev, [field]: value }))
  }

  const handleServiceFieldChange = (field: string, value: string) => {
    setServiceFields(prev => ({ ...prev, [field]: value }))
  }

  return (
    <div className="min-h-screen bg-black">
      {/* Header */}
      <div className="border-b border-cyan-500/20 backdrop-blur-md bg-black/20">
        <div className="container mx-auto px-6 py-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2">📋 Document Verification</h1>
              <p className="text-cyan-400">Verify each document independently</p>
            </div>
            <a href="/" className="px-6 py-3 bg-gray-800 hover:bg-gray-700 text-white rounded-lg font-semibold transition-all">
              ← Back
            </a>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-6 py-12 max-w-5xl">
        
        {/* Step 1: Create Inspection */}
        <div className="mb-8">
          <div className="rounded-2xl border border-cyan-500/20 bg-gradient-to-br from-cyan-500/10 to-blue-500/10 p-8">
            <h2 className="text-2xl font-bold text-white mb-6">Step 1: Create Inspection Session</h2>
            {!inspectionId ? (
              <button
                onClick={handleCreateInspection}
                disabled={loading}
                className="w-full bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-bold py-4 px-6 rounded-lg transition-all disabled:opacity-50"
              >
                {loading ? '⏳ Creating...' : '🚀 Create New Inspection'}
              </button>
            ) : (
              <div className="bg-green-500/20 border border-green-400/30 rounded-lg p-4">
                <p className="text-green-300 font-bold">✓ Inspection Created: {inspectionId}</p>
              </div>
            )}
          </div>
        </div>

        {inspectionId && (
          <>
            {/* RC Certificate Section */}
            <div className="mb-8">
              <div className="rounded-2xl border border-cyan-500/20 bg-gradient-to-br from-cyan-500/10 to-blue-500/10 p-8">
                <h2 className="text-2xl font-bold text-cyan-300 mb-6 flex items-center">
                  <span className="text-3xl mr-3">📋</span> Registration Certificate (RC)
                </h2>

                {/* RC Fields */}
                <div className="mb-6 pb-6 border-b border-cyan-500/20">
                  <h3 className="text-lg font-bold text-cyan-200 mb-4">Enter RC Information:</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {[
                      { field: 'registration_number', label: 'Registration Number', type: 'text' },
                      { field: 'model', label: 'Model', type: 'text' },
                      { field: 'manufacturing_year', label: 'Manufacturing Year', type: 'number' },
                      { field: 'fuel_type', label: 'Fuel Type', type: 'select' },
                      { field: 'vin', label: 'VIN / Chassis Number', type: 'text' },
                    ].map((item) => (
                      <div key={item.field}>
                        <label className="block text-sm text-gray-300 mb-2 font-semibold">{item.label}</label>
                        {item.type === 'select' ? (
                          <select
                            value={rcFields[item.field as keyof typeof rcFields]}
                            onChange={(e) => handleRcFieldChange(item.field, e.target.value)}
                            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm focus:border-cyan-500 outline-none"
                          >
                            <option value="">Select fuel type</option>
                            <option value="petrol">Petrol</option>
                            <option value="diesel">Diesel</option>
                            <option value="cng">CNG</option>
                            <option value="lpg">LPG</option>
                            <option value="electric">Electric</option>
                            <option value="hybrid">Hybrid</option>
                          </select>
                        ) : (
                          <input
                            type={item.type}
                            value={rcFields[item.field as keyof typeof rcFields]}
                            onChange={(e) => handleRcFieldChange(item.field, e.target.value)}
                            placeholder={`Enter ${item.label.toLowerCase()}`}
                            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm focus:border-cyan-500 outline-none"
                          />
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* RC Upload */}
                <div className="mb-6 pb-6 border-b border-cyan-500/20">
                  <h3 className="text-lg font-bold text-cyan-200 mb-4">Upload RC Document:</h3>
                  <div className="border-2 border-dashed border-cyan-400/50 rounded-lg p-6 text-center hover:border-cyan-400 transition-all cursor-pointer mb-3">
                    <input
                      type="file"
                      accept=".pdf,.jpg,.jpeg,.png"
                      onChange={(e) => setRcFile(e.target.files?.[0] || null)}
                      className="w-full cursor-pointer"
                    />
                  </div>
                  {rcFile && (
                    <div className="bg-green-500/20 border border-green-400/30 rounded-lg p-3">
                      <p className="text-green-300 font-semibold text-sm">✓ {rcFile.name}</p>
                    </div>
                  )}
                </div>

                {/* RC Verify Button */}
                <button
                  onClick={() => verifyDocument('rc')}
                  disabled={verifying === 'rc' || !rcFile}
                  className={`w-full font-bold py-3 px-4 rounded-lg transition-all ${
                    verifying === 'rc' || !rcFile
                      ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                      : 'bg-cyan-600 hover:bg-cyan-500 text-white'
                  }`}
                >
                  {verifying === 'rc' ? '⏳ Verifying...' : '✓ Verify RC Fields'}
                </button>

                {/* RC Results */}
                {rcResults && (
                  <div className={`mt-6 p-4 rounded-lg border ${
                    rcResults.all_matched
                      ? 'bg-green-500/20 border-green-400/30'
                      : 'bg-yellow-500/20 border-yellow-400/30'
                  }`}>
                    <h4 className={`font-bold mb-3 ${rcResults.all_matched ? 'text-green-300' : 'text-yellow-300'}`}>
                      {rcResults.all_matched ? '✅ All RC Fields Verified' : '⚠️ Some RC Fields Not Found'}
                    </h4>
                    <div className="space-y-2">
                      {Object.entries(rcResults.verification_results).map(([field, result]: any) => (
                        <div key={field} className="flex justify-between text-sm">
                          <span className="text-gray-300">{field.replace(/_/g, ' ')}</span>
                          <span className={result.found ? 'text-green-400' : 'text-red-400'}>
                            {result.found ? '✅ Found' : '❌ Not Found'}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Insurance Section */}
            <div className="mb-8">
              <div className="rounded-2xl border border-green-500/20 bg-gradient-to-br from-green-500/10 to-emerald-500/10 p-8">
                <h2 className="text-2xl font-bold text-green-300 mb-6 flex items-center">
                  <span className="text-3xl mr-3">🛡️</span> Insurance Policy
                </h2>

                {/* Insurance Fields */}
                <div className="mb-6 pb-6 border-b border-green-500/20">
                  <h3 className="text-lg font-bold text-green-200 mb-4">Enter Insurance Information:</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {[
                      { field: 'policy_number', label: 'Policy Number', type: 'text' },
                      { field: 'valid_from', label: 'Valid From', type: 'date' },
                      { field: 'valid_until', label: 'Valid Until', type: 'date' },
                    ].map((item) => (
                      <div key={item.field}>
                        <label className="block text-sm text-gray-300 mb-2 font-semibold">{item.label}</label>
                        <input
                          type={item.type}
                          value={insuranceFields[item.field as keyof typeof insuranceFields]}
                          onChange={(e) => handleInsuranceFieldChange(item.field, e.target.value)}
                          placeholder={`Enter ${item.label.toLowerCase()}`}
                          className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm focus:border-green-500 outline-none"
                        />
                      </div>
                    ))}
                  </div>
                </div>

                {/* Insurance Upload */}
                <div className="mb-6 pb-6 border-b border-green-500/20">
                  <h3 className="text-lg font-bold text-green-200 mb-4">Upload Insurance Document:</h3>
                  <div className="border-2 border-dashed border-green-400/50 rounded-lg p-6 text-center hover:border-green-400 transition-all cursor-pointer mb-3">
                    <input
                      type="file"
                      accept=".pdf,.jpg,.jpeg,.png"
                      onChange={(e) => setInsuranceFile(e.target.files?.[0] || null)}
                      className="w-full cursor-pointer"
                    />
                  </div>
                  {insuranceFile && (
                    <div className="bg-green-500/20 border border-green-400/30 rounded-lg p-3">
                      <p className="text-green-300 font-semibold text-sm">✓ {insuranceFile.name}</p>
                    </div>
                  )}
                </div>

                {/* Insurance Verify Button */}
                <button
                  onClick={() => verifyDocument('insurance')}
                  disabled={verifying === 'insurance' || !insuranceFile}
                  className={`w-full font-bold py-3 px-4 rounded-lg transition-all ${
                    verifying === 'insurance' || !insuranceFile
                      ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                      : 'bg-green-600 hover:bg-green-500 text-white'
                  }`}
                >
                  {verifying === 'insurance' ? '⏳ Verifying...' : '✓ Verify Insurance Fields'}
                </button>

                {/* Insurance Results */}
                {insuranceResults && (
                  <div className={`mt-6 p-4 rounded-lg border ${
                    insuranceResults.all_matched
                      ? 'bg-green-500/20 border-green-400/30'
                      : 'bg-yellow-500/20 border-yellow-400/30'
                  }`}>
                    <h4 className={`font-bold mb-3 ${insuranceResults.all_matched ? 'text-green-300' : 'text-yellow-300'}`}>
                      {insuranceResults.all_matched ? '✅ All Insurance Fields Verified' : '⚠️ Some Insurance Fields Not Found'}
                    </h4>
                    <div className="space-y-2">
                      {Object.entries(insuranceResults.verification_results).map(([field, result]: any) => (
                        <div key={field} className="flex justify-between text-sm">
                          <span className="text-gray-300">{field.replace(/_/g, ' ')}</span>
                          <span className={result.found ? 'text-green-400' : 'text-red-400'}>
                            {result.found ? '✅ Found' : '❌ Not Found'}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Service Section */}
            <div className="mb-8">
              <div className="rounded-2xl border border-purple-500/20 bg-gradient-to-br from-purple-500/10 to-pink-500/10 p-8">
                <h2 className="text-2xl font-bold text-purple-300 mb-6 flex items-center">
                  <span className="text-3xl mr-3">🔧</span> Service Bills
                </h2>

                {/* Service Fields */}
                <div className="mb-6 pb-6 border-b border-purple-500/20">
                  <h3 className="text-lg font-bold text-purple-200 mb-4">Enter Service Information:</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {[
                      { field: 'claimed_mileage_km', label: 'Claimed Mileage (km)', type: 'number' },
                      { field: 'accident_history', label: 'Accident History', type: 'select' },
                    ].map((item) => (
                      <div key={item.field}>
                        <label className="block text-sm text-gray-300 mb-2 font-semibold">{item.label}</label>
                        {item.type === 'select' ? (
                          <select
                            value={serviceFields[item.field as keyof typeof serviceFields]}
                            onChange={(e) => handleServiceFieldChange(item.field, e.target.value)}
                            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm focus:border-purple-500 outline-none"
                          >
                            <option value="">Select accident history</option>
                            <option value="none">None</option>
                            <option value="minor">Minor</option>
                            <option value="major">Major</option>
                          </select>
                        ) : (
                          <input
                            type={item.type}
                            value={serviceFields[item.field as keyof typeof serviceFields]}
                            onChange={(e) => handleServiceFieldChange(item.field, e.target.value)}
                            placeholder={`Enter ${item.label.toLowerCase()}`}
                            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm focus:border-purple-500 outline-none"
                          />
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Service Upload */}
                <div className="mb-6 pb-6 border-b border-purple-500/20">
                  <h3 className="text-lg font-bold text-purple-200 mb-4">Upload Service Bill(s):</h3>
                  <div className="border-2 border-dashed border-purple-400/50 rounded-lg p-6 text-center hover:border-purple-400 transition-all cursor-pointer mb-3">
                    <input
                      type="file"
                      accept=".pdf,.jpg,.jpeg,.png"
                      multiple
                      onChange={(e) => setServiceFiles(Array.from(e.target.files || []))}
                      className="w-full cursor-pointer"
                    />
                  </div>
                  {serviceFiles.length > 0 && (
                    <div className="space-y-2">
                      {serviceFiles.map((file, idx) => (
                        <div key={idx} className="bg-purple-500/20 border border-purple-400/30 rounded-lg p-3">
                          <p className="text-purple-300 font-semibold text-sm">✓ {file.name}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Service Verify Button */}
                <button
                  onClick={() => verifyDocument('service')}
                  disabled={verifying === 'service' || serviceFiles.length === 0}
                  className={`w-full font-bold py-3 px-4 rounded-lg transition-all ${
                    verifying === 'service' || serviceFiles.length === 0
                      ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                      : 'bg-purple-600 hover:bg-purple-500 text-white'
                  }`}
                >
                  {verifying === 'service' ? '⏳ Verifying...' : '✓ Verify Service Fields'}
                </button>

                {/* Service Results */}
                {serviceResults && (
                  <div className={`mt-6 p-4 rounded-lg border ${
                    serviceResults.all_matched
                      ? 'bg-green-500/20 border-green-400/30'
                      : 'bg-yellow-500/20 border-yellow-400/30'
                  }`}>
                    <h4 className={`font-bold mb-3 ${serviceResults.all_matched ? 'text-green-300' : 'text-yellow-300'}`}>
                      {serviceResults.all_matched ? '✅ All Service Fields Verified' : '⚠️ Some Service Fields Not Found'}
                    </h4>
                    <div className="space-y-2">
                      {Object.entries(serviceResults.verification_results).map(([field, result]: any) => (
                        <div key={field} className="flex justify-between text-sm">
                          <span className="text-gray-300">{field.replace(/_/g, ' ')}</span>
                          <span className={result.found ? 'text-green-400' : 'text-red-400'}>
                            {result.found ? '✅ Found' : '❌ Not Found'}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Summary Section */}
            <div className="mt-12 p-6 rounded-2xl border border-blue-500/20 bg-blue-500/10">
              <h3 className="text-lg font-bold text-blue-300 mb-4">✨ Verification Summary</h3>
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <p className="text-gray-400 text-sm mb-1">RC Status</p>
                  <p className={`font-bold ${rcResults?.all_matched ? 'text-green-400' : rcResults ? 'text-yellow-400' : 'text-gray-500'}`}>
                    {rcResults?.all_matched ? '✅ Verified' : rcResults ? '⚠️ Incomplete' : '○ Pending'}
                  </p>
                </div>
                <div>
                  <p className="text-gray-400 text-sm mb-1">Insurance Status</p>
                  <p className={`font-bold ${insuranceResults?.all_matched ? 'text-green-400' : insuranceResults ? 'text-yellow-400' : 'text-gray-500'}`}>
                    {insuranceResults?.all_matched ? '✅ Verified' : insuranceResults ? '⚠️ Incomplete' : '○ Pending'}
                  </p>
                </div>
                <div>
                  <p className="text-gray-400 text-sm mb-1">Service Status</p>
                  <p className={`font-bold ${serviceResults?.all_matched ? 'text-green-400' : serviceResults ? 'text-yellow-400' : 'text-gray-500'}`}>
                    {serviceResults?.all_matched ? '✅ Verified' : serviceResults ? '⚠️ Incomplete' : '○ Pending'}
                  </p>
                </div>
              </div>
            </div>
          </>
        )}

        {/* Info Box */}
        <div className="mt-12 rounded-2xl border border-gray-500/20 bg-gray-500/5 p-8">
          <h3 className="text-xl font-bold text-white mb-4">ℹ️ How It Works</h3>
          <ol className="space-y-3 text-gray-300">
            <li className="flex">
              <span className="text-cyan-400 font-bold mr-3">1.</span>
              <span>Create an inspection session to get started</span>
            </li>
            <li className="flex">
              <span className="text-cyan-400 font-bold mr-3">2.</span>
              <span>For each document (RC, Insurance, Service):</span>
            </li>
            <li className="flex ml-8">
              <span className="text-cyan-400 font-bold mr-3">a.</span>
              <span>Enter the field values from that document</span>
            </li>
            <li className="flex ml-8">
              <span className="text-cyan-400 font-bold mr-3">b.</span>
              <span>Upload the document file</span>
            </li>
            <li className="flex ml-8">
              <span className="text-cyan-400 font-bold mr-3">c.</span>
              <span>Click "Verify" to check if values exist in document</span>
            </li>
            <li className="flex">
              <span className="text-cyan-400 font-bold mr-3">3.</span>
              <span>View results for each document independently</span>
            </li>
          </ol>
        </div>
      </div>
    </div>
  )
}
