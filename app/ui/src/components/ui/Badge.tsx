import clsx from 'clsx'

type Color = 'gray' | 'blue' | 'green' | 'yellow' | 'red' | 'purple' | 'gold' | 'zen'

const styles: Record<Color, string> = {
  gray:   'bg-gray-100 text-gray-700',
  blue:   'bg-blue-50 text-blue-700 ring-1 ring-blue-200',
  green:  'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200',
  yellow: 'bg-amber-50 text-amber-700 ring-1 ring-amber-200',
  red:    'bg-rose-50 text-rose-700 ring-1 ring-rose-200',
  purple: 'bg-purple-50 text-purple-700 ring-1 ring-purple-200',
  gold:   'bg-amber-50 text-amber-700 ring-1 ring-amber-200',
  zen:    'bg-zen-50 text-zen-700 ring-1 ring-zen-200',
}

interface Props {
  label: string
  color?: Color
  className?: string
}

export default function Badge({ label, color = 'gray', className }: Props) {
  return (
    <span className={clsx('inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold', styles[color], className)}>
      {label}
    </span>
  )
}
