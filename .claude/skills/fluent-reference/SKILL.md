---
name: fluent-reference
description: Use when a design question needs the Fluent 2 / Windows 11 value (control sizes, spacing, radii, type ramp, motion, colours, dialog button order, focus ring, toasts and InfoBars). Read it before deciding look rows in docs/ui-goal; it replaces working from memory. Every value in tokens.md carries its source and a verified flag.
---

# Fluent 2 / Windows 11 reference

The owner chose Fluent 2 as the design reference (docs/ui-goal/decisions.md Q-02, DESIGN.md
"direction A"). Where our approved values differ from Fluent, ours stay unless a row is
explicitly open; this skill tells you what Fluent says, and how sure we are.

Files:
- `tokens.md`: the values as tables. Each table names its source (package@version file path or
  URL) and every row has a flag: `verified` (read from the source in the session that built this
  file) or `unverified (memory)`. Never quote an unverified value as fact in a decision; say so.
- `mapping.md`: our DESIGN.md tokens mapped to the nearest Fluent token, with mismatches flagged.

Rules of use:
1. Look the value up in tokens.md first. If the row is `unverified (memory)`, either find a
   source (fetch the Learn page, or `npm pack @fluentui/tokens`) and upgrade the row, or say
   "unverified" in your answer.
2. Package data is MIT (`@fluentui/tokens` 1.0.0-alpha.25, `@fluentui/react-theme` 9.2.3 which
   re-exports it). Microsoft Learn text is paraphrased only; link, do not copy.
3. Fluent web tokens are CSS px; Windows apps use effective pixels (epx) with the same numbers at
   100 % scale.
4. Refresh: `npm pack` both packages into a new scratch dir each time, read as data, never run.
