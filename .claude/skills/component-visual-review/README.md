# component-visual-review

Pixel-perfect visual review of a Drupal SDC component against a Figma design or reference image.

## Overview

Iterative styling workflow that extracts exact design values from Figma — colors, gradients, SVG paths, typography, and spacing — and applies them to the component's CSS and Twig files. Takes before/after screenshots via Chrome DevTools at both desktop (1280px) and mobile (390px) breakpoints, compares against the reference, and iterates until the component matches.

**Core rule: no value is guessed.** Every number comes from the design reference or is explicitly confirmed by you.

Falls back to attached images when Figma is unavailable, but prompts for exact values (hex colors, font sizes, weights) that can't be reliably read from an image.

This skill is typically invoked automatically at the end of `/component-create`, but can be run standalone on any existing component.

## Usage

```
/component-visual-review
```

You will be prompted for:

| Input | Required | Description |
|---|---|---|
| Component directory | Yes | e.g. `project/themes/tryngolza/components/my-component/` |
| Local preview URL | Yes | e.g. `http://tryn-nxt.docksal.site/component-test` |
| Desktop design reference | Yes | Figma URL (preferred) or attached image |
| Mobile design reference | Optional | Figma URL or image; defaults to proportional scaling of desktop |

## What it does

1. Extracts exact values from Figma via MCP: fills, gradients (including gradient strokes), SVG paths, sizing, spacing, and typography — or collects values visually from an attached image
2. Takes a baseline screenshot at desktop and mobile before making any changes
3. Applies extracted values to the component CSS and Twig files
4. Screenshots after each round of changes, compares against the reference, and iterates
5. Stops after 3 rounds if pixel-level differences remain and surfaces them for your judgment
6. Final sign-off checklist: colors, gradients, SVG paths, sizes, spacing, and mobile layout

## Dependencies

- **Figma MCP** (`mcp__plugin_figma_figma__*`) — preferred for exact value extraction; connected via claude.ai Figma plugin
- **Chrome DevTools MCP** (`mcp__chrome-devtools__*`) — for viewport screenshots; Chrome must be running and the DevTools MCP server must be active
- Docksal site running at the local preview URL
