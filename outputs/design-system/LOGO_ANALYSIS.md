# Análise Visual do Logotipo — Universidade Lusíada

**Documento de Pesquisa Visual & Brainstorm Criativo**

---

## 1. Análise Visual do Logotipo

### 1.1 Estrutura Geométrica

```
┌─────────────────────────────┐
│      Círculo Amarelo        │
│   ┌───────────────────────┐ │
│   │  ╔═════════════════╗  │ │
│   │  ║  Mapa Portugal  ║  │ │
│   │  ║  (branco)       ║  │ │
│   │  ╚═════════════════╝  │ │
│   └───────────────────────┘ │
│   Azul Escuro (marco)       │
└─────────────────────────────┘
```

**Camadas:**
1. **Círculo amarelo** — Forma primária, vibrante, soleado
2. **Marco azul** — Quadrado com distorções dinâmicas (tilt)
3. **Linhas diagonais dashed** — Movimento, ritmo
4. **Mapa de Portugal** — Identidade cultural, branco
5. **Texto circular** — "UNIVERSIDADE LUSÍADA • SOLUCETOMIBUS"

### 1.2 Paleta de Cores Atual

| Elemento | Cor | Hex Aproximado | RGB | Característica |
|----------|-----|---|---|---|
| **Azul Escuro** | Navy Blue | `#003DA5` | 0, 61, 165 | Profundo, confiável, institucional |
| **Amarelo** | Bright Yellow | `#FFD100` | 255, 209, 0 | Vibrante, soleado, energético |
| **Branco** | White | `#FFFFFF` | 255, 255, 255 | Contraste, mapa interior |
| **Texto** | Navy | `#003DA5` | Mesmo azul | Coerência cromática |

### 1.3 Elementos Característicos (Features)

**Geométricos:**
- ✅ Círculo (forma primária, completude)
- ✅ Quadrado rotacionado/distorcido (dinamismo, movimento)
- ✅ Linhas diagonais dashes (ritmo, energia)
- ✅ Simetria com assimetria (equilíbrio criativo)

**Visuais:**
- ✅ Mapa de Portugal (identidade regional, local)
- ✅ Alto contraste azul ↔ amarelo (legibilidade)
- ✅ Branco como elemento neutro (respiro visual)
- ✅ Formato circular (universalidade, completude)

**Semântica:**
- ✅ Institucional (universidade)
- ✅ Português (mapa)
- ✅ Moderno-clássico (mistura de estilos)
- ✅ Confiável (cores sóbrias + vibrante amarelo = equilíbrio)

### 1.4 Tipografia (A EVITAR)

- **Atual:** Serif tradicional (tipo "Times New Roman")
- **Problema:** Pesada, formal, datada
- **Solução:** Sans-serif moderno (Roboto, Inter, SF Pro, Segoe UI)

---

## 2. Extração de Características para Design System

### 2.1 Cores Extraídas

#### Cores Primárias (Dark Mode First)

| Nome | Cor | Hex | RGB | Luminância | Uso |
|------|-----|-----|-----|------------|-----|
| **Navy Primary** | Azul Escuro | `#003DA5` | 0, 61, 165 | 12% | Backgrounds, cards, text (light mode) |
| **Sunny Accent** | Amarelo | `#FFD100` | 255, 209, 0 | 87% | Highlights, CTAs, accents |
| **Navy Dark** | Azul Muito Escuro | `#0A1F47` | 10, 31, 71 | 5% | Backgrounds principal (dark mode) |
| **Navy Light** | Azul Claro | `#1A3A66` | 26, 58, 102 | 8% | Cards, sections (dark mode) |
| **Neutral Light** | Cinzento Claro | `#E8E8E8` | 232, 232, 232 | 92% | Text on dark, light mode bg |
| **Neutral Dark** | Cinzento Escuro | `#333333` | 51, 51, 51 | 13% | Secondary text, light mode |

#### Paleta de Graus (Dark Mode)

```
Navy Dark    #0A1F47   ← Background principal
Navy Base    #0D2456   ← Slight elevation
Navy Light   #1A3A66   ← Cards, sections
Navy Medium  #003DA5   ← Primary element
Sunny        #FFD100   ← Accent, 100%
Sunny Light  #FFE547   ← Hover, lighter
Sunny Dark   #E8BA00   ← Pressed, darker
Gray 200     #E8E8E8   ← Text on dark
Gray 600     #666666   ← Secondary text
```

### 2.2 Elementos Visuais Reutilizáveis

#### A. Linhas Diagonais/Dashed

**Uso:** Divisores, padrões de fundo, movimento

```
Padrão horizontal:
╌ ╌ ╌ ╌ ╌ ╌ ╌ ╌ ╌ ╌  (dashes)
━━━━━━━━━━━━━━━━━━━━  (solid)

Padrão diagonal:
  ╱ ╱ ╱ ╱ ╱ ╱ ╱   (45° dashes)
```

**Aplicações:**
- Divisor entre secções (amarelo em fundo escuro)
- Padrão de fundo sutil (dashes cinzentas, 5% opacity)
- Linha decorativa em cards (amarelo, 2px)
- Border-bottom para headings

#### B. Quadrados com Rotação/Distorção

**Uso:** Frames para conteúdo importante, cards de destaque

```
Padrão normal:
┌─────────────┐
│ Conteúdo    │
└─────────────┘

Padrão rotacionado (2-3°):
  ┌─────────────┐
  │ Conteúdo    │
  └─────────────┘

Padrão com "tilt":
┌─────────────┐
│ Conteúdo    │
└─────────────┘  ← um canto um pouco mais elevado
```

#### C. Círculos Concêntricos

**Uso:** Badges, status indicators, avatars, accents

```
┌─────────────┐
│   ◯ ◯ ◯     │  ← Círculos concêntricos
│   ◯ ✓ ◯     │
│   ◯ ◯ ◯     │
└─────────────┘
```

#### D. Simetria Dinâmica

**Uso:** Layouts, iconografia, padrões

```
Simétrico:          Dinamicamente assimétrico:
▌ ▌ ▌               ▌ ▌ ▌
▌ ▌ ▌        →      ▌  ▌
▌ ▌ ▌                ▌
```

---

## 3. Brainstorm de Ideias Criativas

### 3.1 Conceito 1: "Subtle Geometry"

**Filosofia:** Elementos do logotipo integrados de forma sutil, não óbvia

**Aplicação:**
- Background: Gradiente azul escuro Navy Dark → Navy Medium (0° → 135°)
- Padrão sutil: Dashes diagonais (2% opacity) ao fundo
- Accent color: Amarelo para CTAs, badges, highlights
- Quadrados arredondados em vez de circulares (modernização)
- Linhas diagonais como separadores entre secções

**Exemplo:**
```
┌──────────────────────────────────────┐
│  ╌ ╌ ╌ ╌ ╌ ╌ ╌ ╌ ╌ ╌ ╌ ╌ ╌ ╌ ╌    │
│  (Padrão background, muito sutil)     │
│                                      │
│  ╔══════════════════════════════╗   │
│  ║  Titulo com Amarelo          ║   │
│  ╠──────────────────────────────╣   │
│  ║  Conteúdo em branco/cinzento ║   │
│  ╚══════════════════════════════╝   │
│        ━━ ━━ ━━ ━━ ━━           │
│     (Separador amarelo dashed)       │
└──────────────────────────────────────┘
```

### 3.2 Conceito 2: "Accent Frames"

**Filosofia:** Quadrados com tilt leve como frames para conteúdo importante

**Aplicação:**
- Cards principais: Quadrado com rotação 1-2° (sutil)
- Border: Amarelo 2px (lado esquerdo ou superior)
- Fundo: Navy Light com gradient
- Texto: Branco/cinzento claro

**Exemplo:**
```
┌─────────────────────────────┐
│ [Amarelo 2px esquerda]      │
│                             │
│  Contexto: Turma A 2026.1  │
│  Estudantes: 32/32 ✓       │
│  Notas: 31/32 (97%)        │
│                             │
└─────────────────────────────┘  (tilt: 1.5°)
```

### 3.3 Conceito 3: "Gradient Depth"

**Filosofia:** Usar gradientes suaves para profundidade, mantendo Navy + Amarelo

**Aplicação:**
- Background primário: Navy Dark (#0A1F47)
- Gradient secondary: Navy Dark → Navy Base (vertical, 45°)
- Cards: Navy Light com overlay gradient
- Hover effect: Subtle amarelo glow (0.5s transition)

**Exemplo:**
```
Background:
▓▓▓▓▓▓▓▓  ← Navy Dark
▓▓▓▓▓▓░░
▓▓▓▓░░░░
▓▓░░░░░░  ← Navy Medium
```

### 3.4 Conceito 4: "Geometric Accents"

**Filosofia:** Usar círculos concêntricos, linhas, quadrados como micro-elementos

**Aplicação:**
- Badges: Círculo concêntrico com centro amarelo
- Icons: Linhas diagonais para movimento (like logo arrows)
- Separators: Dashed lines amarelas (rotacionadas, variadas)
- Corners: Pequenos quadrados rotacionados (accent)

**Exemplo Badge:**
```
┌───────────┐
│  ◯ ✓ ◯   │  ← Círculo concêntrico
│  ◯ ✓ ◯   │
│  ◯ ◯ ◯   │
│ Sucesso  │
└───────────┘
```

### 3.5 Conceito 5: "Minimal Modern" (RECOMENDADO)

**Filosofia:** Extremamente moderno, dark mode native, minimalista com accents coloridos

**Aplicação:**
- Background: Navy Dark (#0A1F47) — flat, no pattern
- Typography: Sans-serif clean (Inter, Roboto, SF Pro)
- Accents: Amarelo (#FFD100) para CTAs, warnings, important
- Linhas: Apenas onde necessário (amarelo 2px dashed para dividers)
- Espaço branco: Generoso, respiração visual
- Cards: Navy Light (#1A3A66) com 1px border amarelo topo

**Exemplo:**
```
┌──────────────────────────────────────┐
│  Planilha de Notas                   │ ← Branco, 32px
│  ━━ ━━ ━━ ━━ ━━ ━━ ━━ ━━          │ ← Amarelo dashed
│                                      │
│  ┌──────────────────────────────┐   │
│  │ Contexto: Turma A           │   │
│  ├──────────────────────────────┤   │
│  │ Estudantes: 32/32           │   │
│  │ Notas: 31/32                │   │
│  │ [🔘 Publicar]               │   │ ← Amarelo button
│  └──────────────────────────────┘   │
│                                      │
└──────────────────────────────────────┘
```

---

## 4. Proposta de Design System v2 (Dark Mode First)

### 4.1 Paleta de Cores Modernizada

#### Primária

```css
--color-primary: #003DA5;           /* Navy Base (from logo) */
--color-primary-dark: #0A1F47;      /* Navy Dark (dark mode bg) */
--color-primary-light: #1A3A66;     /* Navy Light (cards) */
--color-primary-lighter: #2A5099;   /* Navy Lighter (hover) */

--color-accent: #FFD100;            /* Sunny Yellow (from logo) */
--color-accent-dark: #E8BA00;       /* Sunny Dark (hover) */
--color-accent-light: #FFE547;      /* Sunny Light (glow) */
```

#### Semântica

```css
--color-success: #4CAF50;           /* Green (not in logo, but needed) */
--color-warning: #FF9800;           /* Orange (not in logo, but needed) */
--color-error: #F44336;             /* Red (not in logo, but needed) */
--color-info: #2196F3;              /* Blue (lighter than primary) */
```

#### Neutros (Dark Mode)

```css
--color-bg: #0A1F47;                /* Navy Dark (main background) */
--color-bg-secondary: #0D2456;      /* Navy Dark-er (slight elevation) */
--color-bg-tertiary: #1A3A66;       /* Navy Light (cards, sections) */
--color-bg-inverted: #F5F5F5;       /* Light gray (light mode fallback) */

--color-text: #FFFFFF;              /* White (primary text on dark) */
--color-text-secondary: #B0B0B0;    /* Gray (secondary text) */
--color-text-hint: #696969;         /* Dark gray (hints, captions) */
--color-text-inverted: #0A1F47;     /* Navy (text on light) */

--color-border: #2A3A5A;            /* Navy Medium (borders) */
--color-border-accent: #FFD100;     /* Sunny (accent borders) */
```

### 4.2 Elementos Visuais de Assinatura

#### Padrão 1: Linha Diagonal Dashed (Separador)

```css
.divider-accent {
  border-top: 2px dashed #FFD100;
  opacity: 1;           /* Full visibility */
  margin: 24px 0;
  transform: scaleX(0.5);
}

.divider-subtle {
  border-top: 1px dashed #2A3A5A;
  opacity: 0.3;         /* Subtle background */
  margin: 16px 0;
}
```

#### Padrão 2: Quadrado com Border Amarelo

```css
.card-featured {
  background: #1A3A66;
  border: 2px solid #FFD100;
  border-left: 6px solid #FFD100;  /* Accent side */
  border-radius: 8px;
  padding: 24px;
  transform: rotate(0.5deg);        /* Subtle tilt */
}
```

#### Padrão 3: Círculo Accent (Badge/Status)

```css
.badge-success {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #FFD100;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #0A1F47;
  font-weight: 700;
  box-shadow: 0 0 16px rgba(255, 209, 0, 0.3);
}
```

#### Padrão 4: Gradiente Navy (Background)

```css
body {
  background: linear-gradient(135deg, #0A1F47 0%, #0D2456 50%, #1A3A66 100%);
  color: #FFFFFF;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
```

---

## 5. Aplicações Práticas

### 5.1 Login Page (Inspired)

```
┌─────────────────────────────────────────────┐
│    [Navy Dark BG com gradient sutil]        │
│                                             │
│    Logo Universidade (canto superior)      │
│                                             │
│    ╔═════════════════════════════════════╗ │
│    ║  Planilha de Notas                  ║ │
│    ║  ━━ ━━ ━━ ━━ ━━ ━━ ━━ ━━ ━━    ║ │
│    ║                                     ║ │
│    ║  Email                              ║ │
│    ║  [input amarelo border on focus]    ║ │
│    ║                                     ║ │
│    ║  Palavra-passe                      ║ │
│    ║  [input amarelo border on focus]    ║ │
│    ║                                     ║ │
│    ║  [🔘 Iniciar Sessão] (amarelo btn) ║ │
│    ║                                     ║ │
│    ╚═════════════════════════════════════╝ │
│                                             │
└─────────────────────────────────────────────┘
```

**Elementos:**
- ✅ Background: Navy Dark com gradient
- ✅ Card: Navy Light, border amarelo topo
- ✅ Divisor: Dashed amarelo
- ✅ Botão: Amarelo (#FFD100), texto navy
- ✅ Logo: Canto superior esquerdo, 20% tamanho original

### 5.2 Professor Dashboard

```
┌──────────────────────────────────────────────────┐
│ [Logo Univ]  Planilha de Notas    [Context▼][⚙️]│
│ ━━ ━━ ━━ ━━ ━━ ━━ ━━ ━━ ━━ ━━ ━━ ━━ ━━ ━━│
│                                                  │
│  ┌─────────────────────┐  ┌──────────────────┐ │
│  │ Turma A — 2026.1   │  │ Turma B — 2026.1 │ │
│  ├─────────────────────┤  ├──────────────────┤ │
│  │ ✓ 32/32 estudantes  │  │ ⚠️ 28/32 estudantes│ │
│  │ ✓ 31/32 notas       │  │ ⚠️ 20/28 notas    │ │
│  │ ✓ Publicado         │  │ ⚪ Rascunho       │ │
│  ├─────────────────────┤  ├──────────────────┤ │
│  │ [📤 Enviar]         │  │ [📤 Enviar]      │ │
│  └─────────────────────┘  └──────────────────┘ │
│                                                  │
└──────────────────────────────────────────────────┘
```

**Elementos:**
- ✅ Cards: Navy Light, 2px border amarelo esquerda
- ✅ Badges: Círculos amarelos com checkmarks
- ✅ Botões: Amarelo com texto navy

### 5.3 Student Portal (Mobile-first)

```
┌──────────────────────────┐
│ [Logo Univ]  Minhas Notas│
│ ━━ ━━ ━━ ━━ ━━ ━━ ━━│
│                          │
│  Programação I           │
│  ┌────────────────────┐  │
│  │ Nota Final: 18/20  │  │
│  │ Frequência: 95%    │  │
│  │ Publicado: sim     │  │
│  │                    │  │
│  │ [✓ Publicado]      │  │
│  └────────────────────┘  │
│                          │
│  Cálculo II              │
│  ┌────────────────────┐  │
│  │ Nota: 16/20        │  │
│  │ ⚠️ Não publicado   │  │
│  └────────────────────┘  │
│                          │
│  ━━ ━━ ━━ ━━ ━━ ━━ ━━│
│                          │
│  Calendário              │
│  📅 Exame: 15-06        │
│  📅 Recurso: 22-06      │
│                          │
└──────────────────────────┘
```

**Elementos:**
- ✅ Cards: Navy Light com tilt leve (1-2°)
- ✅ Badges: Círculos amarelos para status
- ✅ Divisores: Dashed amarelo entre secções
- ✅ Ícones: Simples, linhas, cores neutras

---

## 6. Recomendação Final: Conceito "Minimal Modern"

### ✅ Por Que Este Abordagem?

1. **Moderno:** Dark mode first, minimalista, contemporâneo
2. **Acessível:** Alto contraste Navy + Amarelo (WCAG AAA)
3. **Reconhecível:** Amarelo + Navy dizem "Lusíada" sem obsessão
4. **Flexível:** Funciona em mobile, tablet, desktop
5. **Profissional:** Sem parecer datado ou kitsch
6. **Sustentável:** Fácil manutenção, componentes reutilizáveis

### 🎯 Elementos-Chave a Usar

| Elemento | Uso | Frequência |
|----------|-----|-----------|
| **Amarelo (#FFD100)** | CTAs, accents, dividers | Moderado |
| **Navy Dark (#0A1F47)** | Backgrounds, profundidade | Constante |
| **Navy Light (#1A3A66)** | Cards, sections | Frequente |
| **Linhas Dashed** | Separadores, movimento | Ocasional |
| **Quadrados Leves** | Frames, cards | Frequente |
| **Círculos** | Badges, status | Ocasional |
| **Gradientes** | Background, depth | Frequente |
| **Espaço Branco** | Respiro visual | Constante |

### 📝 Paleta Simplificada (CSS)

```css
:root {
  /* Logo Colors */
  --color-navy-dark: #0A1F47;
  --color-navy-base: #003DA5;
  --color-navy-light: #1A3A66;
  --color-yellow: #FFD100;
  --color-white: #FFFFFF;
  --color-gray-light: #E8E8E8;
  --color-gray-dark: #666666;
  
  /* Sem Serif */
  --font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 
                 'Roboto', 'Helvetica Neue', sans-serif;
}
```

---

## 7. Próximos Passos

1. ✅ **Aprovação da Proposta** — Validar se a direção "Minimal Modern" agrada
2. **Atualizar DESIGN.md** — Incorporar novo conceito
3. **Criar Design System v2** — Componentes baseados em Navy + Amarelo
4. **Mid-Fi Mockups** — Aplicar à 9 interfaces (wireframes)
5. **User Testing** — Validar com professor + estudante real

---

**Análise Completa ✅**  
**Brainstorm Criativo ✅**  
**Conceito Recomendado: "Minimal Modern" (Dark Mode First)**

---

*Documento de Pesquisa Visual*  
*Criado por Uma (UX Design Expert) — 2026-06-03*
