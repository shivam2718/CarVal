/**
 * CarVal Dashboard - Home Page
 * AI-Powered Vehicle Intelligence Platform
 * Modern 2040 Design
 */

export default function Home() {
  return (
    <div className="min-h-screen bg-black overflow-hidden">
      {/* Animated Background */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute inset-0 bg-gradient-to-br from-cyan-600/5 via-purple-600/5 to-pink-600/5"></div>
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute top-1/2 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }}></div>
        <div className="absolute bottom-0 left-1/2 w-96 h-96 bg-pink-500/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '2s' }}></div>
      </div>

      <div className="relative z-10">
        {/* Header */}
        <header className="border-b border-cyan-500/10 backdrop-blur-md bg-black/20">
          <div className="container mx-auto px-6 py-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3 group cursor-pointer">
                <div className="relative w-14 h-14">
                  <div className="absolute inset-0 bg-gradient-to-r from-cyan-500 to-purple-500 rounded-2xl blur-lg opacity-75 group-hover:opacity-100 transition-opacity"></div>
                  <div className="relative w-14 h-14 bg-black rounded-2xl flex items-center justify-center border border-cyan-500/30">
                    <span className="text-2xl">⚡</span>
                  </div>
                </div>
                <div>
                  <h1 className="text-3xl font-black bg-gradient-to-r from-cyan-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
                    CarVal
                  </h1>
                  <p className="text-xs text-cyan-400/70 font-mono">v2.0 • AI Intelligence</p>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <div className="px-4 py-2 rounded-full bg-gradient-to-r from-green-500/20 to-emerald-500/20 border border-green-500/30 backdrop-blur-sm">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                    <p className="text-sm font-semibold text-green-300">System Active</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Hero Section */}
        <section className="container mx-auto px-6 py-24">
          <div className="text-center mb-20">
            <h2 className="text-7xl md:text-8xl font-black mb-6 leading-tight">
              <span className="bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-400 bg-clip-text text-transparent">
                Next-Gen Vehicle
              </span>
              <br />
              <span className="bg-gradient-to-r from-purple-400 via-pink-400 to-red-400 bg-clip-text text-transparent">
                Intelligence
              </span>
            </h2>
            <p className="text-xl text-cyan-300/70 max-w-2xl mx-auto mb-8 font-light">
              Powered by advanced AI | Real-time analytics | Quantum-grade insights
            </p>
            <div className="flex justify-center gap-3 flex-wrap">
              <div className="px-4 py-2 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-300 font-mono text-sm">
                📋 Document AI
              </div>
              <div className="px-4 py-2 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-300 font-mono text-sm">
                📸 Vision Engine
              </div>
              <div className="px-4 py-2 rounded-lg bg-pink-500/10 border border-pink-500/20 text-pink-300 font-mono text-sm">
                💰 Smart Valuation
              </div>
            </div>
          </div>

          {/* Main CTA Cards */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
            {/* Document Extraction */}
            <div className="group relative">
              <div className="absolute inset-0 bg-gradient-to-r from-cyan-600 to-blue-600 rounded-2xl blur-xl opacity-30 group-hover:opacity-60 transition-all duration-500"></div>
              <div className="relative rounded-2xl p-8 border border-cyan-500/30 bg-gradient-to-br from-black/50 to-black/80 backdrop-blur-xl hover:border-cyan-500/60 transition-all duration-300 group-hover:scale-[1.02]">
                <div className="flex items-start justify-between mb-6">
                  <div>
                    <div className="text-5xl mb-4">📋</div>
                    <h3 className="text-3xl font-black text-white mb-2">Document AI</h3>
                    <p className="text-cyan-400 font-mono text-sm">Optical Recognition • Field Extraction</p>
                  </div>
                  <div className="w-12 h-12 rounded-full bg-gradient-to-r from-cyan-500 to-blue-500 flex items-center justify-center text-white font-bold">
                    ✓
                  </div>
                </div>

                <p className="text-gray-300 mb-8 leading-relaxed">
                  Upload RC certificates, insurance policies & service records. AI extracts structured data with 95% accuracy.
                </p>

                <div className="space-y-3 mb-8">
                  <div className="flex items-center space-x-3 text-cyan-300">
                    <div className="w-1 h-1 bg-cyan-400 rounded-full"></div>
                    <span className="text-sm">Multi-state RC format support</span>
                  </div>
                  <div className="flex items-center space-x-3 text-cyan-300">
                    <div className="w-1 h-1 bg-cyan-400 rounded-full"></div>
                    <span className="text-sm">Real-time confidence scoring</span>
                  </div>
                  <div className="flex items-center space-x-3 text-cyan-300">
                    <div className="w-1 h-1 bg-cyan-400 rounded-full"></div>
                    <span className="text-sm">Structured JSON output</span>
                  </div>
                  <div className="flex items-center space-x-3 text-cyan-300">
                    <div className="w-1 h-1 bg-cyan-400 rounded-full"></div>
                    <span className="text-sm">Insurance claim parsing</span>
                  </div>
                </div>

                <a
                  href="/inspection/analyze"
                  className="w-full group/btn relative overflow-hidden rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 p-0.5"
                >
                  <div className="relative rounded-xl bg-black px-8 py-4 flex items-center justify-center space-x-2 group-hover/btn:bg-black/50 transition-all duration-300">
                    <span className="text-lg">🚀</span>
                    <span className="font-bold text-white">Launch Platform</span>
                  </div>
                </a>
              </div>
            </div>

            {/* Vision Service */}
            <div className="group relative">
              <div className="absolute inset-0 bg-gradient-to-r from-purple-600 to-pink-600 rounded-2xl blur-xl opacity-20 group-hover:opacity-40 transition-all duration-500"></div>
              <div className="relative rounded-2xl p-8 border border-purple-500/20 bg-gradient-to-br from-black/50 to-black/80 backdrop-blur-xl">
                <div className="flex items-start justify-between mb-6">
                  <div>
                    <div className="text-5xl mb-4">📸</div>
                    <h3 className="text-3xl font-black text-white mb-2">Vision Engine</h3>
                    <p className="text-purple-400 font-mono text-sm">Damage Detection • YOLOv8</p>
                  </div>
                  <div className="w-12 h-12 rounded-full bg-gradient-to-r from-purple-600 to-pink-600 flex items-center justify-center text-white font-bold opacity-50">
                    ⏳
                  </div>
                </div>

                <p className="text-gray-400 mb-8 leading-relaxed">
                  Advanced computer vision for detecting vehicle damage, scratches & structural issues.
                </p>

                <div className="space-y-3 mb-8">
                  <div className="flex items-center space-x-3 text-purple-300/60">
                    <div className="w-1 h-1 bg-purple-400 rounded-full"></div>
                    <span className="text-sm">YOLOv8 detection model</span>
                  </div>
                  <div className="flex items-center space-x-3 text-purple-300/60">
                    <div className="w-1 h-1 bg-purple-400 rounded-full"></div>
                    <span className="text-sm">Real-time severity scoring</span>
                  </div>
                  <div className="flex items-center space-x-3 text-purple-300/60">
                    <div className="w-1 h-1 bg-purple-400 rounded-full"></div>
                    <span className="text-sm">Bounding box annotations</span>
                  </div>
                  <div className="flex items-center space-x-3 text-purple-300/60">
                    <div className="w-1 h-1 bg-purple-400 rounded-full"></div>
                    <span className="text-sm">Multi-angle analysis</span>
                  </div>
                </div>

                <button 
                  disabled
                  className="w-full rounded-xl bg-purple-600/20 px-8 py-4 font-bold text-purple-300/50 cursor-not-allowed border border-purple-500/20"
                >
                  Coming in Next Phase
                </button>
              </div>
            </div>
          </div>

          {/* AI Pipeline Timeline */}
          <div className="rounded-2xl border border-cyan-500/20 bg-gradient-to-br from-black/50 to-black/80 backdrop-blur-xl p-8 mb-12">
            <h3 className="text-2xl font-black text-white mb-8">Development Roadmap</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              
              {/* Phase 1 */}
              <div className="relative group">
                <div className="absolute inset-0 bg-gradient-to-r from-green-500 to-emerald-500 rounded-xl blur opacity-40 group-hover:opacity-60 transition-opacity"></div>
                <div className="relative rounded-xl border border-green-500/50 bg-black/70 p-6">
                  <div className="text-4xl mb-3">⚡</div>
                  <h4 className="text-lg font-bold text-green-400 mb-2">Review 2</h4>
                  <p className="text-sm text-gray-400 mb-4">Current Phase</p>
                  <ul className="space-y-1 text-xs text-gray-500">
                    <li>✓ Document AI</li>
                    <li>✓ OCR Engine</li>
                    <li>○ Vision API</li>
                  </ul>
                </div>
              </div>

              {/* Phase 2 */}
              <div className="relative group">
                <div className="absolute inset-0 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-xl blur opacity-20 group-hover:opacity-40 transition-opacity"></div>
                <div className="relative rounded-xl border border-blue-500/30 bg-black/70 p-6">
                  <div className="text-4xl mb-3">💰</div>
                  <h4 className="text-lg font-bold text-blue-400 mb-2">Review 3</h4>
                  <p className="text-sm text-gray-400 mb-4">Next Phase</p>
                  <ul className="space-y-1 text-xs text-gray-500">
                    <li>○ Valuation AI</li>
                    <li>○ Market Data</li>
                    <li>○ Price Prediction</li>
                  </ul>
                </div>
              </div>

              {/* Phase 3 */}
              <div className="relative group">
                <div className="absolute inset-0 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl blur opacity-20 group-hover:opacity-40 transition-opacity"></div>
                <div className="relative rounded-xl border border-purple-500/30 bg-black/70 p-6">
                  <div className="text-4xl mb-3">🧠</div>
                  <h4 className="text-lg font-bold text-purple-400 mb-2">Review 4</h4>
                  <p className="text-sm text-gray-400 mb-4">Future Phase</p>
                  <ul className="space-y-1 text-xs text-gray-500">
                    <li>○ LLM Synthesis</li>
                    <li>○ Report Gen</li>
                    <li>○ Insights</li>
                  </ul>
                </div>
              </div>

              {/* Production */}
              <div className="relative group">
                <div className="absolute inset-0 bg-gradient-to-r from-yellow-500 to-orange-500 rounded-xl blur opacity-20 group-hover:opacity-40 transition-opacity"></div>
                <div className="relative rounded-xl border border-yellow-500/30 bg-black/70 p-6">
                  <div className="text-4xl mb-3">🚀</div>
                  <h4 className="text-lg font-bold text-yellow-400 mb-2">Production</h4>
                  <p className="text-sm text-gray-400 mb-4">Enterprise</p>
                  <ul className="space-y-1 text-xs text-gray-500">
                    <li>○ Scaling</li>
                    <li>○ APIs</li>
                    <li>○ Deployment</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          {/* Tech Stack */}
          <div className="rounded-2xl border border-cyan-500/20 bg-gradient-to-br from-black/50 to-black/80 backdrop-blur-xl p-8">
            <h3 className="text-2xl font-black text-white mb-8 text-center">Powered By Advanced Technology</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="group cursor-pointer">
                <div className="rounded-xl border border-cyan-500/30 bg-black/50 p-6 group-hover:border-cyan-500/60 group-hover:bg-black/70 transition-all duration-300 text-center">
                  <div className="text-3xl mb-2">🐍</div>
                  <p className="font-bold text-cyan-400 text-sm">FastAPI</p>
                  <p className="text-xs text-gray-500">Backend</p>
                </div>
              </div>
              <div className="group cursor-pointer">
                <div className="rounded-xl border border-blue-500/30 bg-black/50 p-6 group-hover:border-blue-500/60 group-hover:bg-black/70 transition-all duration-300 text-center">
                  <div className="text-3xl mb-2">⚛️</div>
                  <p className="font-bold text-blue-400 text-sm">Next.js</p>
                  <p className="text-xs text-gray-500">Frontend</p>
                </div>
              </div>
              <div className="group cursor-pointer">
                <div className="rounded-xl border border-purple-500/30 bg-black/50 p-6 group-hover:border-purple-500/60 group-hover:bg-black/70 transition-all duration-300 text-center">
                  <div className="text-3xl mb-2">🤖</div>
                  <p className="font-bold text-purple-400 text-sm">Tesseract</p>
                  <p className="text-xs text-gray-500">OCR</p>
                </div>
              </div>
              <div className="group cursor-pointer">
                <div className="rounded-xl border border-pink-500/30 bg-black/50 p-6 group-hover:border-pink-500/60 group-hover:bg-black/70 transition-all duration-300 text-center">
                  <div className="text-3xl mb-2">👁️</div>
                  <p className="font-bold text-pink-400 text-sm">YOLOv8</p>
                  <p className="text-xs text-gray-500">Vision AI</p>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}