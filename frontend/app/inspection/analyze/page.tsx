import { redirect } from 'next/navigation'

// Old upload URL: everything now lives on /inspection.
export default function LegacyAnalyze() {
  redirect('/inspection')
}
