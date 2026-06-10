import { Search } from 'lucide-react'
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
      <Search className="absolute left-3 size-4 text-muted-foreground pointer-events-none" />
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
