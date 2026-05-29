---
name: component-visual-review
description: Visual review of a Drupal SDC component against a design reference. Prefers Figma (extracts exact values via MCP) but falls back to attached images. Iterates with Chrome DevTools screenshots until the component matches the reference.
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
  - Grep
  - Glob
  - mcp__plugin_figma_figma__get_design_context
  - mcp__plugin_figma_figma__use_figma
  - mcp__plugin_figma_figma__get_screenshot
  - mcp__plugin_figma_figma__get_metadata
  - mcp__chrome-devtools__navigate_page
  - mcp__chrome-devtools__emulate
  - mcp__chrome-devtools__take_screenshot
  - mcp__chrome-devtools__evaluate_script
---

# Component Visual Review

A structured workflow for matching a Drupal SDC component to a design reference.
**The rule: no visual value is guessed. Everything comes from the reference (Figma if available, attached image otherwise).**

---

## Step 0: Collect inputs

### Required

1. **Component directory path** — e.g. `project/themes/tryngolza/components/my-component/`
2. **Local preview URL** — e.g. `http://tryn-nxt.docksal.site/component-test`
3. **At least one design reference for desktop** — Figma URL OR attached image

### Optional

4. **Mobile design reference** — Figma URL or attached image. If not provided, ask the user whether mobile should:
   - **Stack** (default fallback): vertical stack of desktop elements, reduce padding/font proportionally
   - **Match desktop**: same layout, scaled down by viewport
   - **Custom**: user describes mobile behavior verbally

### Branching

- **Figma available** → Step 1A (extract via MCP)
- **Image only** → Step 1B (visual reference)

If the Figma MCP tools fail (server not connected, URL invalid), ask the user if they have an attached image to use as a fallback. Don't proceed without some reference.

---

## Step 1A: Extract exact specs from Figma

Call `get_design_context` for the desktop URL (and mobile if provided). Extract and record the following explicitly — these values go directly into code, never approximated.

### Colors and gradients

- Every fill: exact hex or `rgba(r, g, b, a)` value
- Every gradient: type (linear/radial), angle, each stop with color and position %
  - Translate to CSS: `linear-gradient(180deg, rgba(...) X%, #HEX Y%)`
- **Gradient strokes (critical)**: Figma MCP flattens gradient strokes to a solid color in its output. If a stroke should be a gradient:
  1. Use `use_figma` to read the raw paint data for that node
  2. Extract each gradient stop from the raw `gradientStops` array
  3. Build the CSS manually from those exact stop values
  4. For gradient borders, use the multi-background technique: `border: 2px solid transparent; background: <inner-bg> padding-box, <gradient> border-box;`

### SVG paths and shapes

- **Never reconstruct SVG paths by hand or copy from screenshots**
- For any inline SVG (circles, icons, decorative shapes):
  1. Use `use_figma` to export the node as SVG markup
  2. Copy `<path d="...">`, `viewBox`, fill, and stroke values verbatim
  3. Record each `<linearGradient>` / `<radialGradient>` definition with exact stop colors and positions
  4. Ensure IDs are unique per instance if the SVG repeats — use a Twig `random()` uid

### Sizing and spacing

- All dimensions in px: width, height, min-height, padding (each side), gap, border-radius (each corner)
- Note border-radius math where the radius must match another element's curvature (e.g., card left border-radius = circle width / 2)

### Typography

- Font family, weight, size, line-height, letter-spacing per text style per breakpoint

---

## Step 1B: Use attached image as reference

If working from an attached image only:

- Use the image visually for layout, colors, proportions, and spacing
- Sample colors from the image with care; ask the user to confirm exact hex values for brand colors
- For SVGs/icons: ask the user to provide the SVG file directly, or extract from existing components in the codebase — never trace from an image
- For typography: ask the user for font family, sizes, and weights if not obvious

Document everything you extract or assume. Ask the user to confirm before writing CSS.

---

## Step 2: Baseline screenshot (before any code changes)

Screenshot the current local component at both breakpoints using Chrome DevTools:

```text
Desktop: emulate viewport 1280x900x1
Mobile:  emulate viewport 390x844x2,mobile,touch
```

Navigate to the local preview URL, scroll to the component, and take screenshots. Note every visible gap vs. the reference.

### Note: Canvas iframe context

If the component is only visible inside the Canvas editor (not on a public test page), some styles that depend on the `body.path-canvas` selector will apply. If the component looks correct on the test page but broken in Canvas edit mode (or vice-versa), check whether any CSS is scoped to `body.path-canvas`.

---

## Step 3: Implement using extracted values

Apply the exact values from Step 1 to the component CSS and Twig files:

- Paste gradient CSS verbatim from the extracted stop values
- Paste SVG `<path d="...">` strings exactly as exported — no manual redrawing
- Apply all sizing, spacing, and border-radius from extracted measurements
- For any value not yet extracted, go back to the reference before guessing

---

## Step 4: Verify at both breakpoints

After each meaningful change:

1. Reload the local preview URL
2. Screenshot at 1280px (desktop)
3. Screenshot at 390px mobile
4. Compare each screenshot against the reference
5. List every remaining gap explicitly
6. Repeat from Step 3 until no gaps remain

Pay special attention to:
- Gradient colors and direction
- SVG rendering (circle gradients, stroke gradients, decorative shapes)
- Spacing on mobile vs. desktop (often differ significantly)
- `overflow` behavior — confirm clipping is correct at all breakpoints

### Iteration cap

If after **3 rounds of fixes** there are still visible gaps but no obvious cause:
- Pause and present what you see to the user
- Ask whether the remaining differences are acceptable or whether they're being caused by an upstream stylesheet, a font that isn't loaded, or a value you can't extract from the reference
- Don't loop indefinitely on micro-pixel differences

---

## Step 5: Final sign-off

Take a final viewport screenshot at both breakpoints and confirm:
- [ ] All colors and gradients match the reference
- [ ] All SVG paths render correctly
- [ ] All sizes and spacing match
- [ ] Mobile layout matches (or matches the agreed fallback strategy from Step 0)
- [ ] No values were approximated — every number came from the reference or was explicitly confirmed by the user
- [ ] If the component is used inside Canvas edit mode, verified there too
