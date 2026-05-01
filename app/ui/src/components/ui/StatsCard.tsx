interface Props {
  title: string
  value: string | number
  subtitle?: string
  color?: 'navy' | 'gold' | 'green' | 'red'
}

const borders: Record<string, string> = {
  navy:  'border-l-navy-500',
  gold:  'border-l-gold-500',
  green: 'border-l-green-500',
  red:   'border-l-red-500',
}

export default function StatsCard({ title, value, subtitle, color = 'navy' }: Props) {
  return (
    <div className={`bg-white rounded-xl shadow-sm p-5 border-l-4 ${borders[color]}`}>
      <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">{title}</p>
      <p className="mt-1 text-3xl font-bold text-gray-900">{value}</p>
      {subtitle && <p className="mt-1 text-xs text-gray-400">{subtitle}</p>}
    </div>
  )
}
