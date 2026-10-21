import type { ReactNode } from 'react'

// Shared frame for each module section on the inspection page.
export default function ModuleCard({ id, title, subtitle, badge, children }: {
  id: string; title: string; subtitle: string; badge?: string; children: ReactNode
}) {
  return (
    <section id={id} className="scroll-mt-24 rounded-2xl border border-cyan-500/20 bg-gradient-to-br from-cyan-500/5 to-blue-500/5 p-6 md:p-8 space-y-6">
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <h2 className="text-2xl font-bold text-white">{title}</h2>
          <p className="text-gray-400 text-sm mt-1">{subtitle}</p>
        </div>
        {badge && <span className="text-xs px-3 py-1 rounded-full border border-gray-500/40 text-gray-300">{badge}</span>}
      </div>
      {children}
    </section>
  )
}

export const buttonCls =
  'px-5 py-2.5 rounded-lg font-semibold text-white bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 disabled:opacity-40 disabled:cursor-not-allowed'

export const errMsg = (e: unknown) => (e instanceof Error ? e.message : 'Something went wrong')

export function ErrorBox({ message }: { message: string | null }) {
  return message ? <div className="p-3 rounded-lg border border-red-500/40 bg-red-500/10 text-red-300 text-sm">{message}</div> : null
}
