#!/usr/bin/env python3
"""Isometric contribution calendar, built from GitHub's own numbers.

Two reasons this exists rather than using metrics' isocalendar plugin:

  1. metrics undercounts. Its card reported ~1.04 contributions/day, roughly
     379 for the year, against GitHub's actual 1,275. Private contributions
     are the bulk of that gap.
  2. metrics renders its text inside <foreignObject>, which browsers do not
     draw when an SVG is loaded as an image — which is how GitHub serves
     README images. That forced PNG output. This file uses <polygon> and
     <text> only, so it renders as SVG.

Data comes from the GraphQL contributionCalendar, which includes private
contributions because "Include private contributions on my profile" is on.

Usage: python3 scripts/make-calendar.py [output.svg]
"""
import json
import subprocess
import sys

USER = "gconsentini"
OUT = sys.argv[1] if len(sys.argv) > 1 else "contributions.svg"

QUERY = """
{ user(login: "%s") { contributionsCollection { contributionCalendar {
    totalContributions
    weeks { contributionDays { contributionCount date weekday } }
} } } }
""" % USER

# GitHub's contribution greens, plus darker shades for the cube sides.
LEVELS = [
    ("#ebedf0", "#d8dade", "#c6c8cc"),
    ("#9be9a8", "#7cbb86", "#68a071"),
    ("#40c463", "#339d4f", "#2b8543"),
    ("#30a14e", "#26813e", "#206e35"),
    ("#216e39", "#1a582d", "#164a26"),
]

TW, TH = 6, 3          # half-width, half-height of an isometric tile
MAX_BAR = 34           # tallest cube, in px
PAD = 18


def fetch():
    raw = subprocess.run(
        ["gh", "api", "graphql", "-f", "query=" + QUERY,
         "--jq", ".data.user.contributionsCollection.contributionCalendar"],
        capture_output=True, text=True, check=True,
    ).stdout
    return json.loads(raw)


def streaks(days):
    best = cur = run = 0
    for d in days:
        if d["contributionCount"] > 0:
            run += 1
            best = max(best, run)
        else:
            run = 0
    for d in reversed(days):
        if d["contributionCount"] > 0:
            cur += 1
        else:
            break
    return cur, best


def level(count, mx):
    if count <= 0:
        return 0
    q = count / mx
    return 1 if q <= 0.25 else 2 if q <= 0.5 else 3 if q <= 0.75 else 4


def build(cal):
    weeks = cal["weeks"]
    days = [d for w in weeks for d in w["contributionDays"]]
    total = cal["totalContributions"]
    active = sum(1 for d in days if d["contributionCount"] > 0)
    mx = max(d["contributionCount"] for d in days)
    cur, best = streaks(days)

    ncols = len(weeks)
    ox = PAD + 6 * TW + TW
    oy = PAD + MAX_BAR + 16
    cal_w = ox + (ncols - 1) * TW + TW + PAD
    panel_x = cal_w + 6
    width = panel_x + 250
    height = oy + (ncols - 1 + 6) * TH + TH * 2 + PAD + 8

    cells = []
    for col, wk in enumerate(weeks):
        for d in wk["contributionDays"]:
            row = d["weekday"]
            cells.append((col + row, col, row, d["contributionCount"]))
    cells.sort(key=lambda c: (c[0], c[1]))   # painter's order: back to front

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="Isometric contribution calendar: {total} contributions over {active} active days">',
        '<style>'
        '.h{font:600 15px -apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif;fill:#61afef}'
        '.k{font:400 12px -apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif;fill:#768390}'
        '.v{font:600 12px -apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif;fill:#8b949e}'
        '</style>',
        f'<text class="h" x="{PAD}" y="22">Contributions calendar</text>',
    ]

    for _, col, row, count in cells:
        lv = level(count, mx)
        top, left, right = LEVELS[lv]
        h = 0 if count <= 0 else 2 + (count / mx) * MAX_BAR
        x = ox + (col - row) * TW
        base = oy + (col + row) * TH
        ty = base - h
        # top face
        out.append(
            f'<polygon points="{x},{ty} {x+TW},{ty+TH} {x},{ty+TH*2} {x-TW},{ty+TH}" fill="{top}"/>'
        )
        if h > 0:
            out.append(
                f'<polygon points="{x-TW},{ty+TH} {x},{ty+TH*2} {x},{ty+TH*2+h} {x-TW},{ty+TH+h}" fill="{left}"/>'
            )
            out.append(
                f'<polygon points="{x},{ty+TH*2} {x+TW},{ty+TH} {x+TW},{ty+TH+h} {x},{ty+TH*2+h}" fill="{right}"/>'
            )

    stats = [
        ("Contributions", f"{total:,}"),
        ("Active days", f"{active} of {len(days)}"),
        ("Best streak", f"{best} days"),
        ("Current streak", f"{cur} days"),
        ("Busiest day", f"{mx} contributions"),
    ]
    y = 52
    for k, v in stats:
        out.append(f'<text class="k" x="{panel_x}" y="{y}">{k}</text>')
        out.append(f'<text class="v" x="{panel_x + 240}" y="{y}" text-anchor="end">{v}</text>')
        y += 22

    out.append('</svg>')
    return "\n".join(out), total, active


if __name__ == "__main__":
    svg, total, active = build(fetch())
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print(f"wrote {OUT}: {total:,} contributions across {active} active days")
