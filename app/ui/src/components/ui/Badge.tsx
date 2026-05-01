import clsx from 'clsx'

type Color = 'gray' | 'blue' | 'green' | 'yellow' | 'red' | 'purple' | 'gold'

const styles: Record<Color, string> = {
  gray:   'bg-gray-100 text-gray-700',
  blue:   'bg-blue-100 text-blue-700',
  green:  'bg-green-100 text-green-700',
  yellow: 'bg-yellow-100 text-yellow-700',
  red:    'bg-red-100 text-red-700',
  purple: 'bg-purple-100 text-purple-700',
  gold:   'bg-amber-100 text-amber-700',
}

interface Props {
  label: string
  color?: Color
  className?: string
}

export default function Badge({ label, color = 'gray', className }: Props) {
  return (
    <span className={clsx('inline-flex px-2 py-0.5 rounded-full text-xs font-semibold', styles[color], className)}>
      {label}
    </span>
  )
}
