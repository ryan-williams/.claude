---
name: slack-emoji
description: Convert a logo (SVG or PNG) into a ≤256px square PNG suitable for upload as a Slack custom emoji (slack.com/customize/emoji or slackmojis.com). Outside-the-logo stays transparent; if the logo has a central circle/square with transparent cutouts inside, those cutouts get a white fill so they don't disappear on dark themes. Use when the user says "make a slack emoji from X", "extract logo X as slack emoji", "<=256 png for slack", etc.
---

# Logo → Slack emoji PNG

Goal: produce `<name>-slack.png`, 256×256, RGBA, with transparent area outside the logo. If the logo has a containing circle/square/cluster with transparent regions inside (letter cutouts, gaps between cubes), fill those interior regions with white so the emoji reads on dark Slack themes.

Outputs go next to the input file (same directory). Default name: `<input-stem>-slack.png`. If a white-fill variant is also produced, name it `<input-stem>-slack-white.png`.

## Decision tree

Look at the source first (`Read` for SVG, `magick … info:` for PNG, or render+sample). Three buckets:

1. **Open-shape logo** (e.g. a wordmark, a free-standing icon with no enclosed area). No interior to fill. → Just trim + pad + resize.
2. **Containing shape with interior cutouts** (e.g. Whole Foods green disc with text cut out, Zipcar green circle with white Z cut out, a filled square with transparent text). → Composite the rendered logo over a white circle/rect of the right size and position.
3. **Cluster with gaps** (e.g. zarr cube stack, a logomark made of separated tiles). → Build a binary "inside-cluster" mask via morphological close + flood-fill from outside; use that as alpha on a white canvas under the logo.

**Detection — don't get this wrong.** Render the SVG to PNG and *look at it on a dark background*. If the logo's interior has shapes that visually disappear into the dark — that's transparent-where-it-should-be-white, and you're in Case 2 or 3. The most common trap: an SVG contains one big colored path with the foreground letterform cut out of it (rather than a separate white path on top). Rendered on a white preview (like Finder's), it looks correct because the letter shows white from the page background; rendered on a dark Slack theme, the letter goes black/transparent. The Zipcar SVG is exactly this — a single green path with the "Z" cut out, no white path filling the Z. If in doubt, render and `magick … -background "#1a1d21" -flatten` to preview against Slack's dark theme color before deciding.

If still unsure between (1) and (2/3), ask the user.

## Procedure

### 0. Inspect the source

```bash
# SVG: read the file, note viewBox and any explicit shapes
# PNG: check size + alpha density
magick input.png -format "size=%wx%h alpha-mean=%[fx:mean.a]\n" info:
```

For SVG, `cat` / `Read` the file — small SVGs make the containing shape obvious. Look for a single big `<circle>` or `<rect>` (likely case 2), a path with many disjoint subpaths (likely 3), or a single complex path (likely 1).

### 1. Render to a high-res working PNG

Render at 1024–2400px (more if the logo has fine detail or you'll be doing flood-fill). Always render larger than your final 256, then downsample at the end for clean antialiasing.

```bash
rsvg-convert -w 1024 -h 1024 input.svg -o /tmp/work-1024.png
# or if input is already a PNG, use it directly
```

For SVGs whose viewBox doesn't match the logo's bbox (extra padding, off-center), render then trim:

```bash
magick /tmp/work-1024.png -trim +repage /tmp/work-trim.png
magick /tmp/work-trim.png -format "%wx%h\n" info:   # note tight bbox
```

### 2a. Case 1 — open-shape logo (transparent only)

```bash
magick /tmp/work-trim.png -background none -gravity center \
  -extent <maxdim>x<maxdim> -resize 256x256 \
  -colorspace sRGB -type TrueColorAlpha \
  PNG32:<name>-slack.png
```

`<maxdim>` = `max(width, height)` of the trimmed image. The `-extent` pads the shorter side so the logo ends up centered in a square.

### 2b. Case 2 — containing circle/square with cutouts

Render at high-res, build the white shape that matches the logo's *containing* bounds (not the trimmed bbox — match the shape the designer drew), composite the rendered logo on top of it.

For a circle filling the SVG viewBox:
```bash
rsvg-convert -w 1024 -h 1024 input.svg -o /tmp/wf-1024.png
magick -size 1024x1024 xc:none -fill white -draw "circle 512,512 512,0" \
  -colorspace sRGB -type TrueColorAlpha /tmp/wf-disc.png
# IMPORTANT: -compose DstOver puts the second image UNDER the first.
# This avoids the grayscale-promotion gotcha (see below).
magick /tmp/wf-1024.png /tmp/wf-disc.png -compose DstOver -composite /tmp/wf-combined.png
magick /tmp/wf-combined.png -resize 256x256 \
  -colorspace sRGB -type TrueColorAlpha \
  PNG32:<name>-slack-white.png
```

For a rectangle: `-fill white -draw "rectangle 0,0 1023,1023"` (or whatever bounds).

To find the disc's center+radius for the `circle` draw, parse the SVG path. A circle in path notation usually looks like `... a R,R 0 ...` or `... 0 0-R-x-R-x-R S<cx> <cy> <cx> <cy>s<R> R R<R> R...` — the cubic Bézier coordinates encode the radius and the `S<x> <y>` reflection point gives the center. If the circle isn't obvious from the path, render once, find the bbox of the colored region with `-trim`, and use bbox center + half-width as a good-enough approximation.

### 2c. Case 3 — cluster with gaps (mask-based interior fill)

Build a binary inside-cluster mask and use it as alpha on a white canvas. Steps:

1. Extract the alpha channel of the trimmed logo.
2. Threshold + morphological close to seal narrow gaps between cluster elements (the close kernel size depends on gap width — start at `Disk:8`, adjust if mask comes out wrong).
3. Flood-fill from a bordered (0,0) corner using a *distinct intermediate color* (e.g. `rgb(128,128,128)`) so you can later distinguish three regions: content (255 from threshold), unreachable interior (0, the holes you want filled), and outside (your intermediate color).
4. Map: black (interior holes) → white, gray (outside) → black. Result is a binary "inside cluster" mask.
5. Use that mask as alpha on a white canvas, then composite the original logo on top.

```bash
magick /tmp/work-trim.png -channel A -separate /tmp/alpha.png
magick /tmp/alpha.png -threshold 1% -morphology Close Disk:8 \
  -bordercolor black -border 2 \
  -fill "rgb(128,128,128)" -draw "color 0,0 floodfill" \
  -fill white -opaque black \
  -fill black -opaque "rgb(128,128,128)" \
  -shave 2x2 /tmp/mask.png

# Inspect mask: should be ≈high mean if interior is large.
magick /tmp/mask.png -format "mask mean=%[fx:mean]\n" info:

# Build white interior shape, composite logo on top
WH=$(magick /tmp/work-trim.png -format "%wx%h" info:)
magick -size $WH xc:white \
  \( /tmp/mask.png -alpha off \) -compose CopyOpacity -composite \
  PNG32:/tmp/white-fill.png
magick /tmp/white-fill.png /tmp/work-trim.png \
  -compose Over -composite PNG32:/tmp/combined.png

# Pad to square + resize
DIM=$(magick /tmp/combined.png -format "%[fx:max(w,h)]" info:)
magick /tmp/combined.png -background none -gravity center -extent ${DIM}x${DIM} \
  -resize 256x256 -colorspace sRGB -type TrueColorAlpha \
  PNG32:<name>-slack-white.png
```

If `Disk:8` produces a mask with a too-low mean (interior holes still flagged as outside) or too-high mean (outside leaking inward), adjust:
- Mean too low (gaps not sealed) → larger disk (`Disk:12`, `Disk:16`)
- Mean too high (outside region eaten) → smaller disk (`Disk:4`, `Disk:6`) or skip the close entirely
- `Disk:30` is almost always too aggressive — back off

### 2d. Flat raster logos — rebuild from solid color, don't flood-fill the original

When the input is a *raster* (PNG/webp/JPG) flat logo — a couple of solid colors on a solid background — do **not** background-remove by flood-filling the original's alpha. The original's antialiased edge pixels are color↔background *blends*; flood-fill only removes pixels close to the background color, leaving the mid-blend pixels opaque as a visible **halo** (a light fringe of the blended color, very obvious on Slack's dark theme).

Instead, rebuild the logo from solid color:

1. Threshold the (grayscaled) image to a clean 2-tone, build a **silhouette mask** (the whole logo outline incl. enclosed counters) via the flood-fill recipe in 2c.
2. If the logo has enclosed white counters (the hole in a "b"/"o"/"a", etc.) that must read as white on the final, build a second **counter mask**: same flood-fill, but stop after `-fill black -opaque "rgb(128,128,128)"` so only the still-white enclosed region survives.
3. Composite a solid-color result: `magick -size WxH xc:"<logo-color>" \( -size WxH xc:white \) counter-mask.png -compose over -composite` — solid logo color with white punched in at the counters.
4. Apply the silhouette mask as alpha: `magick solid.png silhouette-mask.png -alpha off -compose CopyOpacity -composite PNG32:clean.png`.

Result: pure logo color, pure white counters, crisp haloless edges (the threshold's hard edge antialiases cleanly on the final downscale). Sample the body — it should be the *exact* brand color (`srgba(6,74,122,1)`), not a lightened blend.

For dark, single-color marks (navy, black, dark green…) also produce a **white-badge variant**: composite the clean cutout over a white rounded-square (`-draw "roundrectangle 0,0 W-1,H-1 r,r"`), since the dark color alone is low-contrast on Slack's dark theme.

### 2e. Other raster preprocessing routes

When §2d's full color-rebuild is overkill, two quicker recipes for raster inputs:

- **Solid background with enclosed same-color regions** (e.g. character/face art with white eyes, an "r"/"m" mark with white counters). Flood-fill *alpha* to none from all 4 corners with fuzz (`-fuzz 15-18%`). This removes only border-connected background pixels, leaving enclosed same-color regions intact. A global "white→transparent" would punch holes in those. Some halo may remain at antialiased edges; switch to §2d if it shows on dark theme.

- **Already-transparent source with a baked-in glow/halo** (semi-transparent fringe around the logo, invisible on white preview, ugly on dark). A transparent input isn't automatically clean — preview on dark theme to check. Fix: re-flatten on white (`-background white -flatten`) so the glow merges to white, then rebuild alpha from inverse luminance (`-colorspace Gray -negate`, then `CopyOpacity` onto a solid-black canvas). Glow → white → transparent, leaving haloless ink.

### 3. Verify

Always sample pixels at known interesting points:

```bash
magick <output>.png -format "size=%wx%h\n%[pixel:p{5,5}] (corner)\n%[pixel:p{128,128}] (center)\n" info:
```

Expectations:
- Corner `(5,5)` → `srgba(0,0,0,0)` (transparent)
- For Case 1: center → logo color or transparent (depending on logo)
- For Cases 2/3: a known cutout point → `srgba(255,255,255,1)`; a known logo-color point → that color, fully opaque
- An outside-the-shape point near a corner → transparent

If colors come back as `graya(...)` instead of `srgba(...,1)`, the file got promoted to grayscale (see gotcha below) — re-run with explicit `PNG32:` and `-colorspace sRGB -type TrueColorAlpha`.

### 4. Report

Brief output to user: file path, dimensions, file size. If you produced two variants (with/without white fill), tell them both paths so they can pick.

## Gotchas

- **Grayscale promotion**: ImageMagick auto-saves PNGs as grayscale when the image contains only achromatic pixels (e.g. an all-white disc with transparent surround). If you then composite that disc *over* a colored logo, the result will be grayscale and the logo's color is lost. Two ways to dodge: (a) use `-compose DstOver` so the colored logo is the first/destination image (which is RGBA-color, forcing color output), or (b) explicitly write intermediates with `PNG32:` and `-colorspace sRGB -type TrueColorAlpha`.
- **Composite ordering**: `magick A B -compose Over -composite` puts B *over* A. `-compose DstOver` reverses, putting A over B. Pick the one that keeps your colored layer as the "top" of the operation so color survives.
- **Flood-fill leaks**: If interior gaps are wider than your morphological close kernel, the flood-fill will leak and your "inside" mask will be wrong. Either widen the close (`Disk:8` → `Disk:12`) or hand-paint problem regions before flood-fill.
- **Border for flood-fill**: Always `-bordercolor X -border 2` before `-draw "color 0,0 floodfill"`, then `-shave 2x2`. This guarantees (0,0) is reachable and outside the original content area.
- **Trim before extent**: Always `-trim +repage` before computing the square extent — otherwise the SVG's stray transparent padding offsets the centering.
- **Final size**: Slack's hard cap is 128KB and 256×256 max for custom emoji. PNGs at 256² with reasonable detail come in well under 128KB; if one doesn't, drop to 192×192 or simplify the logo.
