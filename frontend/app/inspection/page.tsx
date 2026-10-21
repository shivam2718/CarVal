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
    vin: "",
    make: "",
    model: "",
    variant: "",
    manufacturing_year: "",
    registration_year: "",
    fuel_type: "",
    transmission: "",
    engine_displacement_cc: "",
    engine_power_bhp: "",
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

  // Service Fields - Support multiple service records
  const [serviceRecords, setServiceRecords] = useState<Array<{
    date: string;
    mileage_km: string;
    work_done: string;
    cost: string;
  }>>([])
  const [newServiceRecord, setNewServiceRecord] = useState({
    date: "",
    mileage_km: "",
    work_done: "",
    cost: "",
  })
  const [serviceFiles, setServiceFiles] = useState<File[]>([])
  const [serviceResults, setServiceResults] = useState<any>(null)

  // Odometer image and user-entered reading
  const [odometerReading, setOdometerReading] = useState("")
  const [odometerFile, setOdometerFile] = useState<File | null>(null)
  const [odometerResults, setOdometerResults] = useState<any>(null)

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

  const verifyDocument = async (docType: 'rc' | 'insurance' | 'service' | 'odometer') => {
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
    } else if (docType === 'odometer') {
      fields = { odometer_reading_km: odometerReading }
      file = odometerFile
      if (!file) {
        alert('Please upload an odometer image')
        return
      }
      if (!odometerReading.trim()) {
        alert('Please enter the odometer reading in kilometers')
        return
      }
    } else {
      // For service, combine all service records into a single fields object
      fields = {}
      serviceRecords.forEach((record, index) => {
        fields[`service_${index}_date`] = record.date
        fields[`service_${index}_mileage_km`] = record.mileage_km
        fields[`service_${index}_work_done`] = record.work_done
        fields[`service_${index}_cost`] = record.cost
      })
      
      files = serviceFiles
      if (files.length === 0) {
        alert('Please upload at least one Service document')
        return
      }
      if (serviceRecords.length === 0) {
        alert('Please add at least one service record')
        return
      }
    }

    try {
      setVerifying(docType)
      const formData = new FormData()
      
      if (docType === 'service') {
        serviceFiles.forEach(f => formData.append('files', f))
      } else {
        const uploadName = docType === 'odometer' && !file!.name.toLowerCase().includes('odometer')
          ? `odometer_${file!.name}`
          : file!.name
        formData.append('files', file!, uploadName)
      }

      // Upload document
      console.log(`📤 Uploading ${docType} document(s)...`)
      const uploadRes = await fetch(`${apiUrl}/inspection/${inspectionId}/documents`, {
        method: 'POST',
        body: formData,
      })

      if (!uploadRes.ok) throw new Error('Upload failed')
      const uploadData = await uploadRes.json()
      console.log('✓ Document(s) uploaded')

      // Verify fields
      console.log(`🔍 Verifying ${docType} fields...`)
      const verifyRes = await fetch(`${apiUrl}/inspection/${inspectionId}/verify-fields`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          fields,
          document_ids: uploadData.files.map((uploadedFile: { file_id: string }) => uploadedFile.file_id),
        }),
      })

      if (!verifyRes.ok) {
        const errorData = await verifyRes.json().catch(() => null)
        const detail = errorData?.detail
        throw new Error(typeof detail === 'string' ? detail : detail?.message || 'Verification failed')
      }
      const result = await verifyRes.json()
      
      console.log(`✓ ${docType} verification complete:`, result)

      if (docType === 'rc') {
        setRcResults(result)
      } else if (docType === 'insurance') {
        setInsuranceResults(result)
      } else if (docType === 'odometer') {
        setOdometerResults(result)
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
                      { field: 'registration_number', label: 'Registration Number', type: 'text', required: true },
                      { field: 'vin', label: 'VIN / Chassis Number', type: 'text', required: true },
                      { field: 'make', label: 'Make (Brand)', type: 'text', required: true },
                      { field: 'model', label: 'Model', type: 'text', required: true },
                      { field: 'variant', label: 'Variant (e.g., LXi, VXi)', type: 'text', required: false },
                      { field: 'manufacturing_year', label: 'Manufacturing Year', type: 'number', required: true },
                      { field: 'registration_year', label: 'Registration Year', type: 'number', required: true },
                      { field: 'fuel_type', label: 'Fuel Type', type: 'select', required: true },
                      { field: 'transmission', label: 'Transmission', type: 'select', required: true },
                      { field: 'engine_displacement_cc', label: 'Engine Displacement (cc)', type: 'number', required: true },
                      { field: 'engine_power_bhp', label: 'Engine Power (bhp)', type: 'number', required: false },
                    ].map((item) => (
                      <div key={item.field}>
                        <label className="block text-sm text-gray-300 mb-2 font-semibold">
                          {item.label}
                          {item.required && <span className="text-red-400">*</span>}
                        </label>
                        {item.type === 'select' ? (
                          <select
                            value={rcFields[item.field as keyof typeof rcFields]}
                            onChange={(e) => handleRcFieldChange(item.field, e.target.value)}
                            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm focus:border-cyan-500 outline-none"
                          >
                            <option value="">Select {item.label.toLowerCase()}</option>
                            {item.field === 'fuel_type' ? (
                              <>
                                <option value="petrol">Petrol</option>
                                <option value="diesel">Diesel</option>
                                <option value="cng">CNG</option>
                                <option value="lpg">LPG</option>
                                <option value="electric">Electric</option>
                                <option value="hybrid">Hybrid</option>
                              </>
                            ) : item.field === 'transmission' ? (
                              <>
                                <option value="manual">Manual</option>
                                <option value="automatic">Automatic</option>
                              </>
                            ) : null}
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

                {/* Add Service Record Form */}
                <div className="mb-6 pb-6 border-b border-purple-500/20">
                  <h3 className="text-lg font-bold text-purple-200 mb-4">Add Service Records:</h3>
                  <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-700 mb-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                      <div>
                        <label className="block text-sm text-gray-300 mb-2 font-semibold">Service Date*</label>
                        <input
                          type="date"
                          value={newServiceRecord.date}
                          onChange={(e) => setNewServiceRecord(prev => ({ ...prev, date: e.target.value }))}
                          className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm focus:border-purple-500 outline-none"
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-300 mb-2 font-semibold">Mileage (km)*</label>
                        <input
                          type="number"
                          value={newServiceRecord.mileage_km}
                          onChange={(e) => setNewServiceRecord(prev => ({ ...prev, mileage_km: e.target.value }))}
                          placeholder="e.g., 45000"
                          className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm focus:border-purple-500 outline-none"
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-300 mb-2 font-semibold">Work Done*</label>
                        <input
                          type="text"
                          value={newServiceRecord.work_done}
                          onChange={(e) => setNewServiceRecord(prev => ({ ...prev, work_done: e.target.value }))}
                          placeholder="e.g., Oil Change, Filter Replacement"
                          className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm focus:border-purple-500 outline-none"
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-300 mb-2 font-semibold">Cost (INR)</label>
                        <input
                          type="number"
                          value={newServiceRecord.cost}
                          onChange={(e) => setNewServiceRecord(prev => ({ ...prev, cost: e.target.value }))}
                          placeholder="e.g., 2500"
                          className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm focus:border-purple-500 outline-none"
                        />
                      </div>
                    </div>
                    <button
                      onClick={() => {
                        if (!newServiceRecord.date || !newServiceRecord.mileage_km || !newServiceRecord.work_done) {
                          alert('Please fill all required fields (marked with *)')
                          return
                        }
                        setServiceRecords(prev => [...prev, newServiceRecord])
                        setNewServiceRecord({ date: '', mileage_km: '', work_done: '', cost: '' })
                      }}
                      className="w-full bg-purple-600 hover:bg-purple-500 text-white font-bold py-2 px-4 rounded-lg transition-all"
                    >
                      + Add Service Record
                    </button>
                  </div>

                  {/* Display Added Service Records */}
                  {serviceRecords.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="text-purple-300 font-semibold">Added Records ({serviceRecords.length}):</h4>
                      {serviceRecords.map((record, idx) => (
                        <div key={idx} className="bg-purple-500/20 border border-purple-400/30 rounded-lg p-3 flex justify-between items-start">
                          <div className="flex-1">
                            <p className="text-purple-300 font-semibold text-sm">{record.date} - {record.mileage_km} km</p>
                            <p className="text-gray-400 text-xs">{record.work_done}</p>
                            {record.cost && <p className="text-gray-400 text-xs">Cost: ₹{record.cost}</p>}
                          </div>
                          <button
                            onClick={() => setServiceRecords(prev => prev.filter((_, i) => i !== idx))}
                            className="text-red-400 hover:text-red-300 ml-4 font-bold"
                          >
                            ✕
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
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
                  disabled={verifying === 'service' || serviceFiles.length === 0 || serviceRecords.length === 0}
                  className={`w-full font-bold py-3 px-4 rounded-lg transition-all ${
                    verifying === 'service' || serviceFiles.length === 0 || serviceRecords.length === 0
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
                      {serviceResults.all_matched ? '✅ All Service Records Verified' : '⚠️ Some Service Records Not Found'}
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

            {/* Odometer Image Verification */}
            <div className="mb-8 rounded-2xl border border-amber-500/20 bg-gradient-to-br from-amber-500/10 to-orange-500/10 p-8">
              <h2 className="mb-2 text-2xl font-bold text-amber-300">Odometer Reading</h2>
              <p className="mb-6 text-sm text-gray-300">
                Upload a clear photo of the dashboard odometer and enter the displayed reading. OCR will check the number in the image.
              </p>

              <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
                <div>
                  <label htmlFor="odometer-reading" className="mb-2 block text-sm font-semibold text-gray-300">
                    Odometer reading (km)
                  </label>
                  <input
                    id="odometer-reading"
                    type="number"
                    min="0"
                    step="1"
                    value={odometerReading}
                    onChange={(e) => setOdometerReading(e.target.value)}
                    placeholder="e.g., 48235"
                    className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-3 text-white outline-none focus:border-amber-500"
                  />
                </div>
                <div>
                  <label htmlFor="odometer-image" className="mb-2 block text-sm font-semibold text-gray-300">
                    Odometer image
                  </label>
                  <input
                    id="odometer-image"
                    type="file"
                    accept=".jpg,.jpeg,.png,.bmp,.tif,.tiff"
                    onChange={(e) => setOdometerFile(e.target.files?.[0] ?? null)}
                    className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2.5 text-white file:mr-4 file:rounded file:border-0 file:bg-amber-600 file:px-3 file:py-2 file:font-semibold file:text-white"
                  />
                  {odometerFile && <p className="mt-2 text-sm text-amber-200">Selected: {odometerFile.name}</p>}
                </div>
              </div>

              <button
                onClick={() => verifyDocument('odometer')}
                disabled={verifying === 'odometer' || !odometerFile || !odometerReading.trim()}
                className={`mt-6 w-full rounded-lg px-4 py-3 font-bold transition-all ${
                  verifying === 'odometer' || !odometerFile || !odometerReading.trim()
                    ? 'cursor-not-allowed bg-gray-600 text-gray-400'
                    : 'bg-amber-600 text-white hover:bg-amber-500'
                }`}
              >
                {verifying === 'odometer' ? 'Verifying odometer...' : 'Verify Odometer Reading'}
              </button>

              {odometerResults && (
                <div className={`mt-6 rounded-lg border p-4 ${
                  odometerResults.all_matched
                    ? 'border-green-400/30 bg-green-500/20'
                    : 'border-yellow-400/30 bg-yellow-500/20'
                }`}>
                  <h3 className={`mb-3 font-bold ${odometerResults.all_matched ? 'text-green-300' : 'text-yellow-300'}`}>
                    {odometerResults.all_matched ? 'Odometer reading verified' : 'Odometer reading could not be verified'}
                  </h3>
                  {Object.entries(odometerResults.verification_results).map(([field, result]: any) => (
                    <div key={field} className="flex justify-between text-sm">
                      <span className="text-gray-300">Entered reading: {result.value} km</span>
                      <span className={result.found ? 'text-green-400' : 'text-red-400'}>
                        {result.found ? 'Found in image' : 'Not found'}
                      </span>
                    </div>
                  ))}
                  <div className="mt-3 border-t border-white/10 pt-3 text-sm">
                    <p className="text-gray-300">OCR candidates: <span className="font-mono text-white">
                      {odometerResults.recognized_readings?.length ? odometerResults.recognized_readings.join(', ') : 'No digits recognized'}
                    </span></p>
                    {odometerResults.ocr_engines?.length > 0 && (
                      <p className="mt-1 text-gray-400">Recognizers: {odometerResults.ocr_engines.join(', ')}</p>
                    )}
                    {typeof odometerResults.ocr_confidence === 'number' && (
                      <p className="mt-1 text-gray-400">OCR confidence: {Math.round(odometerResults.ocr_confidence * 100)}%</p>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Summary Section */}
            <div className="mt-12 p-6 rounded-2xl border border-blue-500/20 bg-blue-500/10">
              <h3 className="text-lg font-bold text-blue-300 mb-4">✨ Verification Summary</h3>
              <div className="grid grid-cols-2 gap-4 text-center md:grid-cols-4">
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
                <div>
                  <p className="text-gray-400 text-sm mb-1">Odometer Status</p>
                  <p className={`font-bold ${odometerResults?.all_matched ? 'text-green-400' : odometerResults ? 'text-yellow-400' : 'text-gray-500'}`}>
                    {odometerResults?.all_matched ? 'Verified' : odometerResults ? 'Incomplete' : 'Pending'}
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
              <span>For each document or odometer image (RC, Insurance, Service):</span>
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
