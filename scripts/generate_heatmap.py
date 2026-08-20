#!/usr/bin/env python3
"""
Fetch real GitHub contribution data for a user and generate a red/crimson
contribution-heatmap SVG styled to match a cyberpunk profile README.

Usage:
    python generate_heatmap.py <username> <output_path>

Requires:
    - GITHUB_TOKEN environment variable (for authenticated GraphQL queries)
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone

# ── Colour palette ─────────────────────────────────────────────────────────
BG         = "#080A0F"
PANEL_BG   = "#0B0D12"
EMPTY      = "#16191F"
LEVEL_1    = "#3A1117"
LEVEL_2    = "#6F1722"
LEVEL_3    = "#B51F32"
LEVEL_4    = "#FF3347"
BORDER     = "#FF3347"
TEXT_MONTH  = "#858994"
TEXT_DAY    = "#858994"
TEXT_LEGEND = "#858994"
TEXT_TITLE  = "#F2F2F4"
ACCENT      = "#FF3347"

LEVEL_MAP = {
    "NONE":          EMPTY,
    "FIRST_QUARTILE": LEVEL_1,
    "SECOND_QUARTILE": LEVEL_2,
    "THIRD_QUARTILE": LEVEL_3,
    "FOURTH_QUARTILE": LEVEL_4,
}

# ── GitHub GraphQL ─────────────────────────────────────────────────────────
QUERY = """
query($username: String!) {
  user(login: $username) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            contributionCount
            contributionLevel
            date
            weekday
          }
        }
      }
    }
  }
}
"""


def fetch_contributions(username: str, token: str) -> dict:
    """Fetch contribution calendar via GitHub GraphQL API."""
    payload = json.dumps({"query": QUERY, "variables": {"username": username}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "contribution-heatmap-generator",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"ERROR: GitHub API returned HTTP {e.code}: {body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"ERROR: Could not reach GitHub API: {e.reason}", file=sys.stderr)
        sys.exit(1)

    if "errors" in data:
        print(f"ERROR: GraphQL errors: {json.dumps(data['errors'])}", file=sys.stderr)
        sys.exit(1)

    user = data.get("data", {}).get("user")
    if user is None:
        print(f"ERROR: User '{username}' not found on GitHub.", file=sys.stderr)
        sys.exit(1)

    return user["contributionsCollection"]["contributionCalendar"]


# ── SVG generation ─────────────────────────────────────────────────────────
CELL   = 13       # cell size px
GAP    = 3        # gap between cells
RADIUS = 2        # rounded corner radius
LEFT_LABEL_W = 36 # space for weekday labels
TOP_LABEL_H  = 20 # space for month labels
PADDING = 28      # outer padding

WEEKDAY_LABELS = ["", "Mon", "", "Wed", "", "Fri", ""]


def generate_svg(calendar: dict, username: str) -> str:
    weeks = calendar["weeks"]
    total = calendar["totalContributions"]
    num_weeks = len(weeks)

    grid_w = num_weeks * (CELL + GAP) - GAP
    grid_h = 7 * (CELL + GAP) - GAP

    inner_w = LEFT_LABEL_W + grid_w + 30       # extra right margin for legend
    inner_h = TOP_LABEL_H + grid_h

    svg_w = inner_w + PADDING * 2 + 20
    svg_h = inner_h + PADDING * 2 + 80         # extra bottom for legend

    origin_x = PADDING + 10 + LEFT_LABEL_W
    origin_y = PADDING + 10 + TOP_LABEL_H

    parts = []

    # ── Root ───────────────────────────────────────────────────────────────
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_w}" height="{svg_h}" '
        f'viewBox="0 0 {svg_w} {svg_h}">'
    )

    # ── Defs: glow filter ──────────────────────────────────────────────────
    parts.append("""  <defs>
    <filter id="border-glow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="0" dy="0" stdDeviation="3" flood-color="#FF3347" flood-opacity="0.35"/>
    </filter>
  </defs>""")

    # ── Background ─────────────────────────────────────────────────────────
    parts.append(f'  <rect width="{svg_w}" height="{svg_h}" rx="0" fill="{BG}"/>')

    # ── Panel with cut corners ─────────────────────────────────────────────
    panel_x, panel_y = 8, 8
    panel_w, panel_h = svg_w - 16, svg_h - 16
    cut = 12
    panel_path = (
        f"M {panel_x + cut} {panel_y} "
        f"L {panel_x + panel_w - cut} {panel_y} "
        f"L {panel_x + panel_w} {panel_y + cut} "
        f"L {panel_x + panel_w} {panel_y + panel_h - cut} "
        f"L {panel_x + panel_w - cut} {panel_y + panel_h} "
        f"L {panel_x + cut} {panel_y + panel_h} "
        f"L {panel_x} {panel_y + panel_h - cut} "
        f"L {panel_x} {panel_y + cut} Z"
    )
    parts.append(
        f'  <path d="{panel_path}" fill="{PANEL_BG}" '
        f'stroke="{BORDER}" stroke-width="1.2" stroke-opacity="0.5" '
        f'filter="url(#border-glow)"/>'
    )

    # ── Corner accents ─────────────────────────────────────────────────────
    cx, cy = panel_x, panel_y
    cw, ch = panel_w, panel_h
    accent_len = 24
    for path_d in [
        f"M {cx} {cy+cut+accent_len} L {cx} {cy+cut} L {cx+cut} {cy} L {cx+cut+accent_len} {cy}",
        f"M {cx+cw-cut-accent_len} {cy} L {cx+cw-cut} {cy} L {cx+cw} {cy+cut} L {cx+cw} {cy+cut+accent_len}",
        f"M {cx+cw} {cy+ch-cut-accent_len} L {cx+cw} {cy+ch-cut} L {cx+cw-cut} {cy+ch} L {cx+cw-cut-accent_len} {cy+ch}",
        f"M {cx+cut+accent_len} {cy+ch} L {cx+cut} {cy+ch} L {cx} {cy+ch-cut} L {cx} {cy+ch-cut-accent_len}",
    ]:
        parts.append(
            f'  <path d="{path_d}" fill="none" stroke="{ACCENT}" stroke-width="2"/>'
        )

    # ── Title ──────────────────────────────────────────────────────────────
    title_y = PADDING + 6
    parts.append(
        f'  <text x="{PADDING + 14}" y="{title_y + 14}" '
        f'fill="{TEXT_TITLE}" font-family="\'JetBrains Mono\', monospace" '
        f'font-size="14" font-weight="700" letter-spacing="1.5">'
        f'CONTRIBUTION ACTIVITY</text>'
    )
    parts.append(
        f'  <text x="{svg_w - PADDING - 14}" y="{title_y + 14}" '
        f'fill="{TEXT_MONTH}" font-family="\'JetBrains Mono\', monospace" '
        f'font-size="12" font-weight="500" text-anchor="end">'
        f'{total:,} contributions</text>'
    )

    # ── Thin accent line below title ───────────────────────────────────────
    line_y = title_y + 24
    parts.append(
        f'  <line x1="{PADDING + 14}" y1="{line_y}" '
        f'x2="{svg_w - PADDING - 14}" y2="{line_y}" '
        f'stroke="{ACCENT}" stroke-width="0.8" stroke-opacity="0.5"/>'
    )

    # Shift grid down to account for title area
    grid_offset_y = 22
    origin_y += grid_offset_y

    # ── Month labels ───────────────────────────────────────────────────────
    current_month = -1
    for wi, week in enumerate(weeks):
        if not week["contributionDays"]:
            continue
        first_day = week["contributionDays"][0]
        month_num = int(first_day["date"].split("-")[1])
        if month_num != current_month:
            current_month = month_num
            month_name = datetime.strptime(first_day["date"], "%Y-%m-%d").strftime("%b")
            x = origin_x + wi * (CELL + GAP)
            parts.append(
                f'  <text x="{x}" y="{origin_y - 6}" '
                f'fill="{TEXT_MONTH}" font-family="\'JetBrains Mono\', monospace" '
                f'font-size="11" font-weight="500">{month_name}</text>'
            )

    # ── Weekday labels ─────────────────────────────────────────────────────
    for di, label in enumerate(WEEKDAY_LABELS):
        if label:
            y = origin_y + di * (CELL + GAP) + CELL - 2
            parts.append(
                f'  <text x="{origin_x - 10}" y="{y}" '
                f'fill="{TEXT_DAY}" font-family="\'JetBrains Mono\', monospace" '
                f'font-size="10" font-weight="500" text-anchor="end">{label}</text>'
            )

    # ── Contribution cells ─────────────────────────────────────────────────
    for wi, week in enumerate(weeks):
        for day in week["contributionDays"]:
            di = day["weekday"]
            color = LEVEL_MAP.get(day["contributionLevel"], EMPTY)
            x = origin_x + wi * (CELL + GAP)
            y = origin_y + di * (CELL + GAP)
            count = day["contributionCount"]
            parts.append(
                f'  <rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                f'rx="{RADIUS}" fill="{color}">'
                f'<title>{day["date"]}: {count} contribution{"s" if count != 1 else ""}</title>'
                f'</rect>'
            )

    # ── Legend ─────────────────────────────────────────────────────────────
    legend_y = origin_y + grid_h + 24
    legend_x = origin_x

    parts.append(
        f'  <text x="{legend_x}" y="{legend_y + CELL - 2}" '
        f'fill="{TEXT_LEGEND}" font-family="\'JetBrains Mono\', monospace" '
        f'font-size="11" font-weight="500">Less</text>'
    )
    box_start = legend_x + 38
    for i, color in enumerate([EMPTY, LEVEL_1, LEVEL_2, LEVEL_3, LEVEL_4]):
        bx = box_start + i * (CELL + GAP)
        parts.append(
            f'  <rect x="{bx}" y="{legend_y}" width="{CELL}" height="{CELL}" '
            f'rx="{RADIUS}" fill="{color}"/>'
        )
    parts.append(
        f'  <text x="{box_start + 5 * (CELL + GAP) + 4}" y="{legend_y + CELL - 2}" '
        f'fill="{TEXT_LEGEND}" font-family="\'JetBrains Mono\', monospace" '
        f'font-size="11" font-weight="500">More</text>'
    )

    # ── Subtle bottom-right scan dots ──────────────────────────────────────
    dot_y = legend_y + 2
    for i in range(4):
        dx = svg_w - PADDING - 14 - i * 10
        parts.append(
            f'  <circle cx="{dx}" cy="{dot_y + 6}" r="1.5" '
            f'fill="{ACCENT}" opacity="0.5"/>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


# ── Main ───────────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 3:
        print("Usage: generate_heatmap.py <username> <output_path>", file=sys.stderr)
        sys.exit(1)

    username = sys.argv[1]
    output_path = sys.argv[2]

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print(
            "ERROR: GITHUB_TOKEN environment variable is required.\n"
            "Set it to a GitHub personal access token or use the automatic\n"
            "token provided by GitHub Actions.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Fetching contribution data for '{username}'...")
    calendar = fetch_contributions(username, token)
    total = calendar["totalContributions"]
    num_weeks = len(calendar["weeks"])
    print(f"  Total contributions: {total}")
    print(f"  Weeks of data: {num_weeks}")

    if num_weeks == 0:
        print("ERROR: No contribution weeks returned. Cannot generate heatmap.", file=sys.stderr)
        sys.exit(1)

    print("Generating SVG...")
    svg = generate_svg(calendar, username)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)

    print(f"Saved to {output_path} ({len(svg):,} bytes)")


if __name__ == "__main__":
    main()
