---
name: component-create
description: End-to-end Drupal SDC component creation for Canvas. Accepts requirements from Jira, Figma, attached images, or a written description. Implements all files, then hands off to /component-visual-review for styling.
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
  - mcp__claude_ai_Atlassian__getJiraIssue
  - mcp__claude_ai_Atlassian__search
---

# Component Create Skill

An end-to-end workflow for creating a new Drupal SDC component that works with Canvas. Generates all required files with the correct structure, then hands off to `/component-visual-review` for pixel-perfect styling.

---

## Step 0: Collect inputs

The skill supports multiple input modes. Ask the user which they have available and proceed with whatever is provided.

### Required (always)

1. **Theme name** — `tryngolza` or `kytg_nxt`
2. **Component machine name** — e.g. `shtg-icon-gradient-card` (kebab-case, no theme prefix)

### Requirements source — at least ONE of

3. **Jira ticket URL or ID** (e.g. `TRYN-843`) — preferred; provides full acceptance criteria
4. **Written description** — short paragraph naming the component, its purpose, and variants
5. **Figma desktop frame URL** — preferred design source
6. **Attached image(s)** — designer screenshots; mention them in chat with description ("desktop hero", "mobile hero")

### Optional

7. **Figma mobile frame URL** — only if mobile layout differs meaningfully from desktop (often it just stacks)

### Branching rules

- If the user provides ONLY a written description (no Jira, no Figma, no images), confirm prop inventory verbally before writing files.
- If the user provides Figma URLs, prefer those for spec extraction.
- If the user provides only images, use them visually for prop identification and ask for any values that aren't visible (typography, exact spacing).
- If mobile design isn't provided, assume the mobile layout is "stack vertically, reduce padding/font sizes proportionally" and confirm with the user before writing the mobile media query.

---

## Step 0.5: Validate inputs against the filesystem

**Run these checks before writing any files.** If any fail, stop and tell the user what's wrong — do NOT proceed.

```bash
# 1. Confirm we're in the project root
test -d project/themes || { echo "Not in ionis-tryn repo root"; exit 1; }

# 2. Theme directory exists
test -d project/themes/{theme}/components || { echo "Theme '{theme}' not found — typo?"; exit 1; }

# 3. Component doesn't already exist (no accidental overwrite)
test ! -d project/themes/{theme}/components/{machine-name} \
  || { echo "Component '{machine-name}' already exists in {theme} — pick a different name or use /component-visual-review on the existing one"; exit 1; }

# 4. Canvas config directory exists
test -d project/config/{config_dir} || { echo "Config dir 'project/config/{config_dir}' not found"; exit 1; }

# 5. Drush alias works (catches Docksal not running or misconfigured site)
fin drush @{site_alias}.local status 2>/dev/null | grep -q "Drupal version" \
  || { echo "Drush alias @{site_alias}.local not responding — is fin running? is the site configured?"; exit 1; }
```

Map theme → alias → config dir from the quick-reference table at the bottom of this skill. If any check fails, surface the exact error to the user before continuing.

---

## Step 1: Pull requirements (skip steps that don't apply)

### 1a. Jira ticket (if provided)

```text
mcp__claude_ai_Atlassian__getJiraIssue with issueIdOrKey = <ticket>
```

Note: component purpose, variants (size, layout position, color scheme), specific field requirements.

### 1b. Figma specs (if Figma URLs provided)

Call `get_design_context` for the desktop URL (and the mobile URL if provided).

Extract and record explicitly (these go into code verbatim):

**Props inventory** — every editable element:
- Text fields (title, body, label, etc.)
- Images / media
- Links / URLs
- Enum-style variants (size, color, position, layout)
- Booleans (show/hide elements)

**Sizing, spacing, colors, gradients, typography** — only what's relevant for the prop schema at this stage. Detailed values come later in `/component-visual-review`.

**SVG shapes** — do NOT reconstruct paths by hand. Use `use_figma` to export exact SVG markup.

### 1c. Image-only mode (no Figma, no Jira)

If the user attached images instead of Figma URLs, use the attached images visually to identify props. List what you can see and ask the user to confirm anything that's ambiguous (e.g., "Is the title clickable?", "Is the icon optional?").

---

## Step 2: Derive the component structure

Before writing any files, present a spec summary for the user to review:

```text
Component: {theme}/{machine-name}
Source: Jira <ticket> + Figma <url> | Image attachments | Written description
Props:
  - title: string
  - body: string (optional)
  - link_url: string (optional, URL)
  - image: canvas/image (entity_reference)
  - size: enum [large, small] default: large
  - heading_level: string default: h3   ← only if the component has a title
Canvas config field types:
  - title → field_type: string, default_value: null
  - image → field_type: entity_reference, default_value: {  }
  - link_url → field_type: string, default_value: null
  ...
Mobile strategy: separate Figma frame | proportional scale of desktop | confirm with user
```

Wait for user confirmation before writing files.

---

## Step 3: Create all component files

### Directory
```text
project/themes/{theme}/components/{machine-name}/
  {machine-name}.component.yml
  {machine-name}.twig
  {machine-name}.css
```

### 3a. component.yml

```yaml
$schema: https://git.drupalcode.org/project/drupal/-/raw/HEAD/core/assets/schemas/v1/metadata.schema.json

name: Human Readable Name
description: One-sentence description of the component's purpose.
status: stable
group: {Theme Name} Components

props:
  type: object
  properties:
    title:
      type: string
      title: Title
      description: Component heading.

    heading_level:        # only include if the component has a title
      type: string
      title: Heading Level
      enum:
        - h2
        - h3
        - h4
      default: h3

    body:
      type: string
      title: Body

    link_url:
      type: string
      title: Link URL
      description: Optional URL — makes the title a link.

    image:
      $ref: json-schema-definitions://canvas.module/image
      type: object
      title: Image

    size:
      type: string
      title: Size
      enum:
        - large
        - small
      default: large
```

**Rules:**
- Never use empty string `""` as an enum value — use `none` or the actual default word
- Never use `default` as an enum value (Canvas reserved word)
- For URL props: use `type: string`, NOT `$ref: canvas.module/link`
- Images use `$ref: json-schema-definitions://canvas.module/image`
- Only add `heading_level` enum when the component has a title prop

### 3b. Twig template

```twig
{#
/**
 * @file
 * {Component Name} component.
 *
 * Props:
 * - title: heading text
 * - heading_level: h2|h3|h4 (default h3)
 * - body: HTML body content
 * - link_url: optional URL
 * - image: canvas image object (src, alt, width, height)
 * - size: large (default) or small
 */
#}
{% set size = size|default('large') %}
{% set heading_tag = heading_level|default('h3') %}
{% set component_classes = [
  'component-name',
  'component-name--' ~ size,
] | filter(v => v) | join(' ') %}

<div class="{{ component_classes }}">
  {% if image and image.src %}
    <div class="component-name__media">
      <img
        src="{{ image.src }}"
        alt="{{ image.alt|default('') }}"
        {% if image.width %}width="{{ image.width }}"{% endif %}
        {% if image.height %}height="{{ image.height }}"{% endif %}
        loading="lazy"
        class="component-name__image"
      >
    </div>
  {% endif %}

  <div class="component-name__content">
    {% if title %}
      <{{ heading_tag }} class="component-name__title">
        {% if link_url %}
          <a href="{{ link_url }}" class="component-name__title-link">{{ title }}</a>
        {% else %}
          {{ title }}
        {% endif %}
      </{{ heading_tag }}>
    {% endif %}

    {% if body %}
      <div class="component-name__body">{{ body|raw }}</div>
    {% endif %}
  </div>
</div>
```

**Twig rules:**
- Check `image and image.src` before rendering images (Canvas passes empty object when not set)
- Use `icon.alt|default('')` for decorative icons
- Use `target="_blank" rel="noopener noreferrer"` for external links; add `<span class="visually-hidden"> (opens in new tab)</span>` inside the link
- Use `{{ body|raw }}` for rich text fields
- Use dynamic heading tag pattern: `<{{ heading_tag }}>...</{{ heading_tag }}>`
- Use `random()` uid for SVG gradient IDs when multiple SVGs of the same type appear on a page: `{% set uid = 'prefix-' ~ random(9999999) %}`

### 3c. CSS skeleton (placeholder only)

Write a CSS file with the correct scoping and BEM structure, but leave values empty. The actual values come from the design source in Step 6 via `/component-visual-review`.

```css
.layout-container {

  .component-name {
    /* desktop styles */
  }

  .component-name--small {
    /* size variant */
  }

  .component-name__title {
    /* typography */
  }

  .component-name__body,
  .component-name__body p {
    /* body typography */
  }

  @media (max-width: 767px) {

    .component-name {
      /* mobile styles */
    }

  }

}
```

**CSS rules:**
- Always scope inside `.layout-container { }` — required for Drupal layout system
- Use BEM: `__element` and `--modifier`
- Use CSS custom properties from `_colors.scss` for colors (e.g. `var(--color-purple)`, `var(--gradient-brand)`)
- Gradient borders: `border: 2px solid transparent; background: <gradient> padding-box, var(--gradient-brand) border-box`
- Mobile breakpoint: `max-width: 767px`

---

## Step 4: Create Canvas config

After creating the component files and clearing cache, generate the Canvas config:

```bash
# Clear cache to register new component
fin drush @{site_alias}.local cr

# Check it appears in Canvas
# Visit: {site_url}/admin/appearance/component/status

# Export Canvas config
fin drush @{site_alias}.local cex -y

# Verify file was created
ls project/config/{config_dir}/canvas.component.sdc.{theme}.{machine-name}.yml
```

If the file was NOT created, visit the component status page for errors, then invoke `/canvas-troubleshoot`.

### Canvas config prop field types

Manually verify the exported canvas config. The `field_type` and `default_value` must match:

| SDC prop | Canvas field_type | default_value |
|---|---|---|
| `type: string` (text or URL) | `string` | `null` |
| `type: boolean` | `boolean` | `null` |
| `$ref: canvas.module/image` | `entity_reference` | `{  }` |

If any `default_value` is wrong, edit the exported YAML directly and re-import with `cim -y`.

---

## Step 5: Verify the skeleton renders

Before styling, confirm the component renders without errors:

1. Navigate to a Canvas page or test URL
2. Add the component via Canvas editor
3. Confirm: no PHP errors, no Twig errors, structure is correct

If there are Canvas errors, invoke `/canvas-troubleshoot` and resolve them before continuing.

---

## Step 6: Style with /component-visual-review

Hand off to the `/component-visual-review` skill now.

Inputs to pass along:
- Figma desktop URL (if collected) OR attached reference image
- Figma mobile URL (if collected and meaningfully different from desktop) — otherwise note "mobile = proportional scale of desktop"
- Component directory: `project/themes/{theme}/components/{machine-name}/`
- Local preview URL: `{site_url}/component-test` or the Canvas page URL

---

## Step 7: Export final config and commit

After styling is complete:

```bash
fin drush @{site_alias}.local cex -y

git status
# Expected files:
# - project/themes/{theme}/components/{machine-name}/*.yml
# - project/themes/{theme}/components/{machine-name}/*.twig
# - project/themes/{theme}/components/{machine-name}/*.css
# - project/config/{config_dir}/canvas.component.sdc.{theme}.{machine-name}.yml
```

Use `/commit` or `/pr` to stage and commit.

---

## Theme quick-reference

| Theme | Site alias | Config dir | Site URL |
|---|---|---|---|
| `tryngolza` | `@tryn_nxt.local` | `project/config/tryn_nxt/` | `tryn-nxt.docksal.site` |
| `kytg_nxt` | `@knowtgs.local` | `project/config/kytg_nxt/` | `kytg-nxt.docksal.site` |
