type Color = 'navy' | 'gold' | 'green' | 'red' | 'zen' | 'purple'

const borders: Record<Color, string> = {
  navy:   'border-l-zen-500',
  gold:   'border-l-amber-400',
  green:  'border-l-emerald-500',
  red:    'border-l-rose-500',
  zen:    'border-l-zen-500',
  purple: 'border-l-purple-500',
}

const valueColors: Record<Color, string> = {
  navy:   'text-zen-700',
  gold:   'text-amber-600',
  green:  'text-emerald-700',
  red:    'text-rose-700',
  zen:    'text-zen-700',
  purple: 'text-purple-700',
}

interface Props {
  title: string
  value: string | number
  subtitle?: string
  color?: Color
  delta?: string
}

export default function StatsCard({ title, value, subtitle, color = 'navy', delta }: Props) {
  return (
    <div className={`card p-5 border-l-4 ${borders[color]}`}>
      <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">{title}</p>
      <p className={`mt-1 text-3xl font-bold ${valueColors[color]}`}>{value}</p>
      {subtitle && <p className="mt-1 text-xs text-gray-400">{subtitle}</p>}
      {delta && <p className="mt-1 text-xs font-semibold text-emerald-600">{delta}</p>}
    </div>
  )
}
