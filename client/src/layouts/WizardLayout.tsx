// WizardLayout — full-page layout for wizard/multi-step pages (T06 in inventory)
// Used by PublishPage (/publicar)

import type { ReactNode } from 'react'
import { AppHeader } from '@/components/organisms/AppHeader'

interface WizardLayoutProps {
  children: ReactNode
}

export function WizardLayout({ children }: WizardLayoutProps) {
  return (
    <div className="min-h-screen bg-background flex flex-col">
      <AppHeader activeTab="publicar" />
      <main className="flex-1 w-full max-w-[960px] mx-auto px-4 sm:px-6 py-6">
        {children}
      </main>
    </div>
  )
}
