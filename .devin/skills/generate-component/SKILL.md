---
name: generate-component
description: >-
  Generate a production-ready TailwindCSS UI component skeleton that matches
  the project's design system. Use when the user says "generate component",
  "scaffold component", "create component skeleton", or "new component".
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Write
argument-hint: "<type> [variant] — e.g. card, modal dark, form horizontal, table striped"
---

# Generate Design-System-Consistent Component

Generate a production-ready TailwindCSS component that automatically matches the project's existing design conventions.

## Workflow

### Step 1: Load Design Context

Read `design-system.md` from the project root. If it exists, use those values for all styling decisions. If it does not exist, use the defaults from the `tailwind-ui-rules` skill rules.

### Step 2: Detect Tech Stack

Check the project for framework files to determine output format:

| Check | Framework | Output |
|-------|-----------|--------|
| `*.tsx` + `next.config.*` | Next.js / React | TSX component |
| `*.tsx` | React | TSX component |
| `*.jsx` | React (JS) | JSX component |
| `*.vue` | Vue | SFC `.vue` component |
| `*.svelte` | Svelte | `.svelte` component |
| `*.astro` | Astro | `.astro` component |
| none of above | Plain HTML | HTML with Tailwind classes |

If multiple frameworks detected, prefer TSX (most common).

### Step 3: Parse Arguments

`$ARGUMENTS` specifies the component type and optional variant:

```
/generate-component card                → Standard card
/generate-component card horizontal     → Horizontal card layout
/generate-component modal               → Modal/dialog
/generate-component modal confirmation  → Confirmation dialog variant
/generate-component form                → Standard form
/generate-component form horizontal     → Horizontal label layout
/generate-component table               → Data table
/generate-component table striped       → Striped rows table
/generate-component hero                → Hero section
/generate-component nav                 → Navigation bar
/generate-component sidebar             → Sidebar navigation
/generate-component pricing             → Pricing card/table
/generate-component stats               → Stats/metric cards
/generate-component empty-state         → Empty state placeholder
/generate-component skeleton            → Skeleton loading placeholder
```

If the type is not in the list above, still generate it — use best judgment for the structure and apply all design system rules.

### Step 4: Generate Component

Apply **all** of these to the generated component:

#### From Design System (or defaults)

| Property | Source | Fallback |
|----------|--------|----------|
| Shadow | `design-system.md` → Shadows table | `shadow-sm` rest, `shadow-md` hover |
| Border radius | `design-system.md` → Border Radius | `rounded-lg` cards, `rounded-md` buttons/inputs |
| Spacing | `design-system.md` → Spacing | `p-4` to `p-6` internal, `gap-4` between |
| Colors | `design-system.md` → Colors | `blue-600` primary, `gray` neutral |
| Typography | `design-system.md` → Typography | `text-base` body, `font-semibold` headings |
| Focus | `design-system.md` → Interactive States | `focus-visible:ring-2 ring-blue-500 ring-offset-2` |
| Transitions | `design-system.md` → Interactive States | `transition-colors duration-150` |
| Dark mode | `design-system.md` → Dark Mode | `class` strategy with 3-level surfaces |

#### Mandatory Requirements (always include)

Every generated component **must** have:

- [ ] **Dark mode:** All `bg-*`, `text-*`, `border-*` classes have corresponding `dark:` variants
- [ ] **Hover state:** Cards get shadow step-up + subtle translate; buttons get color darkening
- [ ] **Focus state:** `focus-visible:ring-2` on all interactive elements (never `focus:`)
- [ ] **Disabled state:** `disabled:opacity-50 disabled:cursor-not-allowed` on buttons/inputs
- [ ] **Transitions:** `transition-*` + `duration-*` on all state changes
- [ ] **Responsive:** Mobile-first classes, grid/flex adjusts at `sm:`/`lg:` breakpoints
- [ ] **Accessibility:** Semantic HTML (`<button>`, `<nav>`, `<main>`), `aria-label` where needed, minimum `h-10 w-10` touch targets
- [ ] **Motion safety:** `motion-safe:` prefix on translate/scale animations
- [ ] **Overflow safe:** Cards in scroll containers get `-mx-4 px-4` trick if applicable

---

## Component Templates

### Card

```
Structure:
- Outer: rounded, shadow, border, padding, dark mode bg
- Optional image: aspect-ratio, object-cover, rounded-t
- Content: heading (font-semibold), description (text-gray-600 dark:text-gray-400)
- Optional footer: border-t, flex justify-between, action buttons
- Hover: shadow step-up + motion-safe:translate-y
- Transition: transition-all duration-200
```

Variants:
- `horizontal` — Image left, content right (flex row, stack on mobile)
- `interactive` — Clickable with group-hover effects
- `stats` — Metric value (text-3xl font-bold) + label + optional trend indicator

### Modal

```
Structure:
- Backdrop: fixed inset-0, bg-black/50, backdrop-blur-sm
- Panel: centered, max-w-lg, rounded-xl, shadow-2xl, p-6
- Header: flex justify-between, heading + close button
- Body: content area with overflow-y-auto if needed
- Footer: flex justify-end gap-3, action buttons (cancel secondary, confirm primary)
- Animation: motion-safe:animate (scale + fade in)
```

Variants:
- `confirmation` — Icon (warning/danger) + short message + destructive action button
- `form` — Form fields in body, submit in footer
- `fullscreen` — Mobile fullscreen, desktop centered panel

### Form

```
Structure:
- Form element with flex flex-col gap-6
- Field groups: label + input + optional error message
- Labels: text-sm font-medium text-gray-700 dark:text-gray-300
- Inputs: full border, rounded, padding, focus-visible ring, error ring
- Submit: primary button, full-width on mobile, auto-width on desktop
- Error state: border-red-500 + text-red-600 message below field
```

Variants:
- `horizontal` — Labels beside inputs on desktop (grid grid-cols-[200px_1fr])
- `inline` — Single-row form (search bar, newsletter signup)
- `multi-step` — Step indicator + form sections

### Table

```
Structure:
- Container: overflow-x-auto, rounded-lg, border
- Table: w-full, text-left
- Header: bg-gray-50 dark:bg-gray-800, font-medium, uppercase text-xs tracking-wider
- Rows: border-b, hover:bg-gray-50 dark:hover:bg-gray-800/50
- Cells: px-6 py-4, whitespace-nowrap where appropriate
- Responsive: horizontal scroll on mobile, consider card layout for sm:
```

Variants:
- `striped` — Even rows: bg-gray-50/50 dark:bg-gray-800/30
- `selectable` — Checkbox column, selected row highlight
- `sortable` — Sort icons in header, active sort indicator

### Hero

```
Structure:
- Full-width section, py-16 sm:py-24 lg:py-32
- Container: mx-auto max-w-7xl px-4 sm:px-6 lg:px-8
- Heading: text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight
- Subheading: text-lg sm:text-xl text-gray-600 dark:text-gray-400, max-w-2xl
- CTA buttons: flex gap-4, primary + secondary/ghost
- Optional: background gradient, illustration, stats row
```

### Navigation

```
Structure:
- Sticky top, z-40, backdrop-blur, border-b
- Container: flex items-center justify-between, h-16
- Logo: flex-shrink-0
- Links: hidden md:flex gap-6, active state (font-medium + color)
- Mobile: hamburger button (md:hidden), slide-out or dropdown menu
- Right side: optional search, user avatar, CTA button
```

### Empty State

```
Structure:
- Centered flex-col, py-12
- Icon: h-12 w-12, text-gray-400 dark:text-gray-600
- Heading: text-lg font-semibold
- Description: text-sm text-gray-500, max-w-sm, text-center
- CTA: primary button or link
```

---

## Output Rules

1. **Write to file** if the user's project has a clear component directory structure (e.g., `src/components/`). Ask user for confirmation of the file path.
2. **Output to chat** if the project structure is unclear or the user just wants to see the code.
3. **Include a brief comment** at the top: `<!-- Generated by tailwind-ui-rules | design-system applied -->` (or JSX equivalent `{/* ... */}`)
4. **Name the component** based on the type: `Card.tsx`, `Modal.tsx`, `DataTable.tsx`, etc.
5. **Use TypeScript** if the project uses `.tsx` files. Include a `Props` interface.
6. **Export as default** for page components, **named export** for reusable components.
