---
name: color-palette
description: >-
  Analyze, audit, and optimize the project's color palette. Detects
  inconsistencies, generates harmonious palettes with dark mode mapping,
  and outputs Tailwind config. Use when the user says "color palette",
  "analyze colors", "fix colors", "color audit", or "generate palette".
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Write
argument-hint: "[action] — analyze, generate, harmonize, or export"
---

# Color Palette Analysis & Generator

Analyze, audit, and optimize the color usage in a TailwindCSS project. Detects inconsistencies, suggests improvements, and can generate a complete harmonious palette with dark mode mapping.

## Actions

Parse `$ARGUMENTS` to determine the action:

| Argument | Action |
|----------|--------|
| (empty) or `analyze` | Audit current color usage and report issues |
| `generate [style]` | Generate a new palette from scratch |
| `harmonize` | Fix inconsistencies in the existing palette |
| `export` | Output the current/improved palette as Tailwind config |

---

## Action: Analyze

Scan the project for all color usage and produce a detailed report.

### Scanning Procedure

**Step 1: Read Tailwind config**

Glob for `tailwind.config.*` and read it. Look for:
- `theme.colors` (full override)
- `theme.extend.colors` (extensions)
- Custom color tokens (e.g., `primary`, `secondary`, `accent`)

**Step 2: Scan color class usage**

```
Grep: (bg|text|border|ring|shadow|from|via|to|accent|fill|stroke)-(slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose)-(\d{2,3})
Glob: *.{html,jsx,tsx,vue,svelte,astro}
head_limit: 100
```

**Step 3: Count and categorize**

Build a usage map:
```
Color         | Occurrences | Used as
blue-600      | 23          | bg (buttons), text (links), ring (focus)
blue-500      | 8           | bg (hover), ring (focus)
gray-50       | 15          | bg (surface)
gray-100      | 12          | bg (hover)
...
```

### Report Format

```
## 🎨 Color Palette Analysis

### Current Palette
| Role | Color | Shade Range | Occurrences |
|------|-------|-------------|-------------|
| Primary | blue | 500-700 | 45 |
| Neutral | gray | 50-900 | 89 |
| Accent | emerald | 400-600 | 12 |
| Destructive | red | 500-600 | 8 |

### 🔴 Issues Found

#### Inconsistent Primary Color
- `blue-500` used as primary in 8 places
- `blue-600` used as primary in 23 places
- `indigo-600` used as primary in 3 places
→ **Fix:** Standardize on `blue-600` as primary, `blue-700` for hover

#### Missing Dark Mode Colors
- 34 color classes lack `dark:` variants
- Worst offenders: {list top 5 files}

#### Too Many Gray Variants
- Using both `gray-100` and `gray-50` for the same purpose (surface bg)
→ **Fix:** Consolidate to `gray-50` for surfaces, `gray-100` for hover

#### Accessibility Contrast Issues
- `text-gray-400` on `bg-white` fails WCAG AA (3.6:1, needs 4.5:1)
→ **Fix:** Use `text-gray-500` or darker (4.6:1+)

### ✅ What's Good
{positive observations}

### 📋 Recommended Palette
{optimized palette table — see below}
```

---

## Action: Generate

Generate a complete new color palette. Parse the style from arguments:

```
/color-palette generate              → Default modern SaaS palette
/color-palette generate warm         → Warm tones (amber, orange, rose)
/color-palette generate cool         → Cool tones (sky, blue, slate)
/color-palette generate earthy       → Earthy/natural (stone, emerald, amber)
/color-palette generate vibrant      → Bold/saturated (violet, fuchsia, cyan)
/color-palette generate monochrome   → Single hue + neutrals
/color-palette generate brand #3B82F6 → Build palette around a specific brand color
```

### Palette Structure

Every generated palette must include:

```
## Generated Palette

| Role | Light Mode | Dark Mode | Usage |
|------|-----------|-----------|-------|
| **Primary** | {color}-600 | {color}-500 | Buttons, links, active states |
| **Primary Hover** | {color}-700 | {color}-400 | Button hover, link hover |
| **Primary Light** | {color}-50 | {color}-950 | Subtle backgrounds, badges |
| **Secondary** | {color2}-600 | {color2}-500 | Secondary actions |
| **Accent** | {color3}-500 | {color3}-400 | Highlights, indicators |
| **Destructive** | red-600 | red-500 | Delete, error states |
| **Warning** | amber-500 | amber-400 | Warning states |
| **Success** | emerald-600 | emerald-500 | Success states |
| **Neutral BG** | white | {gray}-950 | Page background |
| **Surface** | {gray}-50 | {gray}-900 | Card/panel background |
| **Surface Hover** | {gray}-100 | {gray}-800 | Hover on surfaces |
| **Elevated** | white | {gray}-800 | Elevated panels, modals |
| **Border** | {gray}-200 | {gray}-700 | Borders, dividers |
| **Text Primary** | {gray}-900 | {gray}-100 | Headings, body text |
| **Text Secondary** | {gray}-600 | {gray}-400 | Descriptions, labels |
| **Text Muted** | {gray}-400 | {gray}-500 | Placeholders, captions |
```

### Palette Rules

- **One primary color family.** Never use two different saturated colors for the same role.
- **One neutral gray family.** Pick `gray`, `slate`, `zinc`, `neutral`, or `stone` — use only that one across the entire project.
- **Dark mode = lighter shades.** Primary goes from 600→500, neutrals invert (50→950, 100→900, etc.).
- **Contrast:** All text/bg combinations must meet WCAG AA (4.5:1 for normal text, 3:1 for large text).
- **Maximum 4 semantic colors:** primary, secondary, accent, destructive. More creates visual chaos.
- **Surface hierarchy in dark mode:** Always 3 levels (`*-950` base → `*-900` surface → `*-800` elevated).

---

## Action: Harmonize

Fix inconsistencies in the existing palette without changing the overall look:

1. Run the **Analyze** procedure first
2. For each inconsistency found:
   - Pick the most-used variant as the canonical one
   - List all files that need updating
   - Provide the exact class replacement (e.g., `indigo-600` → `blue-600`)
3. Generate a migration checklist:

```
## Harmonization Plan

### Changes (safe — no visual regression)
- [x] `text-gray-400` → `text-gray-500` (5 files — contrast fix)
- [x] Remove `gray-100` usage → use `gray-50` (3 files — consolidation)

### Changes (minor visual change)
- [ ] `indigo-600` → `blue-600` in 3 files (align with primary)
- [ ] `shadow-blue-400/20` → `shadow-blue-500/25` (align with primary)

### Dark Mode Additions Needed
- [ ] src/components/Card.tsx — 6 classes missing `dark:` variants
- [ ] src/components/Sidebar.tsx — 4 classes missing `dark:` variants
```

Present the plan and **ask the user** before applying changes.

---

## Action: Export

Output the palette in formats the user can directly use:

### Tailwind Config Format

```js
// tailwind.config.js — paste into theme.extend.colors
colors: {
  primary: {
    50: '#eff6ff',   // blue-50
    100: '#dbeafe',  // blue-100
    500: '#3b82f6',  // blue-500
    600: '#2563eb',  // blue-600
    700: '#1d4ed8',  // blue-700
  },
  surface: {
    light: '#f9fafb',   // gray-50
    DEFAULT: '#ffffff',
    dark: '#030712',     // gray-950
  },
  // ... full mapping
}
```

### CSS Custom Properties Format

```css
:root {
  --color-primary: theme('colors.blue.600');
  --color-primary-hover: theme('colors.blue.700');
  --color-surface: theme('colors.gray.50');
  /* ... */
}
.dark {
  --color-primary: theme('colors.blue.500');
  --color-primary-hover: theme('colors.blue.400');
  --color-surface: theme('colors.gray.900');
  /* ... */
}
```

### Design System Update

If `design-system.md` exists, offer to update its `## Colors` section with the exported palette.

---

## Accessibility Reference

Minimum contrast ratios (WCAG 2.1 AA):

| Type | Ratio | Example |
|------|-------|---------|
| Normal text | 4.5:1 | `text-gray-600` on `white` = 5.4:1 ✅ |
| Large text (18px+ bold / 24px+) | 3:1 | `text-gray-500` on `white` = 4.6:1 ✅ |
| UI components | 3:1 | `border-gray-300` on `white` = 3.2:1 ✅ |

Common TailwindCSS contrast traps:

| Combo | Ratio | Verdict |
|-------|-------|---------|
| `text-gray-400` on `bg-white` | 3.6:1 | ❌ Fail AA |
| `text-gray-500` on `bg-white` | 4.6:1 | ✅ Pass AA |
| `text-gray-400` on `bg-gray-900` | 4.2:1 | ❌ Fail AA |
| `text-gray-500` on `bg-gray-900` | 3.4:1 | ❌ Fail AA |
| `text-gray-400` on `bg-gray-950` | 4.8:1 | ✅ Pass AA |
