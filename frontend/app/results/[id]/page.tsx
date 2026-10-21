import { redirect } from 'next/navigation'

// Old results URL: everything now lives on /inspection.
export default function LegacyResults() {
  redirect('/inspection')
}
