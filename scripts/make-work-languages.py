#!/usr/bin/env python3
"""Build a static language chart from real data.

Uses plain <rect>/<text> only — no <foreignObject> — so GitHub renders it
directly in a README, unlike metrics output which needs PNG rasterisation.
"""
import io

# Measured from repos/LendingHome/lendinghome-monolith/languages
LANGS = [
    ("Ruby",       38.30, "#701516"),
    ("Kotlin",     19.84, "#A97BFF"),
    ("TypeScript", 13.48, "#3178C6"),
    ("HTML",       10.12, "#e34c26"),
    ("JavaScript",  5.77, "#f1e05a"),
    ("Gherkin",     3.61, "#5B2063"),
    ("Other",       8.88, "#8b949e"),
]

W, PAD = 480, 16
BAR_Y, BAR_H = 58, 10
COL_W = (W - PAD * 2) / 2

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

rows = (len(LANGS) + 1) // 2
H = BAR_Y + BAR_H + 22 + rows * 19 + PAD

out = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
    f'viewBox="0 0 {W} {H}" role="img" aria-label="Language mix of the codebase I work in daily">',
    '<style>'
    '.t{font:600 15px -apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif;fill:#61afef}'
    '.s{font:400 11px -apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif;fill:#8b949e}'
    '.l{font:400 12px -apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif;fill:#768390}'
    '.p{font:400 12px -apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif;fill:#8b949e}'
    '</style>',
    f'<text class="t" x="{PAD}" y="24">Languages I work in daily</text>',
    f'<text class="s" x="{PAD}" y="42">Primary work codebase &#183; 1,735 commits authored</text>',
]

# stacked bar, with rounded ends via a clip path
out.append(f'<clipPath id="r"><rect x="{PAD}" y="{BAR_Y}" width="{W-PAD*2}" height="{BAR_H}" rx="5"/></clipPath>')
out.append('<g clip-path="url(#r)">')
x = PAD
for _, pct, color in LANGS:
    w = (W - PAD * 2) * pct / 100
    out.append(f'<rect x="{x:.2f}" y="{BAR_Y}" width="{w:.2f}" height="{BAR_H}" fill="{color}"/>')
    x += w
out.append('</g>')

# two-column legend
y0 = BAR_Y + BAR_H + 26
for i, (name, pct, color) in enumerate(LANGS):
    col, row = i % 2, i // 2
    cx = PAD + col * COL_W
    cy = y0 + row * 19
    out.append(f'<circle cx="{cx+5:.1f}" cy="{cy-4:.1f}" r="5" fill="{color}"/>')
    out.append(f'<text class="l" x="{cx+17:.1f}" y="{cy}">{esc(name)}</text>')
    out.append(f'<text class="p" x="{cx+COL_W-24:.1f}" y="{cy}" text-anchor="end">{pct:.2f}%</text>')

out.append('</svg>')
io.open("work-languages.svg", "w", encoding="utf-8").write("\n".join(out))
print(f"wrote work-languages.svg ({W}x{H})")
print("sum:", round(sum(p for _, p, _ in LANGS), 2), "%")
