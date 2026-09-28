/**
 * CarVal Dashboard - Home Page
 * Member 3 - Frontend
 */

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-20">
        {/* Header */}
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            CarVal
          </h1>
          <p className="text-xl text-gray-600">
            AI-Powered Vehicle Inspection & Valuation
          </p>
        </div>

        {/* Demo CTAs */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
          {/* Vision Service Card */}
          <div className="bg-white rounded-lg shadow-lg p-8 hover:shadow-xl transition">
            <h2 className="text-2xl font-bold text-indigo-600 mb-4">
              📸 Damage Detection
            </h2>
            <p className="text-gray-600 mb-6">
              Upload car images and detect visible damage with YOLOv8
            </p>
            <a
              href="/inspection"
              className="inline-block bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700"
            >
              Start Inspection
            </a>
          </div>

          {/* Document AI Card */}
          <div className="bg-white rounded-lg shadow-lg p-8 hover:shadow-xl transition">
            <h2 className="text-2xl font-bold text-indigo-600 mb-4">
              📄 Document Extraction
            </h2>
            <p className="text-gray-600 mb-6">
              Upload RC, insurance and service documents for information extraction
            </p>
            <button className="inline-block bg-gray-400 text-white px-6 py-2 rounded-lg cursor-not-allowed">
              Coming in Review 2
            </button>
          </div>

          {/* Valuation Card */}
          <div className="bg-white rounded-lg shadow-lg p-8 hover:shadow-xl transition">
            <h2 className="text-2xl font-bold text-indigo-600 mb-4">
              💰 Valuation
            </h2>
            <p className="text-gray-600 mb-6">
              Fair market value prediction and negotiation insights
            </p>
            <button className="inline-block bg-gray-400 text-white px-6 py-2 rounded-lg cursor-not-allowed">
              Review 3+
            </button>
          </div>
        </div>

        {/* Info Section */}
        <div className="bg-white rounded-lg shadow-lg p-8 mt-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            Review 2 Roadmap
          </h2>
          <ul className="space-y-3 text-gray-700">
            <li className="flex items-start">
              <span className="text-indigo-600 font-bold mr-3">✓</span>
              <span>Vision Service: YOLOv8 damage detection with bounding boxes</span>
            </li>
            <li className="flex items-start">
              <span className="text-indigo-600 font-bold mr-3">✓</span>
              <span>Document AI: RC, insurance, service bill extraction</span>
            </li>
            <li className="flex items-start">
              <span className="text-indigo-600 font-bold mr-3">✓</span>
              <span>Backend Integration: FastAPI orchestrator connecting all services</span>
            </li>
            <li className="flex items-start">
              <span className="text-indigo-600 font-bold mr-3">✓</span>
              <span>Combined Results: Structured Vehicle JSON with all findings</span>
            </li>
          </ul>
        </div>
      </div>
    </main>
  )
}
