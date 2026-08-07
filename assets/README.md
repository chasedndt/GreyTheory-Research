# Brand assets

## The mark

Three paths approach a gate. Two stop. One passes through.

That is not decoration — it is the product. The execution gate has seventeen ways to deny and one to allow, and that ratio is the whole thesis: the system's default is refusal, and what gets through has earned it. The amber bar is the gate itself, which is why it is the only coloured element. Authority is the thing that colours everything else.

It reads at 16px, works in one colour, and does not depend on a typeface.

## Files

| File | Use |
|---|---|
| `logo/mark.svg` | Primary mark. Uses `currentColor` for the paths, so it inherits the surrounding text colour and works on light or dark. |
| `logo/mark-mono.svg` | Single-colour version for print, embroidery, or anywhere amber cannot be reproduced. |
| `logo/icon.svg` | App icon with the dark rounded-square container. |
| `logo/wordmark.svg` | Mark plus "GreyTheory AI". Uses a system font stack — for fixed rendering use the PNG. |
| `logo/icon-{32,64,128,256,512}.png` | Raster icons. |
| `logo/favicon.ico` | Multi-resolution favicon, 16–256px. |
| `social/social-preview.png` | GitHub social preview, 1280×640 — the size GitHub actually uses. |
| `social/banner.png` | README banner, 1200×300. |

The SVGs are the source of truth. `render.py` draws the raster files from the same geometry; run `python assets/render.py` after any change to the mark so they cannot drift apart.

## Colour

| Role | Hex | Notes |
|---|---|---|
| Ink | `#0B0F19` | Background on dark surfaces |
| Paper | `#FFFFFF` | Background on light surfaces |
| Fog | `#E5E7EB` | Paths on dark |
| Grey | `#6B7280` | Secondary text |
| **Authority** | `#F59E0B` | The gate. The only accent in the mark. |
| Proof | `#10B981` | Allowed states in diagrams and the dashboard |
| Denial | `#EF4444` | Refusals and alerts. Never in the mark. |

Amber and emerald carry meaning across the diagrams, the dashboard and the mark: amber is authority, emerald is proof, red is refusal. Keep it that way — a reader who learns the code once should not have to relearn it.

## Using it

**Do**

- Give the mark clear space of at least the height of its gate bar.
- Use `currentColor` versions inside text so the mark tracks the theme.
- Keep amber on the gate bar only.

**Don't**

- Recolour the gate bar. It is the one element carrying meaning.
- Stretch, rotate, or add effects.
- Place the mark on a busy image. It is a thin monoline glyph and it disappears.
- Pair it with claims the capability register does not support. The identity is not exempt from the rule that governs the rest of the project: nothing described as working unless it works.

## Setting the GitHub social preview

It is not automatic — the file being in the repo does nothing on its own:

**Settings → General → Social preview → Upload an image** → `assets/social/social-preview.png`
