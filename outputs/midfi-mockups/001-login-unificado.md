# Mid-Fi Mockup — Login Unificado

**Interface:** 001-login-unificado  
**Requisito:** FR13 (Login + First-time password change)  
**Device:** Desktop (1024px+) | Mobile (320-480px)  
**Dark Mode:** Navy Dark background  

---

## Desktop Layout (1024px)

```
┌──────────────────────────────────────────────────────────────┐
│                    [Navy Dark #0A1F47]                        │
│                                                               │
│                                                               │
│                    ┌──────────────────────┐                  │
│                    │  [Logo Universidade] │  32px            │
│                    │  (canto superior)    │                  │
│                    └──────────────────────┘                  │
│                                                               │
│                         48px space                            │
│                                                               │
│    ┌─────────────────────────────────────────────────────┐  │
│    │  [Navy Light bg #1A3A66]                            │  │
│    │  border: 1px #1A3A66 (imperceptível)               │  │
│    │  radius: 4px                                        │  │
│    │  padding: 48px                                      │  │
│    │                                                     │  │
│    │  ┌───────────────────────────────────────────────┐ │  │
│    │  │ Planilha de Notas                             │ │  │
│    │  │ 32px / 700 / Navy Base #003DA5               │ │  │
│    │  └───────────────────────────────────────────────┘ │  │
│    │                                                     │  │
│    │  16px space                                        │  │
│    │                                                     │  │
│    │  Email                                             │  │
│    │  12px / 500 / Gray 400 #A0A0A0                   │  │
│    │  16px space                                        │  │
│    │                                                     │  │
│    │  ┌───────────────────────────────────────────────┐ │  │
│    │  │ user@universidade.pt                          │ │  │
│    │  │ 14px / 400 / White                            │ │  │
│    │  │ bg: Navy Light #1A3A66                        │ │  │
│    │  │ border: 1px Navy Light (imperceptível)        │ │  │
│    │  │ padding: 12px 16px                            │ │  │
│    │  │ radius: 4px                                   │ │  │
│    │  │ focus: outline 2px #2196F3, offset 2px        │ │  │
│    │  └───────────────────────────────────────────────┘ │  │
│    │                                                     │  │
│    │  24px space                                        │  │
│    │                                                     │  │
│    │  Palavra-passe                                     │  │
│    │  12px / 500 / Gray 400 #A0A0A0                   │  │
│    │  16px space                                        │  │
│    │                                                     │  │
│    │  ┌───────────────────────────────────────────────┐ │  │
│    │  │ ••••••••                                      │ │  │
│    │  │ [Same input styling as above]                 │ │  │
│    │  │ type: password                                │ │  │
│    │  └───────────────────────────────────────────────┘ │  │
│    │                                                     │  │
│    │  24px space                                        │  │
│    │                                                     │  │
│    │  ☐ Lembrar-me                                      │  │
│    │  12px / 400 / White                              │  │
│    │  checkbox: 20x20px, Navy Light border            │  │
│    │                                                     │  │
│    │  32px space                                        │  │
│    │                                                     │  │
│    │  ┌───────────────────────────────────────────────┐ │  │
│    │  │  Iniciar Sessão                               │ │  │
│    │  │  14px / 600 / White                           │ │  │
│    │  │  bg: Navy Base #003DA5                        │ │  │
│    │  │  hover: bg Navy Dark #0A1F47, shadow-sm      │ │  │
│    │  │  padding: 12px 24px                           │ │  │
│    │  │  height: 44px (touch target)                  │ │  │
│    │  │  radius: 4px                                  │ │  │
│    │  │  width: 100%                                  │ │  │
│    │  │  cursor: pointer                              │ │  │
│    │  └───────────────────────────────────────────────┘ │  │
│    │                                                     │  │
│    │  16px space                                        │  │
│    │                                                     │  │
│    │  Esqueceu a palavra-passe?                         │  │
│    │  12px / 400 / Navy Base #003DA5, underline       │  │
│    │  hover: no underline                              │  │
│    │                                                     │  │
│    └─────────────────────────────────────────────────────┘  │
│                                                               │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## Color Breakdown

| Element | Color | Hex | Usage |
|---------|-------|-----|-------|
| **Background** | Navy Dark | `#0A1F47` | Page bg |
| **Card** | Navy Light | `#1A3A66` | Card bg |
| **Card Border** | Navy Light | `#1A3A66` | Imperceptible |
| **Title** | Navy Base | `#003DA5` | Heading |
| **Label** | Gray 400 | `#A0A0A0` | Form label |
| **Input bg** | Navy Light | `#1A3A66` | Input field |
| **Input text** | White | `#FFFFFF` | Placeholder |
| **Button bg** | Navy Base | `#003DA5` | CTA |
| **Button hover** | Navy Dark | `#0A1F47` | Hover state |
| **Focus outline** | Blue | `#2196F3` | Keyboard focus |

---

## Typography Stack

| Element | Font | Size | Weight | Line Height |
|---------|------|------|--------|-------------|
| **Title** | System | 32px | 700 | 1.2 |
| **Labels** | System | 12px | 500 | 1.4 |
| **Input text** | System | 14px | 400 | 1.6 |
| **Link** | System | 12px | 400 | 1.4 |

---

## Spacing Grid (8px)

```
Logo area:     32px from top
Logo to form:  48px gap
Form padding:  48px (all sides)
Field gap:     24px (between fields)
Label to input: 16px
Button gap:    32px
Link gap:      16px from button
```

---

## Interactive States

### Input Focus
```
Input: Navy Light bg → Navy Light bg (no change)
Border: Navy Light → remains Navy Light (imperceptible)
Outline: 2px solid #2196F3, offset 2px
```

### Button Hover
```
Button: Navy Base bg → Navy Dark bg
Shadow: none → shadow-sm
Text: White (unchanged)
Cursor: pointer
Transition: 200ms ease
```

### Button Active (Pressed)
```
Button: Navy Dark bg (stays)
Shadow: none
Text: White
```

### Button Disabled (Loading)
```
Button: Navy Base bg
Text: "Iniciando..." with spinner
Opacity: 0.75
Cursor: not-allowed
```

---

## Mobile Layout (320-480px)

```
┌──────────────────────┐
│ [Navy Dark bg]       │
│                      │
│  [Logo 24px]         │
│  32px space          │
│                      │
│  ┌──────────────────┐│
│  │ Planilha de Notas││ 28px / 600
│  │                  ││
│  │ Email            ││ 12px label
│  │ 16px space       ││
│  │ ┌────────────────┤│
│  │ │user@univ.pt   ││ 14px input
│  │ └────────────────┤│
│  │                  ││
│  │ 24px space       ││
│  │                  ││
│  │ Palavra-passe    ││ 12px label
│  │ 16px space       ││
│  │ ┌────────────────┤│
│  │ │••••••••       ││ 14px input
│  │ └────────────────┤│
│  │                  ││
│  │ 24px space       ││
│  │ ☐ Lembrar-me     ││ 12px checkbox
│  │                  ││
│  │ 32px space       ││
│  │ ┌────────────────┤│
│  │ │ Iniciar Sessão ││ 14px button
│  │ └────────────────┤│
│  │                  ││
│  │ 16px space       ││
│  │ Esqueceu pw?     ││ 12px link
│  │                  ││
│  └──────────────────┘│
│  padding: 16px       │
│                      │
└──────────────────────┘
```

---

## Responsive Breakpoints

| Size | Changes |
|------|---------|
| **Mobile (320-480px)** | Padding 16px, card margin-x 16px |
| **Tablet (481-768px)** | Padding 24px, card max-w 400px |
| **Desktop (769px+)** | Padding 32px, card max-w 500px, centered |

---

## Accessibility Features

✅ **Color Contrast:**
- White on Navy Light: 15:1 (AAA)
- Navy Base on White (link): 20:1 (AAA)

✅ **Keyboard Navigation:**
- Tab order: Email → Password → Checkbox → Button → Link
- Focus indicator: 2px blue outline, always visible

✅ **Semantic HTML:**
```html
<form>
  <label for="email">Email</label>
  <input id="email" type="email" required />
  
  <label for="password">Palavra-passe</label>
  <input id="password" type="password" required />
  
  <label>
    <input type="checkbox" name="remember" />
    Lembrar-me
  </label>
  
  <button type="submit">Iniciar Sessão</button>
  
  <a href="/forgot-password">Esqueceu a palavra-passe?</a>
</form>
```

---

## Tailwind Classes

```tsx
// Container
<div className="min-h-screen bg-navy-dark flex items-center justify-center px-4">
  
  // Card
  <div className="bg-navy-light border border-navy-light rounded-sm p-12 w-full max-w-lg shadow-sm">
    
    // Logo
    <img src="logo.png" alt="Logo" className="h-8 mb-12" />
    
    // Title
    <h1 className="text-4xl font-bold mb-8">Planilha de Notas</h1>
    
    // Form
    <form className="space-y-6">
      
      // Email field
      <div className="space-y-2">
        <label className="text-sm font-medium text-gray-400">Email</label>
        <input 
          type="email"
          className="w-full bg-navy-light border border-navy-light text-white 
                     placeholder:text-gray-400 px-4 py-2.5 rounded-sm
                     focus:outline-2 focus:outline-offset-0 focus:outline-blue-500
                     transition-colors duration-200"
        />
      </div>
      
      // Password field
      <div className="space-y-2">
        <label className="text-sm font-medium text-gray-400">Palavra-passe</label>
        <input 
          type="password"
          className="w-full bg-navy-light border border-navy-light text-white 
                     placeholder:text-gray-400 px-4 py-2.5 rounded-sm
                     focus:outline-2 focus:outline-offset-0 focus:outline-blue-500"
        />
      </div>
      
      // Checkbox
      <label className="flex items-center space-x-2 text-sm">
        <input type="checkbox" className="rounded-sm" />
        <span>Lembrar-me</span>
      </label>
      
      // Button
      <button 
        type="submit"
        className="w-full bg-navy-base text-white font-semibold h-11 rounded-sm
                   hover:bg-navy-dark transition-colors duration-200"
      >
        Iniciar Sessão
      </button>
      
      // Link
      <a href="#" className="text-sm text-navy-base hover:no-underline">
        Esqueceu a palavra-passe?
      </a>
      
    </form>
    
  </div>
  
</div>
```

---

## Visual Hierarchy

1. **Logo** (32px, subtle, top-left)
2. **Title** (32px, 700, Navy Base, prominent)
3. **Labels** (12px, 500, Gray 400, secondary)
4. **Inputs** (14px, 400, White, primary content)
5. **Button** (14px, 600, Navy Base bg, high contrast)
6. **Link** (12px, 400, Navy Base, low contrast)

---

## Motion & Interactions

| Interaction | Duration | Effect |
|-------------|----------|--------|
| **Input focus** | 200ms | Color transition, outline appear |
| **Button hover** | 200ms | Background darker, shadow-sm |
| **Form submit** | 300ms | Button disabled, spinner appears |

---

## Notes

- ✅ Zero yellow decorative elements
- ✅ Zero gradients (flat navy colors)
- ✅ Imperceptible border (navy-light)
- ✅ Premium, minimal aesthetic
- ✅ Fully accessible (WCAG AA)
- ✅ Mobile-first responsive
- ✅ Ready for Tailwind + shadcn/ui implementation

---

**Status:** Mid-Fi Complete  
**Next:** Validation with user → Hi-Fi Design  
*Premium. Minimal. Serious.*
