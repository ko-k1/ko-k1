"""Render the neofetch card: src/card-dark.svg and src/card-light.svg.

    python3 scripts/card.py      (stdlib only; `uv run scripts/card.py` works too)

Edit ART / INFO below, then re-run. The font is a JetBrains Mono subset
(ASCII + the glyphs in term.GLYPHS); characters outside it fall back to the
viewer's monospace font.
"""

from xml.sax.saxutils import escape

from term import CW, FS, HOST, LH, PAD, TOP, USER, cursor, prompt, window, write

ART = r"""
               /kkkkkk/
              /kkkkkk/
             /kkkkkk/
            /kkkkkk/
           /kkkkkk/
          /kkkkkk/        .nm"
         /kkkkkk/      ,nkkk/
        /kkkkkk/   .nmkkkkk/
       /kkkkkk/ .nkkkkkkkk/
      /kkkkkkkkkkkkkkP*'
     /kkkkkkkkkkkP*'
    /kkkkkkkk<'
   /kkkkkkkkkkmn.,
  /kkkkkk/"*kkklkkkmn.,
 /kkkkkk/     '"*kkkkkkkn.
/kkkkkk/           >kkkkkkk>
                ,kkkkkkk"'
            ,kkkkkkk*"'
        ,jkkilkkkP*'
""".strip("\n").splitlines()

INFO = [
    ("OS", "NixOS · Windows · macOS"),
    ("Host", "Earth"),
    ("Kernel", "Rust, systems & pentesting"),
    ("Uptime", "since 2000-06-29"),
    ("Packages", "~10 GB of code"),
    ("Shell", "kish 0.0.1a"),
    ("DE", "none, CLI is better"),
    ("WM", "Hyprland · niri"),
    ("Terminal", "kitty"),
    ("Langs", "Rust · TypeScript · Python · Nix"),
    ("Org", "@kxki-dev"),
    ("Site", "kxki.dev"),
    ("CPU", "Human-Brain 4790K"),
    ("GPU", "Human-Brain HD Graphics 4600"),
]

ART_X = PAD
INFO_X = PAD + max(map(len, ART)) * CW + 48
W = round(INFO_X + max(len(f"{k}: {v}") for k, v in INFO) * CW + PAD)
ART_Y = TOP + 2 * LH + 12
END_Y = ART_Y + (len(ART) - 1) * LH + 40  # closing prompt baseline
H = END_Y + LH + 28


def render(t):
    grad = (f'<linearGradient id="g" gradientUnits="userSpaceOnUse" x1="0" y1="{ART_Y - FS}" x2="0" y2="{ART_Y + len(ART) * LH}">'
            f'<stop offset="0" stop-color="{t["grad"][0]}"/><stop offset="1" stop-color="{t["grad"][1]}"/></linearGradient>')
    out = window(t, W, H, "neofetch", "; ".join(f"{k}: {v}" for k, v in INFO), defs=grad)
    o = out.append

    o(prompt(TOP, "neofetch"))

    # logo
    o(f'<text x="{ART_X}" y="{ART_Y}" xml:space="preserve" class="b" fill="url(#g)" style="fill:url(#g)">')
    for i, line in enumerate(ART):
        o(f'<tspan x="{ART_X}" y="{ART_Y + i * LH}">{escape(line)}</tspan>')
    o("</text>")

    # info
    y = ART_Y
    o(f'<text x="{INFO_X}" y="{y}" class="b"><tspan class="a">{USER}</tspan>@<tspan class="a">{HOST}</tspan></text>')
    y += LH
    o(f'<text x="{INFO_X}" y="{y}" class="m">{"-" * len(USER + "@" + HOST)}</text>')
    for k, v in INFO:
        y += LH
        o(f'<text x="{INFO_X}" y="{y}" xml:space="preserve"><tspan class="a b">{escape(k)}</tspan>: {escape(v)}</text>')
    y += LH  # blank line, then the colour blocks
    for row in (t["ansi"], t["bright"]):
        y += LH
        for i, c in enumerate(row):
            o(f'<rect x="{INFO_X + i * 3 * CW}" y="{y - FS + 1}" width="{3 * CW}" height="{LH - 2}" fill="{c}"/>')

    o(cursor(t, END_Y))
    o("</svg>")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    write("card", render)
