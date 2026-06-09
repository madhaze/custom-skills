# component-create

End-to-end Drupal SDC component creation for Canvas themes.

## Overview

Creates a complete Drupal Single Directory Component (SDC) that integrates with the Canvas layout builder. Accepts requirements from any combination of Jira ticket, Figma design URL, attached images, or written description. Generates all required files, exports Canvas config via Drush, verifies the component renders, then hands off to `/component-visual-review` for pixel-perfect styling.

This skill is project-specific to the `ionis-tryn` repo and its two Canvas themes.

## Usage

```
/component-create
```

You will be prompted for:

| Input | Required | Description |
|---|---|---|
| Theme name | Yes | `tryngolza` or `kytg_nxt` |
| Machine name | Yes | Kebab-case component name, e.g. `my-icon-card` |
| Jira ticket ID | At least one | e.g. `TRYN-843` — provides full acceptance criteria |
| Written description | At least one | Short description of the component and its variants |
| Figma desktop URL | At least one | Preferred design source |
| Attached images | At least one | Screenshots from the designer |
| Figma mobile URL | Optional | Only if mobile layout differs meaningfully from desktop |

## What it does

1. Validates that the theme directory exists and the component name isn't already taken
2. Pulls requirements from Jira (via MCP) and/or extracts specs from Figma (via MCP)
3. Presents a spec summary — props, Canvas field types, mobile strategy — for your confirmation
4. Writes `.component.yml`, `.twig`, and a CSS skeleton (values left empty for `/component-visual-review`)
5. Clears Drupal cache and exports Canvas config via `fin drush cex`
6. Verifies the component renders without PHP or Twig errors
7. Invokes `/component-visual-review` for styling against the design reference
8. Exports final config and prompts you to commit with `/commit` or `/pr`

## Dependencies

- **Figma MCP** — for Figma-sourced specs (connected via claude.ai Figma plugin)
- **Atlassian MCP** — for Jira ticket requirements (connected via claude.ai Atlassian connector)
- **Docksal** (`fin`) — must be running with the target site alias responding to `drush status`
- [`component-visual-review`](../component-visual-review/README.md) skill
- The `ionis-tryn` repo checked out locally with both theme directories present

## Theme quick-reference

| Theme | Drush alias | Config dir | Local URL |
|---|---|---|---|
| `tryngolza` | `@tryn_nxt.local` | `project/config/tryn_nxt/` | `tryn-nxt.docksal.site` |
| `kytg_nxt` | `@knowtgs.local` | `project/config/kytg_nxt/` | `kytg-nxt.docksal.site` |
