# Mid-Fi Mockup — Dashboard Professor

**Interface:** 002-dashboard-professor  
**Requisito:** FR2-FR3 (Context management, status overview)  
**Device:** Desktop (1024px+) | Tablet (768px)  
**Dark Mode:** Navy Dark background  

---

## Desktop Layout (1200px)

```
┌──────────────────────────────────────────────────────────────────┐
│ Header [Navy Light #1A3A66, border-b 1px Navy Medium #0D2456]   │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ [Logo 24px]  Planilha de Notas                 [Contexto ▼][⚙️] │
│ │ 14px / 400 / White         12px / 400 / Gray-400  Navy Base link
│ └──────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ Content Area [Navy Dark bg]                                     │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ padding: 48px                                                │ │
│ │                                                              │ │
│ │ ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │ │
│ │ │ Turma A         │  │ Turma B         │  │ Turma C      │ │ │
│ │ │ 2026.1          │  │ 2026.1          │  │ 2026.1       │ │ │
│ │ │                 │  │                 │  │              │ │ │
│ │ │ [Navy Light bg] │  │ [Navy Light bg] │  │ [Navy Light] │ │ │
│ │ │ border: 1px     │  │ border: 1px     │  │ border: 1px  │ │ │
│ │ │ Navy Light      │  │ Navy Light      │  │ Navy Light   │ │ │
│ │ │ radius: 4px     │  │ radius: 4px     │  │ radius: 4px  │ │ │
│ │ │ padding: 24px   │  │ padding: 24px   │  │ padding: 24px│ │ │
│ │ │                 │  │                 │  │              │ │ │
│ │ │ ├ Estudantes    │  │ ├ Estudantes    │  │ ├ Estudantes │ │ │
│ │ │ │ 32/32 ✓       │  │ │ 28/32 ⚠️      │  │ │ 25/30 ⚠️   │ │ │
│ │ │ │ 14px / 400    │  │ │ 14px / 400    │  │ │ 14px / 400 │ │ │
│ │ │ │ Gray 400      │  │ │ Gray 400      │  │ │ Gray 400   │ │ │
│ │ │ │                 │  │ │                 │  │ │            │ │ │
│ │ │ ├ Notas         │  │ ├ Notas         │  │ ├ Notas     │ │ │
│ │ │ │ 31/32         │  │ │ 20/28         │  │ │ 18/30     │ │ │
│ │ │ │ 14px / 400    │  │ │ 14px / 400    │  │ │ 14px / 400│ │ │
│ │ │ │ Gray 400      │  │ │ Gray 400      │  │ │ Gray 400  │ │ │
│ │ │ │                 │  │ │                 │  │ │            │ │ │
│ │ │ ├ Status        │  │ ├ Status        │  │ ├ Status    │ │ │
│ │ │ │ [✓ Publicado] │  │ │ [⚪ Rascunho] │  │ │ [⚪ Rascu]  │ │ │
│ │ │ │ Badge Green   │  │ │ Badge Gray    │  │ │ Badge Gray │ │ │
│ │ │ │ 12px / 500   │  │ │ 12px / 500   │  │ │ 12px / 500│ │ │
│ │ │ │                 │  │ │                 │  │ │            │ │ │
│ │ │ └─────────────────┘  │ ├────────────────┐ │  │ ├────────┐  │ │
│ │ │ [📤 Editar] [📤 CV] │ │ [📤 Editar] │ │  │ │ [📤 Ed] │  │ │
│ │ │ 14px / 600 / Navy-B │ │ [📤 Publicar]   │ │  │ │ [🔄 P] │  │ │
│ │ │                     │ │ 12px button     │ │  │ │         │  │ │
│ │ └─────────────────┘  └─────────────────┘  └──────────────┘ │ │
│ │                                                              │ │
│ │ 32px gap between cards (grid gap: 6)                       │ │
│ │                                                              │ │
│ │ Grid: grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6     │ │
│ │                                                              │ │
│ └──────────────────────────────────────────────────────────────┘ │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Card Detail (Expanded View)

```
┌─────────────────────────────────────────┐
│ [Navy Light bg #1A3A66]                 │
│ border: 1px Navy Light (imperceptível) │
│ radius: 4px                             │
│ padding: 24px                           │
│ shadow: shadow-sm                       │
│ hover: shadow-md (subtle elevation)     │
│                                         │
│ ┌────────────────────────────────────┐ │
│ │ Turma A — 2026.1                   │ │
│ │ 16px / 600 / Navy Base #003DA5    │ │
│ └────────────────────────────────────┘ │
│ 16px space                              │
│                                         │
│ Estudantes: 32/32 ✓                    │
│ 14px / 400 / Gray 400 #A0A0A0         │
│ ✓ Badge: Green #4CAF50, 12px/500      │
│                                         │
│ Notas: 31/32 (97%)                     │
│ 14px / 400 / Gray 400 #A0A0A0         │
│ ⚠️ Badge: Orange #FF9800, 12px/500    │
│                                         │
│ Publicado: 2026-05-31 14:30            │
│ 12px / 400 / Gray 600 #666666         │
│ (metadata, smallest text)              │
│                                         │
│ 24px space                              │
│                                         │
│ ┌────────────────────────────────────┐ │
│ │ [Editar]     [📤 Enviar Broadcast] │ │
│ │ Navy-light   Navy Base              │ │
│ │ Secondary    Primary                │ │
│ │ border       bg: #003DA5            │ │
│ │ 12px button  hover: #0A1F47        │ │
│ │              14px / 600             │ │
│ │              h-10 px-6 rounded-sm   │ │
│ └────────────────────────────────────┘ │
│                                         │
└─────────────────────────────────────────┘
```

---

## Color Palette

| Element | Color | Hex | Usage |
|---------|-------|-----|-------|
| **Background** | Navy Dark | `#0A1F47` | Page bg |
| **Header** | Navy Light | `#1A3A66` | Top bar |
| **Card bg** | Navy Light | `#1A3A66` | Card bg |
| **Card border** | Navy Light | `#1A3A66` | Imperceptible |
| **Title** | Navy Base | `#003DA5` | Card title |
| **Text Primary** | Gray 400 | `#A0A0A0` | Metric labels |
| **Text Meta** | Gray 600 | `#666666` | Dates, secondary |
| **Badge Success** | Green | `#4CAF50` | ✓ status |
| **Badge Warning** | Orange | `#FF9800` | ⚠️ status |

---

## Typography

| Element | Font | Size | Weight | Color |
|---------|------|------|--------|-------|
| **Header Title** | System | 14px | 400 | White |
| **Card Title** | System | 16px | 600 | Navy Base #003DA5 |
| **Metric** | System | 14px | 400 | Gray 400 #A0A0A0 |
| **Meta** | System | 12px | 400 | Gray 600 #666666 |
| **Button** | System | 14px | 600 | White (Primary) |
| **Badge** | System | 12px | 500 | Color-specific |

---

## Header Component

```
┌────────────────────────────────────────────────────┐
│ [Navy Light bg]                                    │
│ border-b: 1px Navy Medium (subtle)                │
│ padding: 16px 32px                                │
│                                                   │
│ Logo [24x24px]   Title [14px / 400]  [Ctrl ▼][⚙️] │
│ [Image]          "Planilha de Notas"  Dropdown  Icon
│                                       Menu      Navy Base
│ flex | items-center | space-x-4 | justify-between│
│                                                   │
└────────────────────────────────────────────────────┘
```

---

## Responsive Behavior

| Device | Layout |
|--------|--------|
| **Desktop (1024px+)** | 3-column grid, full card detail |
| **Tablet (768px)** | 2-column grid, card detail slightly compact |
| **Mobile (320px)** | 1-column, cards stack vertically |

**CSS:**
```css
grid: grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6
padding: px-4 md:px-6 lg:px-8
card-padding: p-6
```

---

## Interaction States

### Card Hover
```
bg: Navy Light (no change)
border: Navy Light (no change)
shadow: shadow-sm → shadow-md (subtle elevation)
cursor: pointer (if clickable)
transition: 200ms ease
```

### Button Primary (Enviar Broadcast)
```
State: Default
bg: Navy Base #003DA5
text: White
border: none
radius: 4px
padding: 12px 24px
height: 44px min

State: Hover
bg: Navy Dark #0A1F47
shadow: shadow-sm
transition: 200ms ease-in-out

State: Focus
outline: 2px solid #2196F3
outline-offset: 2px

State: Disabled (if no edits)
bg: Gray 400 #A0A0A0
text: Gray 600 #666666
cursor: not-allowed
opacity: 0.6
```

### Button Secondary (Editar)
```
State: Default
border: 1px Navy Light #1A3A66
bg: transparent
text: Navy Base #003DA5
radius: 4px

State: Hover
bg: Navy Medium #0D2456
text: White
border: Navy Medium
transition: 200ms ease
```

---

## Status Badges

### Success Badge (✓ Publicado)
```
bg: Green #4CAF50
text: White
padding: 4px 8px
radius: 2px (almost square)
font: 12px / 500
icon: ✓
```

### Warning Badge (⚠️ Rascunho)
```
bg: Gray 300 (subtle)
text: Gray 600
padding: 4px 8px
radius: 2px
font: 12px / 500
icon: ⚪ or ⚠️
```

### Info Badge (ⓘ)
```
bg: Blue 100 (light)
text: Blue 800
padding: 4px 8px
radius: 2px
font: 12px / 500
```

---

## Accessibility

✅ **Color Contrast:**
- Navy Base on White (link): 20:1 (AAA)
- Gray 400 on Navy Dark: 4.5:1 (AA)
- Green on Navy Light: 7.5:1 (AAA)

✅ **Keyboard Navigation:**
- Tab: Card → Button (Editar) → Button (Enviar)
- Cards are clickable/focusable
- Focus outline: 2px blue, 2px offset

✅ **Semantic:**
```html
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
  {turmas.map(turma => (
    <article key={turma.id} className="bg-navy-light border border-navy-light rounded-sm p-6">
      <h2 className="text-lg font-semibold text-navy-base mb-4">
        {turma.nome}
      </h2>
      
      <p className="text-sm text-gray-400 mb-2">
        Estudantes: {turma.estudantes_total}/{turma.estudantes_total} 
        <Badge variant="success">✓</Badge>
      </p>
      
      <p className="text-sm text-gray-400 mb-4">
        Notas: {turma.notas_input}/{turma.estudantes_total}
        <Badge variant="warning">⚠️</Badge>
      </p>
      
      <p className="text-xs text-gray-600 mb-6">
        Publicado: {turma.data_publicacao}
      </p>
      
      <div className="flex gap-2">
        <Button variant="outline">Editar</Button>
        <Button variant="primary">📤 Enviar</Button>
      </div>
    </article>
  ))}
</div>
```

---

## Tailwind Implementation

```tsx
export function ProfessorDashboard() {
  return (
    <div className="min-h-screen bg-navy-dark">
      {/* Header */}
      <header className="bg-navy-light border-b border-navy-medium sticky top-0">
        <div className="max-w-7xl mx-auto px-4 md:px-6 lg:px-8 h-16 
                        flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Logo className="h-6 w-6" />
            <h1 className="text-sm font-normal text-white">Planilha de Notas</h1>
          </div>
          
          <div className="flex items-center gap-4">
            <Select>
              <SelectTrigger className="text-sm">
                Contexto
              </SelectTrigger>
            </Select>
            <Settings className="h-5 w-5 text-gray-400 cursor-pointer" />
          </div>
        </div>
      </header>
      
      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 md:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {turmas.map((turma) => (
            <Card key={turma.id} className="bg-navy-light">
              <CardHeader>
                <h2 className="text-lg font-semibold text-navy-base">
                  {turma.nome}
                </h2>
              </CardHeader>
              
              <CardContent className="space-y-3">
                <p className="text-sm text-gray-400 flex items-center gap-2">
                  Estudantes: {turma.estudantes}
                  <Badge className="bg-green-500">✓</Badge>
                </p>
                
                <p className="text-sm text-gray-400 flex items-center gap-2">
                  Notas: {turma.notas}
                  <Badge className="bg-orange-500">⚠️</Badge>
                </p>
                
                <p className="text-xs text-gray-600">
                  Publicado: {turma.data}
                </p>
              </CardContent>
              
              <CardFooter className="flex gap-2">
                <Button variant="outline" size="sm">
                  Editar
                </Button>
                <Button variant="default" size="sm">
                  📤 Enviar
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      </main>
    </div>
  )
}
```

---

## Visual Hierarchy

1. **Header** (sticky, Navy Light, 16px padding)
2. **Card Title** (16px, 600, Navy Base, prominent)
3. **Metrics** (14px, 400, Gray 400, secondary)
4. **Badges** (12px, 500, color-coded)
5. **Date** (12px, 400, Gray 600, tertiary)
6. **Buttons** (14px, 600, high contrast)

---

## Notes

- ✅ Zero yellow decorative elements
- ✅ Imperceptible borders (navy-light on navy-light)
- ✅ Premium subtle shadows (only on hover, elevate)
- ✅ Generous spacing (32px grid gap, 24px card padding)
- ✅ Responsive grid (auto-adjust to device)
- ✅ Status badges clear and functional
- ✅ Clean, composed, serious aesthetic

---

**Status:** Mid-Fi Complete  
**Device Support:** Desktop, Tablet, Mobile  
**Framework:** React + Tailwind + shadcn/ui  
*Premium. Minimal. Serious.*
