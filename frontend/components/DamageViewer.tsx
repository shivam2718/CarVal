'use client'
import { useState } from 'react'
import type { ImageResult } from '../types/vehicle'
import { annotatedImageUrl, originalImageUrl } from '../lib/api'

// Shows each uploaded image with YOLO boxes (drawn by the Vision Service) + a table of detections.
export default function DamageViewer({ inspectionId, results }: { inspectionId: string; results: ImageResult[] }) {
  const [showOriginal, setShowOriginal] = useState<Record<string, boolean>>({})

  if (!results.length) {
    return <p className="text-gray-400">No vision results yet. Upload car images and run the analysis.</p>
  }

  return (
    <div className="space-y-8">
      {results.map((r) => (
        <div key={r.image_id} className="rounded-xl border border-cyan-500/20 bg-gray-900/60 p-4">
          <div className="flex items-center justify-between mb-3">
            <p className="font-mono text-cyan-400 text-sm">{r.image_id}</p>
            <button
              className="text-xs px-3 py-1 rounded bg-gray-800 text-gray-300 hover:bg-gray-700"
              onClick={() => setShowOriginal((s) => ({ ...s, [r.image_id]: !s[r.image_id] }))}
            >
              {showOriginal[r.image_id] ? 'Show detections' : 'Show original'}
            </button>
          </div>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={showOriginal[r.image_id] ? originalImageUrl(inspectionId, r.image_id) : annotatedImageUrl(inspectionId, r.image_id)}
            alt={r.image_id}
            className="w-full max-h-[480px] object-contain rounded-lg bg-black"
          />
          {r.damages.length === 0 ? (
            <p className="text-green-300 text-sm mt-3">No damage detected in this image.</p>
          ) : (
            <table className="w-full text-sm mt-4 text-gray-200">
              <thead>
                <tr className="text-left text-gray-400 border-b border-gray-700">
                  <th className="py-2">ID</th><th>Type</th><th>Confidence</th><th>Severity</th><th>Box (x1,y1,x2,y2)</th>
                </tr>
              </thead>
              <tbody>
                {r.damages.map((d) => (
                  <tr key={d.damage_id} className="border-b border-gray-800">
                    <td className="py-2 font-mono">{d.damage_id}</td>
                    <td className="capitalize">{d.type}</td>
                    <td>{(d.confidence * 100).toFixed(1)}%</td>
                    <td className="capitalize">{d.severity ?? '-'}</td>
                    <td className="font-mono text-xs">{d.bbox.x1},{d.bbox.y1},{d.bbox.x2},{d.bbox.y2}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      ))}
    </div>
  )
}