interface StatCardProps {
  icon: string
  label: string
  value: string | number
}

export function StatCard({ icon, label, value }: StatCardProps) {
  return (
    <div
      className="flex flex-col items-center gap-1 p-3 bg-white rounded-lg border border-slate-200"
      aria-live="polite"
      aria-atomic="true"
    >
      <span className="text-xl" aria-hidden="true">{icon}</span>
      <span className="text-xs text-slate-500 text-center leading-tight">{label}</span>
      <span className="text-2xl font-bold text-slate-900">{value}</span>
    </div>
  )
}
