#!/usr/bin/env python3
"""
Generate an animated Cyberpunk GitHub Contribution Activity GIF.
Real GitHub contribution calendar with a true game-engine snake simulation:
  1. Identifies all real contribution cells (> 0).
  2. The Snake intentionally targets each active red cell in order.
  3. Cell-by-cell pathfinding (UP, DOWN, LEFT, RIGHT).
  4. Precise eat collision events:
     - Approach / Overlap
     - Cell Flashes bright neon-white
     - Cell Disappears into eaten_cells state (drawn permanently EMPTY for the rest of the cycle)
     - Crimson particle explosion effect
     - Snake continues to the next red target
  5. Clean loop reset and optimized GIF export.
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
COLOR_EMPTY_CELL   = (21, 24, 31)     # #15181F

COLOR_LEVEL_1      = (58, 17, 23)     # #3A1117 - Low
COLOR_LEVEL_2      = (111, 23, 34)    # #6F1722 - Medium
COLOR_LEVEL_3      = (181, 31, 50)    # #B51F32 - High
COLOR_LEVEL_4      = (255, 51, 71)    # #FF3347 - Highest

COLOR_TEXT_MAIN    = (242, 242, 244)  # #F2F2F4
COLOR_TEXT_MUTED   = (133, 137, 148)  # #858994
COLOR_TEXT_ACCENT  = (255, 51, 71)    # #FF3347

COLOR_SNAKE_HEAD   = (255, 51, 71)    # #FF3347
COLOR_SNAKE_EYES   = (255, 255, 255)  # #FFFFFF
COLOR_SNAKE_BODY_1 = (255, 70, 90)    # #FF465A
COLOR_SNAKE_BODY_2 = (200, 40, 60)    # #C8283C
COLOR_SNAKE_BODY_3 = (139, 16, 34)    # #8B1022
COLOR_SNAKE_BODY_4 = (70, 15, 25)     # #460F19

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
            print(f"GraphQL fetch failed: {e}. Falling back to public scraper...", file=sys.stderr)
    
    print(f"Fetching contribution data via public scraper for {username}...")
    return fetch_contributions_public(username)

def get_cell_color(day):
    count = day.get("contributionCount", 0)
    level = day.get("contributionLevel", "NONE")
    
    if level == "FOURTH_QUARTILE" or count >= 10:
        return COLOR_LEVEL_4
    elif level == "THIRD_QUARTILE" or count >= 6:
        return COLOR_LEVEL_3
    elif level == "SECOND_QUARTILE" or count >= 3:
        return COLOR_LEVEL_2
    elif level == "FIRST_QUARTILE" or count >= 1:
        return COLOR_LEVEL_1
    return COLOR_EMPTY_CELL

def is_active_day(day):
    return day.get("contributionCount", 0) > 0 or day.get("contributionLevel", "NONE") != "NONE"

# ── Font Loading ───────────────────────────────────────────────────────────
def get_font(size: int, bold: bool = False):
    font_names = [
        "consola.ttf" if not bold else "consolab.ttf",
        "cour.ttf" if not bold else "courbd.ttf",
        "JetBrainsMono-Bold.ttf" if bold else "JetBrainsMono-Regular.ttf",
        "DejaVuSansMono.ttf",
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

# ── Cluster-based Target Planning & Pathfinding ────────────────────────────
def plan_targets(weeks_data, num_cols):
    """
    Extract active cells and plan a logical cluster-by-cluster target order
    from left to right across the board.
    """
    active_cells = []
    for col_idx, week in enumerate(weeks_data):
        for day in week["contributionDays"]:
            if is_active_day(day):
                active_cells.append((col_idx, day["weekday"]))

    if not active_cells:
        # Fallback if brand new profile with 0 contributions
        return [(c, 3) for c in range(10, num_cols - 10, 5)]

    # Group into contiguous / nearby column clusters (cells within 3 columns of each other)
    sorted_cells = sorted(active_cells, key=lambda pt: (pt[0], pt[1]))
    clusters = []
    curr_cluster = [sorted_cells[0]]
    for pt in sorted_cells[1:]:
        if pt[0] - curr_cluster[-1][0] <= 3:
            curr_cluster.append(pt)
        else:
            clusters.append(curr_cluster)
            curr_cluster = [pt]
    clusters.append(curr_cluster)

    ordered_targets = []
    curr_pos = (0, 0)
    for cluster in clusters:
        # Solve local TSP for this cluster to visit all points in cluster starting from curr_pos
        unvisited_cluster = set(cluster)
        while unvisited_cluster:
            nxt = min(unvisited_cluster, key=lambda pt: abs(pt[0] - curr_pos[0]) + abs(pt[1] - curr_pos[1]))
            ordered_targets.append(nxt)
            unvisited_cluster.remove(nxt)
            curr_pos = nxt

    return ordered_targets

def path_between(pt1, pt2):
    """
    Generate step-by-step orthogonal grid path (UP, DOWN, LEFT, RIGHT)
    from pt1 to pt2 (excluding pt1, including pt2).
    """
    cx, cy = pt1
    tx, ty = pt2
    steps = []
    
    # Move horizontally first, then vertically
    step_x = 1 if tx > cx else -1
    while cx != tx:
        cx += step_x
        steps.append((cx, cy))
        
    step_y = 1 if ty > cy else -1
    while cy != ty:
        cy += step_y
        steps.append((cx, cy))
        
    return steps

# ── Simulation & Frame State Generation ────────────────────────────────────
def simulate_animation_frames(weeks_data, num_cols, num_rows=7):
    """
    Run full discrete frame simulation of snake hunting, eating, particle bursts,
    disappearing cells, and loop reset.
    """
    targets = plan_targets(weeks_data, num_cols)
    first_target = targets[0]
    
    # Starting position 2 cells before first target
    start_pos = (max(0, first_target[0] - 2), first_target[1])
    
    # Initial snake body (length 4)
    snake_len = 4
    snake_body = [start_pos] * snake_len
    eaten_cells = set()
    particles = []
    
    frames_state = []
    
    # 1. Approach to first target
    steps_to_first = path_between(start_pos, first_target)
    frames_state.append({
        "snake": list(snake_body),
        "eaten": set(eaten_cells),
        "flash": None,
        "particles": list(particles),
        "phase": "move"
    })
    
    for step in steps_to_first[:-1]:
        snake_body = [step] + snake_body[:-1]
        frames_state.append({
            "snake": list(snake_body),
            "eaten": set(eaten_cells),
            "flash": None,
            "particles": list(particles),
            "phase": "move"
        })

    # 2. Sequential Target Hunting & Eating
    for t_idx, target in enumerate(targets):
        # Move head onto target cell
        snake_body = [target] + snake_body[:-1]
        
        # Frame A: Overlap + Bright Flash
        frames_state.append({
            "snake": list(snake_body),
            "eaten": set(eaten_cells), # not eaten yet
            "flash": target,           # flashing bright
            "particles": list(particles),
            "phase": "flash"
        })
        
        # Frame B: Consume! Target added to eaten_cells + spawn particles
        eaten_cells.add(target)
        
        # Spawn glowing particle sparks
        new_sparks = []
        for angle_deg in [0, 45, 90, 135, 180, 225, 270, 315]:
            rad = math.radians(angle_deg)
            speed = 3.2
            new_sparks.append({
                "cell": target,
                "vx": math.cos(rad) * speed,
                "vy": math.sin(rad) * speed,
                "age": 0,
                "max_age": 3
            })
        particles.extend(new_sparks)
        
        frames_state.append({
            "snake": list(snake_body),
            "eaten": set(eaten_cells), # now permanently eaten
            "flash": None,
            "particles": list(particles),
            "phase": "eat"
        })
        
        # Move towards next target (if any)
        if t_idx < len(targets) - 1:
            next_target = targets[t_idx + 1]
            steps = path_between(target, next_target)
            
            # Step along the path up to next target
            for step in steps[:-1]:
                snake_body = [step] + snake_body[:-1]
                
                # Advance active particles
                updated_particles = []
                for p in particles:
                    p["age"] += 1
                    if p["age"] < p["max_age"]:
                        updated_particles.append(p)
                particles = updated_particles
                
                frames_state.append({
                    "snake": list(snake_body),
                    "eaten": set(eaten_cells),
                    "flash": None,
                    "particles": list(particles),
                    "phase": "move"
                })

    # 3. Return Loop Path back to Start
    last_target = targets[-1]
    
    # Return loop: move up to row 0 / top channel, traverse left to col 0, down to start_pos
    return_waypoints = [
        (min(num_cols - 1, last_target[0] + 1), 0),
        (0, 0),
        start_pos
    ]
    
    curr = last_target
    for r_pt in return_waypoints:
        steps = path_between(curr, r_pt)
        for step in steps:
            snake_body = [step] + snake_body[:-1]
            
            # Age particles
            updated_particles = []
            for p in particles:
                p["age"] += 1
                if p["age"] < p["max_age"]:
                    updated_particles.append(p)
            particles = updated_particles
            
            frames_state.append({
                "snake": list(snake_body),
                "eaten": set(eaten_cells),
                "flash": None,
                "particles": list(particles),
                "phase": "return"
            })
        curr = r_pt

    # 4. Seamless Loop Reset Transition (last 2 frames fade restored grid)
    frames_state.append({
        "snake": list(snake_body),
        "eaten": set(), # Grid restored for seamless loop back to frame 0
        "flash": None,
        "particles": [],
        "phase": "reset"
    })

    return frames_state

# ── Frame Rendering ──────────────────────────────────────────────────────────
def render_frame_image(
    calendar_data,
    weeks_data,
    total_contribs,
    state,
    fonts,
    width=980,
    height=265
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
    draw.text((width - 42, 24), stat_text, fill=COLOR_TEXT_MUTED, font=font_sub, anchor="ra")

    # Divider line
    draw.line([(38, 48), (width - 38, 48)], fill=COLOR_BORDER_DARK, width=1)
    draw.line([(38, 48), (140, 48)], fill=COLOR_BORDER, width=1) # Neon header notch

    # 4. Grid Dimensions & Positions
    cell_size = 12
    cell_gap = 3
    left_margin = 68
    top_margin = 82

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

    # 7. Draw Contribution Grid Cells (With Eaten State & Flash Check)
    eaten_cells = state["eaten"]
    flash_cell = state["flash"]

    for wi, week in enumerate(weeks_data):
        for day in week["contributionDays"]:
            col = wi
            row = day["weekday"]
            x = left_margin + col * (cell_size + cell_gap)
            y = top_margin + row * (cell_size + cell_gap)

            # Cell Color Logic
            if (col, row) == flash_cell:
                # EAT EVENT: Intense Neon Flash!
                cell_fill = (255, 230, 240)
            elif (col, row) in eaten_cells:
                # EATEN STATE: Permanently Empty/Dark for this cycle!
                cell_fill = COLOR_EMPTY_CELL
            else:
                # Normal real contribution color
                cell_fill = get_cell_color(day)

            # Draw rounded square cell
            draw.rounded_rectangle(
                [x, y, x + cell_size - 1, y + cell_size - 1],
                radius=2,
                fill=cell_fill
            )

    # 8. Draw Snake Body & Head
    snake_coords = state["snake"]
    head_pos = snake_coords[0]

    # Body segments (tail to neck)
    body_colors = [COLOR_SNAKE_BODY_4, COLOR_SNAKE_BODY_3, COLOR_SNAKE_BODY_2, COLOR_SNAKE_BODY_1]
    for seg_idx in range(len(snake_coords) - 1, 0, -1):
        sc = snake_coords[seg_idx]
        sx = left_margin + sc[0] * (cell_size + cell_gap)
        sy = top_margin + sc[1] * (cell_size + cell_gap)
        
        c_fill = body_colors[min(seg_idx - 1, len(body_colors) - 1)]
        
        draw.rounded_rectangle(
            [sx + 1, sy + 1, sx + cell_size - 2, sy + cell_size - 2],
            radius=3,
            fill=c_fill,
            outline=COLOR_BORDER,
            width=1
        )
        draw.rectangle(
            [sx + 4, sy + 4, sx + cell_size - 5, sy + cell_size - 5],
            fill=COLOR_BORDER
        )

    # Head Segment
    hx = left_margin + head_pos[0] * (cell_size + cell_gap)
    hy = top_margin + head_pos[1] * (cell_size + cell_gap)

    draw.rounded_rectangle(
        [hx, hy, hx + cell_size - 1, hy + cell_size - 1],
        radius=3,
        fill=COLOR_SNAKE_HEAD,
        outline=(255, 200, 210),
        width=1
    )

    # Orientation for eyes
    prev_pos = snake_coords[1] if len(snake_coords) > 1 else head_pos
    dx = head_pos[0] - prev_pos[0]
    dy = head_pos[1] - prev_pos[1]

    if dx >= 0 and dy == 0:  # Moving Right
        draw.point([(hx + 8, hy + 3), (hx + 8, hy + 8)], fill=COLOR_SNAKE_EYES)
    elif dx < 0 and dy == 0: # Moving Left
        draw.point([(hx + 3, hy + 3), (hx + 3, hy + 8)], fill=COLOR_SNAKE_EYES)
    elif dy > 0:             # Moving Down
        draw.point([(hx + 3, hy + 8), (hx + 8, hy + 8)], fill=COLOR_SNAKE_EYES)
    else:                    # Moving Up
        draw.point([(hx + 3, hy + 3), (hx + 8, hy + 3)], fill=COLOR_SNAKE_EYES)

    # 9. Draw Active Particle Sparks
    for p in state["particles"]:
        p_col, p_row = p["cell"]
        center_x = left_margin + p_col * (cell_size + cell_gap) + cell_size // 2
        center_y = top_margin + p_row * (cell_size + cell_gap) + cell_size // 2
        
        px = center_x + p["vx"] * (p["age"] + 1)
        py = center_y + p["vy"] * (p["age"] + 1)
        pr = max(1, 3 - p["age"])
        
        alpha_factor = max(0.2, 1.0 - (p["age"] / p["max_age"]))
        spark_color = (
            int(255 * alpha_factor),
            int(51 * alpha_factor + 50),
            int(71 * alpha_factor + 50)
        )
        draw.ellipse([px - pr, py - pr, px + pr, py + pr], fill=spark_color)

    # 10. Legend (Bottom Left)
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

    # 11. Bottom Right Subtle HUD Accent Dots
    for i in range(4):
        dot_x = width - 42 - i * 10
        draw.ellipse([dot_x - 1, legend_y + 6, dot_x + 1, legend_y + 8], fill=COLOR_BORDER)

    return im

# ── Main Generator ─────────────────────────────────────────────────────────
def generate_contribution_activity_gif(username: str, output_path: str, duration_ms: int = 90):
    calendar = get_contribution_data(username)
    weeks = calendar["weeks"]
    total = calendar["totalContributions"]
    num_cols = len(weeks)

    print(f"Loaded {num_cols} weeks of real data, Total Contributions: {total}")

    # Fonts
    f_title = get_font(14, bold=True)
    f_sub   = get_font(12, bold=False)
    f_small = get_font(11, bold=False)
    f_tiny  = get_font(10, bold=False)
    fonts = (f_title, f_sub, f_small, f_tiny)

    # Run Simulation to generate frame states
    print("Simulating Snake hunting, eat collisions, and particle bursts...")
    frame_states = simulate_animation_frames(weeks, num_cols, num_rows=7)
    total_frames = len(frame_states)
    print(f"Generated {total_frames} discrete game frames.")

    # Render each frame
    print(f"Rendering {total_frames} animation frames...")
    frames = []
    for f_idx, st in enumerate(frame_states):
        frame_im = render_frame_image(
            calendar_data=calendar,
            weeks_data=weeks,
            total_contribs=total,
            state=st,
            fonts=fonts,
            width=980,
            height=265
        )
        quantized = frame_im.quantize(colors=128, method=Image.Quantize.MEDIANCUT)
        frames.append(quantized)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    print(f"Saving optimized animated GIF to {output_path}...")
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=duration_ms,
        loop=0,
        optimize=True
    )

    file_size = os.path.getsize(output_path)
    print(f"SUCCESS: Saved {output_path} ({file_size:,} bytes, {total_frames} frames, {duration_ms}ms/frame)")
    return total_frames, total, file_size

if __name__ == "__main__":
    user = sys.argv[1] if len(sys.argv) > 1 else "adix-design"
    out = sys.argv[2] if len(sys.argv) > 2 else "assets/github-contribution-activity.gif"
    generate_contribution_activity_gif(user, out)
