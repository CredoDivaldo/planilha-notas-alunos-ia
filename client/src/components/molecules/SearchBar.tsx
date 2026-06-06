import { Input } from '@/components/ui/input'

interface SearchBarProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  className?: string
}

export function SearchBar({
  value,
  onChange,
  placeholder = 'Pesquisar…',
  className,
}: SearchBarProps) {
  return (
    <div className={['relative flex items-center', className].filter(Boolean).join(' ')}>
      <span className="absolute left-3 text-[#475569] pointer-events-none select-none text-sm">
        🔍
      </span>
      <Input
        type="search"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="pl-9 min-w-[280px]"
        aria-label={placeholder}
      />
    </div>
  )
}
