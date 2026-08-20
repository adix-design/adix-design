#!/usr/bin/env python3
"""
Generate an animated Cyberpunk GitHub Contribution Activity GIF.
Combines:
  1. Real GitHub contribution calendar (last ~12 months)
  2. Dark + crimson cyberpunk HUD styling
  3. Interactive pixel snake traversing and consuming red contribution cells
  4. Glowing particle effects on consumption
  5. Optimized, seamless looping GIF export
"""

import json
import os
import re
import sys
import math
import urllib.request
import urllib.error
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# ── Color Palette ──────────────────────────────────────────────────────────
COLOR_BG           = (7, 9, 13)       # #07090D
COLOR_PANEL_BG     = (11, 13, 18)     # #0B0D12
COLOR_BORDER       = (255, 51, 71)    # #FF3347
COLOR_BORDER_DARK  = (139, 16, 34)    # #8B1022
COLOR_ACCENT_GLOW  = (255, 80, 100)   # #FF5064
COLOR_EMPTY_CELL   = (21, 24, 31)     # #15181F

COLOR_LEVEL_1      = (58, 17, 23)     # #3A1117
COLOR_LEVEL_2      = (111, 23, 34)    # #6F1722
COLOR_LEVEL_3      = (181, 31, 50)    # #B51F32
COLOR_LEVEL_4      = (255, 51, 71)    # #FF3347

COLOR_TEXT_MAIN    = (242, 242, 244)  # #F2F2F4
COLOR_TEXT_MUTED   = (133, 137, 148)  # #858994
COLOR_TEXT_ACCENT  = (255, 51, 71)    # #FF3347

COLOR_SNAKE_HEAD   = (255, 51, 71)    # #FF3347
COLOR_SNAKE_EYES   = (255, 255, 255)  # #FFFFFF
COLOR_SNAKE_BODY_1 = (255, 70, 90)    # #FF465A
COLOR_SNAKE_BODY_2 = (181, 31, 50)    # #B51F32
COLOR_SNAKE_BODY_3 = (111, 23, 34)    # #6F1722
COLOR_SNAKE_BODY_4 = (58, 17, 23)     # #3A1117

LEVEL_COLOR_MAP = {
    "NONE":            COLOR_EMPTY_CELL,
    "FIRST_QUARTILE":  COLOR_LEVEL_1,
    "SECOND_QUARTILE": COLOR_LEVEL_2,
    "THIRD_QUARTILE":  COLOR_LEVEL_3,
    "FOURTH_QUARTILE": COLOR_LEVEL_4,
}

# ── Data Fetching ──────────────────────────────────────────────────────────
GRAPHQL_QUERY = """
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

def fetch_contributions_graphql(username: str, token: str) -> dict:
    payload = json.dumps({"query": GRAPHQL_QUERY, "variables": {"username": username}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "contribution-activity-generator",
        },
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
    
    if "errors" in data:
        raise RuntimeError(f"GraphQL error: {data['errors']}")
    user = data.get("data", {}).get("user")
    if not user:
        raise RuntimeError(f"User {username} not found")
    return user["contributionsCollection"]["contributionCalendar"]

def fetch_contributions_public(username: str) -> dict:
    url = f"https://github.com/users/{username}/contributions"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 contribution-activity-generator",
        "Accept": "text/html",
    })
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode("utf-8")

    matches = re.findall(r'data-date="([^"]+)"[^>]*data-level="(\d)"', html)
    if not matches:
        matches = re.findall(r'data-date="([^"]+)".*?data-level="(\d)"', html, re.DOTALL)
    
    if not matches:
        raise RuntimeError("Failed to parse public contribution HTML")
    
    matches.sort(key=lambda x: x[0])
    
    # Try finding counts
    tooltip_matches = dict(re.findall(r'data-date="([^"]+)"[^>]*>.*?(\d+)\s+contribution', html, re.DOTALL))
    
    level_map = {
        "0": "NONE",
        "1": "FIRST_QUARTILE",
        "2": "SECOND_QUARTILE",
        "3": "THIRD_QUARTILE",
        "4": "FOURTH_QUARTILE",
    }
    
    weeks = []
    current_week = []
    for date_str, level_str in matches:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        github_weekday = (dt.weekday() + 1) % 7 # Sunday=0
        
        count = int(tooltip_matches.get(date_str, 0))
        if count == 0 and level_str != "0":
            count = {"1": 1, "2": 3, "3": 6, "4": 10}.get(level_str, 1)
        
        day = {
            "date": date_str,
            "contributionCount": count,
            "contributionLevel": level_map.get(level_str, "NONE"),
            "weekday": github_weekday,
        }
        
        if github_weekday == 0 and current_week:
            weeks.append({"contributionDays": current_week})
            current_week = []
        current_week.append(day)
    
    if current_week:
        weeks.append({"contributionDays": current_week})
    
    total = sum(d["contributionCount"] for w in weeks for d in w["contributionDays"])
    return {"totalContributions": total, "weeks": weeks}

def get_contribution_data(username: str) -> dict:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        try:
            print(f"Fetching contribution data via GraphQL for {username}...")
            return fetch_contributions_graphql(username, token)
        except Exception as e:
            print(f"GraphQL fetch failed: {e}. Falling back to public scraping...", file=sys.stderr)
    
    print(f"Fetching contribution data via public scraper for {username}...")
    return fetch_contributions_public(username)

# ── Font Loading ───────────────────────────────────────────────────────────
def get_font(size: int, bold: bool = False):
    # Try system fonts or default bitmap font
    font_names = [
        "consola.ttf" if not bold else "consolab.ttf",
        "cour.ttf" if not bold else "courbd.ttf",
        "JetBrainsMono-Bold.ttf" if bold else "JetBrainsMono-Regular.ttf",
        "Arial.ttf",
    ]
    for fn in font_names:
        try:
            return ImageFont.truetype(fn, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default()
    except Exception:
        return None

# ── Smart Snake Pathfinding ────────────────────────────────────────────────
def build_snake_path(weeks_data, num_cols, num_rows):
    """
    Build a smooth continuous cyclic path on the (cols, rows) grid that visits
    the active red cells across the board and returns smoothly to the start.
    """
    active_cells = set()
    for col_idx, week in enumerate(weeks_data):
        for day in week["contributionDays"]:
            if day["contributionLevel"] != "NONE" or day["contributionCount"] > 0:
                active_cells.add((col_idx, day["weekday"]))

    # Sort active cells by column
    sorted_active = sorted(list(active_cells), key=lambda pt: (pt[0], pt[1]))
    
    if not sorted_active:
        # Fallback default loop across the grid
        sorted_active = [(col, 3) for col in range(5, num_cols - 5, 4)]

    # We want a sequence of key waypoints that traverses from left to right,
    # visiting active clusters, then loops back along top/bottom edges.
    # Sample waypoints:
    waypoints = []
    # Pick representative active points spread across the timeline
    last_col = -10
    for pt in sorted_active:
        if pt[0] - last_col >= 2 or (pt[0] > last_col and len(waypoints) < 15):
            waypoints.append(pt)
            last_col = pt[0]
            if len(waypoints) >= 20:
                break
    
    if len(waypoints) < 4:
        waypoints = [(5, 2), (15, 4), (25, 1), (35, 5), (45, 3)]

    # Return loop waypoints from right back to left
    return_pts = [
        (min(num_cols - 2, waypoints[-1][0] + 3), 1),
        (num_cols // 2, 0),
        (max(1, waypoints[0][0] - 2), 0)
    ]
    all_targets = waypoints + return_pts

    # Generate step-by-step Manhattan path connecting all targets cyclically
    full_path = []
    curr = all_targets[0]
    full_path.append(curr)

    for target in all_targets[1:] + [all_targets[0]]:
        cx, cy = curr
        tx, ty = target
        
        # Move horizontally towards target X, then vertically towards target Y
        # Introduce slight organic wiggles
        step_x = 1 if tx > cx else -1
        while cx != tx:
            cx += step_x
            full_path.append((cx, cy))
        
        step_y = 1 if ty > cy else -1
        while cy != ty:
            cy += step_y
            full_path.append((cx, cy))
        
        curr = (tx, ty)

    # Remove duplicates
    cleaned_path = [full_path[0]]
    for p in full_path[1:]:
        if p != cleaned_path[-1]:
            cleaned_path.append(p)
    
    # Ensure cycle closes cleanly
    if cleaned_path[-1] == cleaned_path[0]:
        cleaned_path.pop()

    return cleaned_path, active_cells

# ── Frame Drawing ──────────────────────────────────────────────────────────
def render_frame(
    calendar_data,
    weeks_data,
    total_contribs,
    snake_path,
    frame_idx,
    total_frames,
    active_cells,
    fonts,
    width=980,
    height=270
):
    im = Image.new("RGB", (width, height), COLOR_BG)
    draw = ImageDraw.Draw(im)

    font_title, font_sub, font_small, font_tiny = fonts

    # 1. Panel Background with Cut Corners
    panel_x, panel_y = 8, 8
    panel_w, panel_h = width - 16, height - 16
    cut = 12

    panel_polygon = [
        (panel_x + cut, panel_y),
        (panel_x + panel_w - cut, panel_y),
        (panel_x + panel_w, panel_y + cut),
        (panel_x + panel_w, panel_y + panel_h - cut),
        (panel_x + panel_w - cut, panel_y + panel_h),
        (panel_x + cut, panel_y + panel_h),
        (panel_x, panel_y + panel_h - cut),
        (panel_x, panel_y + cut),
    ]
    draw.polygon(panel_polygon, fill=COLOR_PANEL_BG, outline=COLOR_BORDER_DARK)

    # 2. Corner Tech Accents
    accent_len = 24
    cx, cy = panel_x, panel_y
    cw, ch = panel_w, panel_h

    # Top-Left Accent
    draw.line([(cx, cy + cut + accent_len), (cx, cy + cut), (cx + cut, cy), (cx + cut + accent_len, cy)], fill=COLOR_BORDER, width=2)
    # Top-Right Accent
    draw.line([(cx + cw - cut - accent_len, cy), (cx + cw - cut, cy), (cx + cw, cy + cut), (cx + cw, cy + cut + accent_len)], fill=COLOR_BORDER, width=2)
    # Bottom-Right Accent
    draw.line([(cx + cw, cy + ch - cut - accent_len), (cx + cw, cy + ch - cut), (cx + cw - cut, cy + ch), (cx + cw - cut + accent_len, cy + ch)], fill=COLOR_BORDER, width=2)
    # Bottom-Left Accent
    draw.line([(cx + cut + accent_len, cy + ch), (cx + cut, cy + ch), (cx, cy + ch - cut), (cx, cy + ch - cut - accent_len)], fill=COLOR_BORDER, width=2)

    # 3. Header Section
    title_text = "CONTRIBUTION ACTIVITY"
    stat_text = f"{total_contribs:,} CONTRIBUTIONS"

    draw.text((38, 22), title_text, fill=COLOR_TEXT_MAIN, font=font_title)
    
    # Right-aligned count
    draw.text((width - 42, 24), stat_text, fill=COLOR_TEXT_MUTED, font=font_sub, anchor="ra")

    # Divider line
    draw.line([(38, 48), (width - 38, 48)], fill=COLOR_BORDER_DARK, width=1)
    draw.line([(38, 48), (140, 48)], fill=COLOR_BORDER, width=1) # Neon accent on header

    # 4. Grid Coordinates
    cell_size = 12
    cell_gap = 3
    left_margin = 68
    top_margin = 82
    num_cols = len(weeks_data)

    # 5. Month Labels
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    last_month = -1
    for wi, week in enumerate(weeks_data):
        if week["contributionDays"]:
            first_day = week["contributionDays"][0]
            m_num = int(first_day["date"].split("-")[1])
            if m_num != last_month:
                last_month = m_num
                m_str = month_names[m_num - 1]
                x = left_margin + wi * (cell_size + cell_gap)
                draw.text((x, top_margin - 16), m_str, fill=COLOR_TEXT_MUTED, font=font_tiny)

    # 6. Weekday Labels (Mon=1, Wed=3, Fri=5)
    weekdays_to_show = [(1, "Mon"), (3, "Wed"), (5, "Fri")]
    for w_idx, w_label in weekdays_to_show:
        y = top_margin + w_idx * (cell_size + cell_gap) + 1
        draw.text((left_margin - 12, y), w_label, fill=COLOR_TEXT_MUTED, font=font_tiny, anchor="ra")

    # 7. Snake position calculation
    path_len = len(snake_path)
    head_path_idx = (frame_idx) % path_len
    snake_length = 5  # head + 4 tail segments

    # Snake segment coordinates on grid
    snake_coords = []
    for s in range(snake_length):
        idx = (head_path_idx - s) % path_len
        snake_coords.append(snake_path[idx])

    head_pos = snake_coords[0]

    # Track recently consumed cell for particle / burst effects
    # Find active cells that the snake head is visiting or recently visited
    particles = []
    for f_offset in range(4): # Last 4 frames
        check_idx = (head_path_idx - f_offset) % path_len
        check_pt = snake_path[check_idx]
        if check_pt in active_cells:
            # Generate sparkle particles expanding outwards
            progress = f_offset / 3.0  # 0.0 to 1.0
            pt_x = left_margin + check_pt[0] * (cell_size + cell_gap) + cell_size // 2
            pt_y = top_margin + check_pt[1] * (cell_size + cell_gap) + cell_size // 2
            
            p_dist = progress * 9.0
            p_alpha_color = (
                int(255 - progress * 100),
                int(51 + progress * 50),
                int(71 + progress * 50)
            )
            # 4 particle sparks at diagonals
            for angle_deg in [45, 135, 225, 315]:
                rad = math.radians(angle_deg)
                px = pt_x + math.cos(rad) * p_dist
                py = pt_y + math.sin(rad) * p_dist
                particles.append((px, py, max(1, int(3 - progress * 2)), p_alpha_color))

    # 8. Draw Grid Cells
    for wi, week in enumerate(weeks_data):
        for day in week["contributionDays"]:
            col = wi
            row = day["weekday"]
            x = left_margin + col * (cell_size + cell_gap)
            y = top_margin + row * (cell_size + cell_gap)

            base_color = LEVEL_COLOR_MAP.get(day["contributionLevel"], COLOR_EMPTY_CELL)
            
            # Check if this cell is currently under snake head (eaten glow)
            is_head = (col, row) == head_pos
            if is_head and (col, row) in active_cells:
                # Brief neon burst
                cell_fill = (255, 120, 140)
            else:
                cell_fill = base_color

            # Draw rounded square cell
            draw.rounded_rectangle(
                [x, y, x + cell_size - 1, y + cell_size - 1],
                radius=2,
                fill=cell_fill
            )

    # 9. Draw Snake Body and Head
    # Draw body segments (from tail to head)
    body_colors = [COLOR_SNAKE_BODY_4, COLOR_SNAKE_BODY_3, COLOR_SNAKE_BODY_2, COLOR_SNAKE_BODY_1]
    for seg_idx in range(len(snake_coords) - 1, 0, -1):
        sc = snake_coords[seg_idx]
        sx = left_margin + sc[0] * (cell_size + cell_gap)
        sy = top_margin + sc[1] * (cell_size + cell_gap)
        
        c_fill = body_colors[min(seg_idx - 1, len(body_colors) - 1)]
        
        # Inner body segment
        draw.rounded_rectangle(
            [sx + 1, sy + 1, sx + cell_size - 2, sy + cell_size - 2],
            radius=3,
            fill=c_fill,
            outline=COLOR_BORDER,
            width=1
        )
        # Center core glow
        draw.rectangle(
            [sx + 4, sy + 4, sx + cell_size - 5, sy + cell_size - 5],
            fill=COLOR_BORDER
        )

    # Draw Snake Head (Cyberpunk Pixel Head)
    hx = left_margin + head_pos[0] * (cell_size + cell_gap)
    hy = top_margin + head_pos[1] * (cell_size + cell_gap)
    
    # Outer head
    draw.rounded_rectangle(
        [hx, hy, hx + cell_size - 1, hy + cell_size - 1],
        radius=3,
        fill=COLOR_SNAKE_HEAD,
        outline=(255, 200, 210),
        width=1
    )
    
    # Direction for eyes
    prev_pos = snake_coords[1] if len(snake_coords) > 1 else head_pos
    dx = head_pos[0] - prev_pos[0]
    dy = head_pos[1] - prev_pos[1]

    # Glowing eyes
    if dx >= 0 and dy == 0:  # Moving right
        draw.point([(hx + 8, hy + 3), (hx + 8, hy + 8)], fill=COLOR_SNAKE_EYES)
    elif dx < 0 and dy == 0: # Moving left
        draw.point([(hx + 3, hy + 3), (hx + 3, hy + 8)], fill=COLOR_SNAKE_EYES)
    elif dy > 0:             # Moving down
        draw.point([(hx + 3, hy + 8), (hx + 8, hy + 8)], fill=COLOR_SNAKE_EYES)
    else:                    # Moving up
        draw.point([(hx + 3, hy + 3), (hx + 8, hy + 3)], fill=COLOR_SNAKE_EYES)

    # 10. Draw Sparkle / Particle Effects
    for px, py, pr, pcol in particles:
        draw.ellipse([px - pr, py - pr, px + pr, py + pr], fill=pcol)

    # 11. Legend (Bottom Left)
    legend_y = top_margin + 7 * (cell_size + cell_gap) + 20
    draw.text((left_margin, legend_y), "Less", fill=COLOR_TEXT_MUTED, font=font_tiny)

    leg_colors = [COLOR_EMPTY_CELL, COLOR_LEVEL_1, COLOR_LEVEL_2, COLOR_LEVEL_3, COLOR_LEVEL_4]
    leg_x = left_margin + 34
    for lc in leg_colors:
        draw.rounded_rectangle(
            [leg_x, legend_y + 1, leg_x + cell_size - 2, legend_y + cell_size - 1],
            radius=2,
            fill=lc
        )
        leg_x += cell_size + cell_gap

    draw.text((leg_x + 4, legend_y), "More", fill=COLOR_TEXT_MUTED, font=font_tiny)

    # 12. Bottom Right Subtle HUD Accent Dots
    for i in range(4):
        dot_x = width - 42 - i * 10
        draw.ellipse([dot_x - 1, legend_y + 6, dot_x + 1, legend_y + 8], fill=COLOR_BORDER)

    return im

# ── Main Export ────────────────────────────────────────────────────────────
def generate_contribution_activity_gif(username: str, output_path: str, num_frames: int = 60, duration_ms: int = 80):
    calendar = get_contribution_data(username)
    weeks = calendar["weeks"]
    total = calendar["totalContributions"]
    num_weeks = len(weeks)

    print(f"Loaded {num_weeks} weeks of real data, Total Contributions: {total}")

    # Initialize fonts
    f_title = get_font(14, bold=True)
    f_sub   = get_font(12, bold=False)
    f_small = get_font(11, bold=False)
    f_tiny  = get_font(10, bold=False)
    fonts = (f_title, f_sub, f_small, f_tiny)

    # Build snake path
    snake_path, active_cells = build_snake_path(weeks, num_weeks, 7)
    print(f"Snake path constructed with {len(snake_path)} cyclic steps across {len(active_cells)} active contribution cells.")

    # Determine total frames for one complete cyclic loop (or multiple of path)
    actual_frames = len(snake_path)
    print(f"Rendering {actual_frames} animation frames...")

    frames = []
    for f in range(actual_frames):
        frame_im = render_frame(
            calendar_data=calendar,
            weeks_data=weeks,
            total_contribs=total,
            snake_path=snake_path,
            frame_idx=f,
            total_frames=actual_frames,
            active_cells=active_cells,
            fonts=fonts,
            width=980,
            height=265
        )
        # Quantize to 128 colors with custom palette for clean GIF compression
        quantized = frame_im.quantize(colors=128, method=Image.Quantize.MEDIANCUT)
        frames.append(quantized)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    print(f"Saving animated GIF to {output_path}...")
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=duration_ms,
        loop=0,
        optimize=True
    )

    file_size = os.path.getsize(output_path)
    print(f"SUCCESS: Saved {output_path} ({file_size:,} bytes, {len(frames)} frames, {duration_ms}ms/frame)")
    return actual_frames, total, file_size

if __name__ == "__main__":
    user = sys.argv[1] if len(sys.argv) > 1 else "adix-design"
    out = sys.argv[2] if len(sys.argv) > 2 else "assets/github-contribution-activity.gif"
    generate_contribution_activity_gif(user, out)
