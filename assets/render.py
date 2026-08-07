"""Render the raster assets GitHub and the web need.

The SVGs in `logo/` are the source of truth. This draws the same geometry with
Pillow, because GitHub's social preview and favicons want raster and there is
no SVG rasteriser in this environment.

Run:  python assets/render.py
"""

# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 ChaseInTech

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent

INK = (11, 15, 25)
PAPER = (255, 255, 255)
FOG = (229, 231, 235)
GREY = (156, 163, 175)
AMBER = (245, 158, 11)
EMERALD = (16, 185, 129)

FONT_CANDIDATES = (
    "C:/Windows/Fonts/segoeuisb.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
)
LIGHT_FONT_CANDIDATES = (
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
)


def load_font(size: int, light: bool = False) -> ImageFont.FreeTypeFont:
    for path in LIGHT_FONT_CANDIDATES if light else FONT_CANDIDATES:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default(size)


def draw_mark(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    size: int,
    *,
    fg: tuple[int, int, int],
    gate: tuple[int, int, int] = AMBER,
    denied_alpha: float = 0.35,
) -> None:
    """The mark, on a 32-unit grid scaled to ``size``.

    Three paths approach. Two stop at the gate. One passes through. That ratio
    is the product, so it is the logo.
    """
    u = size / 32
    width = max(2, round(2.6 * u))

    def blend(colour: tuple[int, int, int], alpha: float) -> tuple[int, int, int]:
        background = INK if sum(fg) > 380 else PAPER
        return tuple(
            round(c * alpha + b * (1 - alpha)) for c, b in zip(colour, background)
        )

    faded = blend(fg, denied_alpha)
    for cy in (10, 22):  # denied
        draw.line(
            [(x + 4 * u, y + cy * u), (x + 13 * u, y + cy * u)],
            fill=faded, width=width, joint="curve",
        )
    draw.line(  # allowed
        [(x + 4 * u, y + 16 * u), (x + 28 * u, y + 16 * u)],
        fill=fg, width=width, joint="curve",
    )
    draw.line(  # the gate
        [(x + 19 * u, y + 5 * u), (x + 19 * u, y + 27 * u)],
        fill=gate, width=width, joint="curve",
    )


def render_social_preview() -> Path:
    """GitHub social preview. 1280x640 is the size GitHub actually wants."""
    scale = 2
    w, h = 1280 * scale, 640 * scale
    image = Image.new("RGB", (w, h), INK)
    draw = ImageDraw.Draw(image)

    mark_x, mark_y, mark_size = 96 * scale, 96 * scale, 132 * scale
    draw_mark(draw, mark_x, mark_y, mark_size, fg=FOG)

    # The one path that passed, continuing off the edge. Aligned to the mark's
    # own allowed ray rather than to the middle of the canvas.
    ray_y = mark_y + round(mark_size * 16 / 32)
    ray_start = mark_x + round(mark_size * 28 / 32)
    draw.line([(ray_start, ray_y), (w, ray_y)], fill=(26, 34, 51), width=2 * scale)

    title = load_font(84 * scale)
    subtitle = load_font(38 * scale, light=True)
    small = load_font(27 * scale, light=True)

    draw.text((96 * scale, 268 * scale), "GreyTheory AI", font=title, fill=PAPER)
    draw.text(
        (96 * scale, 382 * scale),
        "Proof-first security research control plane",
        font=subtitle,
        fill=GREY,
    )

    line_y = 470 * scale
    draw.line(
        [(96 * scale, line_y), (300 * scale, line_y)], fill=AMBER, width=4 * scale
    )

    draw.text(
        (96 * scale, 506 * scale),
        "Converts authorisation into evidence \u2014 and refuses to move without either.",
        font=small,
        fill=FOG,
    )
    draw.text(
        (96 * scale, 552 * scale),
        "Apache-2.0  \u00b7  zero runtime dependencies  \u00b7  no network in the core",
        font=small,
        fill=(107, 114, 128),
    )

    image = image.resize((1280, 640), Image.LANCZOS)
    out = HERE / "social" / "social-preview.png"
    image.save(out, optimize=True)
    return out


def render_banner() -> Path:
    """A narrower strip for the top of the README."""
    scale = 2
    w, h = 1200 * scale, 300 * scale
    image = Image.new("RGB", (w, h), INK)
    draw = ImageDraw.Draw(image)

    draw_mark(draw, 72 * scale, 66 * scale, 96 * scale, fg=FOG)

    title = load_font(58 * scale)
    subtitle = load_font(26 * scale, light=True)
    draw.text((200 * scale, 84 * scale), "GreyTheory AI", font=title, fill=PAPER)
    draw.text(
        (202 * scale, 158 * scale),
        "Proof-first security research control plane",
        font=subtitle,
        fill=GREY,
    )
    draw.line(
        [(202 * scale, 206 * scale), (330 * scale, 206 * scale)],
        fill=AMBER,
        width=3 * scale,
    )

    image = image.resize((1200, 300), Image.LANCZOS)
    out = HERE / "social" / "banner.png"
    image.save(out, optimize=True)
    return out


def render_icons() -> list[Path]:
    """App icon at the sizes a browser, a repo and a desktop each want."""
    written: list[Path] = []
    for size in (512, 256, 128, 64, 32):
        scale = 4 if size <= 64 else 1
        canvas = size * scale
        image = Image.new("RGB", (canvas, canvas), INK)
        draw = ImageDraw.Draw(image)
        inset = canvas * 0.16
        draw_mark(
            draw,
            round(inset),
            round(inset),
            round(canvas - inset * 2),
            fg=FOG,
        )
        if scale > 1:
            image = image.resize((size, size), Image.LANCZOS)
        out = HERE / "logo" / f"icon-{size}.png"
        image.save(out, optimize=True)
        written.append(out)

    # Multi-resolution .ico for the website favicon.
    base = Image.open(HERE / "logo" / "icon-256.png")
    ico = HERE / "logo" / "favicon.ico"
    base.save(ico, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    written.append(ico)
    return written


def main() -> None:
    for path in [render_social_preview(), render_banner(), *render_icons()]:
        print(f"wrote {path.relative_to(HERE.parent)}")


if __name__ == "__main__":
    main()
