import ModuleCard from './ModuleCard'

// Stub: price valuation is Review 3 scope (XGBoost fair-value model). Nothing is estimated here.
export default function ValuationModule({ status }: { status?: string }) {
  return (
    <ModuleCard id="valuation" title="4 · Car price valuation" subtitle="Fair-value estimate from the vehicle record." badge="Coming in Review 3">
      <div className="p-4 rounded-lg border border-gray-600/40 bg-gray-800/40 text-gray-300 text-sm space-y-1">
        <p>Not implemented in this review — no price is estimated.</p>
        <p className="text-gray-500">
          Backend status: <span className="font-mono">{status ?? 'pending'}</span>. The vehicle JSON already reserves the
          <span className="font-mono"> valuation</span> section, so the XGBoost model can fill it later without changing the frontend contract.
        </p>
      </div>
    </ModuleCard>
  )
}
