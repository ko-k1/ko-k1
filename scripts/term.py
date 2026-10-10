"""Shared look for the profile SVGs: themes, embedded font and terminal window."""

import base64
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
GLYPHS = "╔╚═─━·→█★●"  # non-ASCII glyphs kept in the font subset

USER, HOST = "ko-k1", "github.com"

THEMES = {
    "dark": dict(
        bg="#0d1117", bar="#161b22", border="#30363d", fg="#e6edf3", muted="#7d8590",
        accent="#a08bff", grad=("#7f63f9", "#d66cf5"),
        ansi=["#484f58", "#ff7b72", "#3fb950", "#d29922", "#58a6ff", "#bc8cff", "#39c5cf", "#b1bac4"],
        bright=["#6e7681", "#ffa198", "#56d364", "#e3b341", "#79c0ff", "#d2a8ff", "#56d4dd", "#f0f6fc"],
        heat=["#161b22", "#2f2766", "#4c39b0", "#7f63f9", "#bba8ff"],
    ),
    "light": dict(
        bg="#ffffff", bar="#f6f8fa", border="#d0d7de", fg="#1f2328", muted="#656d76",
        accent="#5f3efb", grad=("#5f3efb", "#ce3ef1"),
        ansi=["#24292f", "#cf222e", "#116329", "#4d2d00", "#0969da", "#8250df", "#1b7c83", "#6e7781"],
        bright=["#57606a", "#a40e26", "#1a7f37", "#633c01", "#218bff", "#a475f9", "#3192aa", "#8c959f"],
        heat=["#ebedf0", "#d6ccfe", "#a993fd", "#7a5cfb", "#4a25df"],
    ),
}

FS, CW, LH = 14, 8.4, 20  # font size, char width (0.6em), line height
PAD, BAR = 44, 34
TOP = BAR + 30  # first prompt baseline


def font_face(weight, name):
    data = base64.b64encode((ROOT / "src/font" / name).read_bytes()).decode()
    return (f"@font-face{{font-family:'JBM';font-weight:{weight};"
            f"src:url(data:font/woff2;base64,{data}) format('woff2')}}")


def prompt(y, tail):
    return (f'<text x="{PAD}" y="{y}"><tspan class="m">╔</tspan><tspan class="a b">[{USER}@{HOST}]</tspan>: ~</text>'
            f'<text x="{PAD}" y="{y + LH}"><tspan class="m">╚═</tspan><tspan class="a b">$</tspan> {tail}</text>')


def window(t, w, h, title, desc, defs=""):
    """Opening tags, styles and window chrome; the caller appends content and '</svg>'."""
    out = []
    o = out.append
    o(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
      f'role="img" aria-labelledby="t d">')
    o(f'<title id="t">{USER}@{HOST} — {escape(title)}</title>')
    o(f'<desc id="d">{escape(desc)}</desc>')
    o("<style>")
    o(font_face(400, "jbm-regular.woff2"))
    o(font_face(700, "jbm-bold.woff2"))
    o(f"text{{font-family:'JBM',ui-monospace,Menlo,Consolas,monospace;font-size:{FS}px;fill:{t['fg']};white-space:pre}}"
      f".m{{fill:{t['muted']}}}.a{{fill:{t['accent']}}}.b{{font-weight:700}}"
      f".bar{{font-size:12px;fill:{t['muted']}}}"
      ".cur{animation:blink 1.1s steps(1) infinite}@keyframes blink{50%{opacity:0}}"
      "@media (prefers-reduced-motion:reduce){.cur{animation:none}}")
    o("</style>")
    o(f'<defs>{defs}<clipPath id="c"><rect width="{w}" height="{h}" rx="12"/></clipPath></defs>')

    o(f'<g clip-path="url(#c)"><rect width="{w}" height="{h}" fill="{t["bg"]}"/>'
      f'<rect width="{w}" height="{BAR}" fill="{t["bar"]}"/>'
      f'<line x1="0" y1="{BAR}" x2="{w}" y2="{BAR}" stroke="{t["border"]}"/></g>')
    o(f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="11.5" fill="none" stroke="{t["border"]}"/>')
    for i in range(3):
        o(f'<circle cx="{20 + i * 18}" cy="{BAR / 2}" r="5.5" fill="{t["border"]}"/>')
    o(f'<text class="bar" x="{w / 2}" y="{BAR / 2 + 4}" text-anchor="middle">kish — {USER}@{HOST}: ~</text>')
    return out


def cursor(t, y):
    """Closing prompt at baseline y with a blinking block cursor."""
    return (prompt(y, "") + f'\n<rect class="cur" x="{PAD + 4 * CW}" y="{y + LH - FS + 1}" '
            f'width="{CW}" height="{FS + 3}" fill="{t["accent"]}"/>')


def write(name, render):
    for theme, t in THEMES.items():
        path = ROOT / "src" / f"{name}-{theme}.svg"
        path.write_text(render(t), encoding="utf-8")
        print(path.relative_to(ROOT), path.stat().st_size, "bytes")
