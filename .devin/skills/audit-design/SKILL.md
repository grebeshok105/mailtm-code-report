---
name: audit-design
description: >-
  Audit the current project's frontend code for TailwindCSS design violations,
  anti-patterns, and inconsistencies. Run this command to get a detailed report
  with concrete fix suggestions. Use when the user says "audit design",
  "check design", "review UI code", "find design issues", or "lint tailwind".
disable-model-invocation: true
allowed-tools: Read, Grep, Glob
argument-hint: "[file-or-directory] (optional — defaults to entire project)"
---

# TailwindCSS Design Audit

Run a comprehensive audit of the project's frontend code against the `tailwind-ui-rules` skill rules. Produce an actionable report with concrete fix suggestions.

## Audit Scope

If `$ARGUMENTS` specifies a file or directory, audit only that scope. Otherwise, audit the entire project.

Target files: `**/*.{html,jsx,tsx,vue,svelte,astro}`

## Audit Checklist

Scan the codebase for each category below. For every violation found, report:
- **File and line** (or file and pattern)
- **What's wrong** (the specific class or pattern)
- **How to fix** (the correct class or pattern)

### 1. Shadow Violations

Search for shadow misuse:

```
Grep: shadow-(lg|xl|2xl)
```

Flag:
- `shadow-lg` or higher on **cards at rest** (should be `shadow-sm`, elevate on hover)
- `shadow-xl` or `shadow-2xl` on anything that is **not** a modal, overlay, or command palette
- Shadow classes **without** `transition-shadow` on interactive elements
- Missing `dark:shadow-` variants (no dark mode shadow handling)
- Colored shadows (`shadow-{color}`) on non-primary-action elements

### 2. Spacing Violations

Search for arbitrary spacing values:

```
Grep: (p|m|gap|space|inset)-\[
```

Flag:
- Any arbitrary value like `p-[13px]`, `mt-[22px]`, `gap-[7px]` — suggest nearest Tailwind scale value
- Mixed spacing between siblings (e.g., one child has `mb-4`, next has `mb-6` — suggest `gap-*` on parent)

Also check for inconsistent component spacing:

```
Grep: (mb|mt|mr|ml)-[0-9]
```

Flag when sibling elements in the same container use different margin values instead of `gap-*` on parent.

### 3. Layout Issues

Search for common layout mistakes:

```
Grep: w-\[.*px\]
```

Flag:
- Hard-coded widths like `w-[800px]` — suggest `max-w-*` or responsive fractions
- `z-\[9999\]` or `z-\[\d{3,}\]` — suggest organized z-index scale (`z-10`, `z-20`, `z-30`, `z-50`)
- Nested flex containers simulating a grid — suggest `grid`
- `w-full` inside flex containers where `flex-1` is more appropriate

### 4. Accessibility Issues

Search for accessibility problems:

```
Grep: focus:ring|focus:outline|onClick
```

Flag:
- `focus:ring` instead of `focus-visible:ring` (rings should only show for keyboard nav)
- `<div onClick` or `<span onClick` without `role="button"` and `tabIndex` — suggest `<button>`
- Interactive elements smaller than `h-10 w-10` (40px touch target)
- Missing `disabled:` state classes on buttons/inputs

### 5. Dark Mode Issues

Search for dark mode completeness:

```
Grep: (bg|text|border)-(gray|slate|zinc|neutral|stone)-[0-9]
```

Cross-reference with:

```
Grep: dark:(bg|text|border)
```

Flag:
- Color classes **without** corresponding `dark:` variants
- Single dark background for all surfaces (should use 3-level hierarchy: `bg-gray-950` → `bg-gray-900` → `bg-gray-800`)
- `dark:shadow-` missing on elevated elements

### 6. Responsive Design Issues

Search for desktop-first patterns:

```
Grep: (block|flex|grid|inline) (sm|md|lg|xl):hidden
```

Flag:
- Desktop-first visibility patterns (`block sm:hidden`) — should be mobile-first (`hidden sm:block`)
- Missing responsive breakpoints on grid layouts (e.g., `grid-cols-3` without `grid-cols-1` base)
- Hard-coded heights/widths without responsive alternatives

### 7. Transition & Animation Issues

Search for missing transitions:

```
Grep: hover:(bg|text|border|shadow|translate|scale)
```

Cross-reference with:

```
Grep: transition-
```

Flag:
- Hover/focus state changes **without** `transition-*` and `duration-*` classes
- Animations without `motion-safe:` prefix (violates `prefers-reduced-motion`)
- `duration-[0-9]` usage — check if it's a standard Tailwind duration value

### 8. Design System Consistency

If `design-system.md` exists in the project root, read it and check:
- Are the actual shadow levels matching the documented ones?
- Are the spacing values consistent with the documented rhythm?
- Are the colors matching the documented palette?
- Are the border-radius values consistent?

Report any **drift** between the documented design system and the actual code.

---

## Output Format

Present the audit as a structured report:

```
## 🔍 TailwindCSS Design Audit Report

**Scope:** {files audited}
**Files scanned:** {count}
**Issues found:** {count by severity}

### 🔴 Critical (Accessibility & Functionality)
{list issues}

### 🟠 Major (Visual Consistency & Best Practice)
{list issues}

### 🟡 Minor (Polish & Optimization)
{list issues}

### ✅ What's Good
{list things the project does well — positive reinforcement}

### 📋 Suggested Fixes (Priority Order)
1. {most impactful fix with code example}
2. {next fix}
...
```

**Severity Classification:**
- **Critical**: Accessibility violations (`focus:` instead of `focus-visible:`, `<div onClick>`, missing touch targets)
- **Major**: Shadow overuse, missing dark mode, spacing inconsistency, desktop-first patterns
- **Minor**: Missing transitions, suboptimal z-index, arbitrary values

**Rules:**
- Always include at least one "What's Good" item — don't be purely negative
- Limit the report to the **top 20 most impactful issues** if there are many. Note the total count.
- Provide **copy-pasteable fix snippets** in the Suggested Fixes section
- If a `design-system.md` exists, reference it in the report and note any drift
- If no issues found in a category, skip that category (don't report empty sections)
