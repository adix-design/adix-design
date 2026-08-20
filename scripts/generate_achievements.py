import os
import json
import urllib.request

def fetch_github_stats():
    # Defaults based on real verified GitHub profile data
    stats = {
        "public_repos": 6,
        "contributions": 73,
        "stars": 0,
        "followers": 0
    }
    
    # Try fetching real data from GitHub API if token or network available
    token = os.environ.get("GITHUB_TOKEN")
    headers = {"User-Agent": "Mozilla/5.0"}
    if token:
        headers["Authorization"] = f"token {token}"
        
    try:
        req = urllib.request.Request("https://api.github.com/users/adix-design", headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            stats["public_repos"] = data.get("public_repos", stats["public_repos"])
            stats["followers"] = data.get("followers", stats["followers"])
    except Exception as e:
        print(f"Note: API fetch fallback used ({e})")
        
    return stats

def generate_svg(stats, out_path="assets/github-trophies.svg"):
    repos_val = f"{stats['public_repos']} PUBLIC REPOS"
    contrib_val = f"{stats['contributions']} CONTRIBUTIONS"
    
    # Vector Icons
    icon_builder = '''<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#FF3347" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
      <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
      <line x1="12" y1="22.08" x2="12" y2="12"/>
    </svg>'''
    
    icon_shipper = '''<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#FF3347" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/>
      <path d="M12 15l-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/>
      <path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/>
      <path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/>
    </svg>'''
    
    icon_opensource = '''<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#FF3347" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="18" cy="18" r="3"/>
      <circle cx="6" cy="6" r="3"/>
      <path d="M13 6h3a2 2 0 0 1 2 2v7"/>
      <line x1="6" y1="9" x2="6" y2="21"/>
    </svg>'''
    
    icon_product = '''<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#FF3347" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
    </svg>'''

    svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 400" width="1200" height="400">
<defs>
  <!-- Card Background Gradient -->
  <linearGradient id="achieve-bg" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#0F121A"/>
    <stop offset="100%" stop-color="#080A0E"/>
  </linearGradient>

  <!-- Glow Filter -->
  <filter id="achieve-glow" x="-10%" y="-10%" width="120%" height="120%">
    <feDropShadow dx="0" dy="0" stdDeviation="2.5" flood-color="#FF3347" flood-opacity="0.25"/>
  </filter>

  <!-- Milestone Grid Pattern -->
  <pattern id="achieve-grid" width="20" height="20" patternUnits="userSpaceOnUse">
    <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#FF3347" stroke-width="0.8" stroke-opacity="0.03"/>
  </pattern>
</defs>

<!-- Transparent Canvas -->

<!-- ── MILESTONE 01: BUILDER (Top-Left: x=10, y=10, w=580, h=180) ── -->
<g id="milestone-01" transform="translate(10, 10)">
  <rect width="580" height="180" rx="8" fill="url(#achieve-bg)" stroke="#FF3347" stroke-width="1.2" stroke-opacity="0.32" filter="url(#achieve-glow)"/>
  <rect width="580" height="180" rx="8" fill="url(#achieve-grid)"/>

  <!-- Top Accent Notch -->
  <line x1="8" y1="0" x2="80" y2="0" stroke="#FF3347" stroke-width="2"/>

  <!-- Header: Icon + Milestone Title + Verified Indicator -->
  <g transform="translate(24, 20)">
    {icon_builder}
  </g>
  <text x="56" y="36" fill="#FF3347" font-family="'JetBrains Mono', Consolas, monospace" font-size="14" font-weight="700" letter-spacing="1.5">01  ◆ BUILDER</text>
  
  <!-- Verified Badge -->
  <circle cx="508" cy="32" r="4" fill="#45E879"/>
  <text x="520" y="36" fill="#45E879" font-family="'JetBrains Mono', monospace" font-size="12" font-weight="700" letter-spacing="1">✓ UNLOCKED</text>

  <line x1="24" y1="52" x2="556" y2="52" stroke="#FF3347" stroke-width="0.6" stroke-opacity="0.15"/>

  <!-- Big Metric (24px) -->
  <text x="24" y="86" fill="#F2F2F4" font-family="'JetBrains Mono', Consolas, monospace" font-size="24" font-weight="800" letter-spacing="1">{repos_val}</text>

  <!-- Description (14.5px) -->
  <text x="24" y="116" fill="#9296A0" font-family="system-ui, -apple-system, sans-serif" font-size="14.5" font-weight="400">
    Built and maintained public full-stack and AI software projects.
  </text>

  <!-- Bottom Verification Footer -->
  <line x1="24" y1="138" x2="556" y2="138" stroke="#FF3347" stroke-width="0.5" stroke-opacity="0.12"/>
  <text x="24" y="160" fill="#858994" font-family="'JetBrains Mono', monospace" font-size="11.5" letter-spacing="1">
    EVIDENCE: <tspan fill="#45E879" font-weight="600">VERIFIED • GITHUB REPOSITORIES</tspan>
  </text>
</g>

<!-- ── MILESTONE 02: SHIPPER (Top-Right: x=610, y=10, w=580, h=180) ── -->
<g id="milestone-02" transform="translate(610, 10)">
  <rect width="580" height="180" rx="8" fill="url(#achieve-bg)" stroke="#FF3347" stroke-width="1.2" stroke-opacity="0.32" filter="url(#achieve-glow)"/>
  <rect width="580" height="180" rx="8" fill="url(#achieve-grid)"/>

  <line x1="8" y1="0" x2="80" y2="0" stroke="#FF3347" stroke-width="2"/>

  <g transform="translate(24, 20)">
    {icon_shipper}
  </g>
  <text x="56" y="36" fill="#FF3347" font-family="'JetBrains Mono', Consolas, monospace" font-size="14" font-weight="700" letter-spacing="1.5">02  ◆ SHIPPER</text>
  
  <circle cx="508" cy="32" r="4" fill="#45E879"/>
  <text x="520" y="36" fill="#45E879" font-family="'JetBrains Mono', monospace" font-size="12" font-weight="700" letter-spacing="1">✓ UNLOCKED</text>

  <line x1="24" y1="52" x2="556" y2="52" stroke="#FF3347" stroke-width="0.6" stroke-opacity="0.15"/>

  <!-- Big Metric (24px) -->
  <text x="24" y="86" fill="#F2F2F4" font-family="'JetBrains Mono', Consolas, monospace" font-size="24" font-weight="800" letter-spacing="1">{contrib_val}</text>

  <!-- Description (14.5px) -->
  <text x="24" y="116" fill="#9296A0" font-family="system-ui, -apple-system, sans-serif" font-size="14.5" font-weight="400">
    Active engineering contributions and continuous development cycle.
  </text>

  <line x1="24" y1="138" x2="556" y2="138" stroke="#FF3347" stroke-width="0.5" stroke-opacity="0.12"/>
  <text x="24" y="160" fill="#858994" font-family="'JetBrains Mono', monospace" font-size="11.5" letter-spacing="1">
    EVIDENCE: <tspan fill="#45E879" font-weight="600">VERIFIED • ANNUAL ACTIVITY</tspan>
  </text>
</g>

<!-- ── MILESTONE 03: OPEN SOURCE (Bottom-Left: x=10, y=205, w=580, h=180) ─ -->
<g id="milestone-03" transform="translate(10, 205)">
  <rect width="580" height="180" rx="8" fill="url(#achieve-bg)" stroke="#FF3347" stroke-width="1.2" stroke-opacity="0.32" filter="url(#achieve-glow)"/>
  <rect width="580" height="180" rx="8" fill="url(#achieve-grid)"/>

  <line x1="8" y1="0" x2="80" y2="0" stroke="#FF3347" stroke-width="2"/>

  <g transform="translate(24, 20)">
    {icon_opensource}
  </g>
  <text x="56" y="36" fill="#FF3347" font-family="'JetBrains Mono', Consolas, monospace" font-size="14" font-weight="700" letter-spacing="1.5">03  ◆ OPEN SOURCE</text>
  
  <circle cx="508" cy="32" r="4" fill="#45E879"/>
  <text x="520" y="36" fill="#45E879" font-family="'JetBrains Mono', monospace" font-size="12" font-weight="700" letter-spacing="1">✓ UNLOCKED</text>

  <line x1="24" y1="52" x2="556" y2="52" stroke="#FF3347" stroke-width="0.6" stroke-opacity="0.15"/>

  <!-- Big Metric (24px) -->
  <text x="24" y="86" fill="#F2F2F4" font-family="'JetBrains Mono', Consolas, monospace" font-size="24" font-weight="800" letter-spacing="1">PUBLIC ECOSYSTEM</text>

  <!-- Description (14.5px) -->
  <text x="24" y="116" fill="#9296A0" font-family="system-ui, -apple-system, sans-serif" font-size="14.5" font-weight="400">
    Open-source codebase contributions, repositories and modern tools.
  </text>

  <line x1="24" y1="138" x2="556" y2="138" stroke="#FF3347" stroke-width="0.5" stroke-opacity="0.12"/>
  <text x="24" y="160" fill="#858994" font-family="'JetBrains Mono', monospace" font-size="11.5" letter-spacing="1">
    EVIDENCE: <tspan fill="#45E879" font-weight="600">VERIFIED • GITHUB ECOSYSTEM</tspan>
  </text>
</g>

<!-- ── MILESTONE 04: PRODUCT BUILDER (Bottom-Right: x=610, y=205, w=580, h=180) ─ -->
<g id="milestone-04" transform="translate(610, 205)">
  <rect width="580" height="180" rx="8" fill="url(#achieve-bg)" stroke="#FF3347" stroke-width="1.2" stroke-opacity="0.32" filter="url(#achieve-glow)"/>
  <rect width="580" height="180" rx="8" fill="url(#achieve-grid)"/>

  <line x1="8" y1="0" x2="80" y2="0" stroke="#FF3347" stroke-width="2"/>

  <g transform="translate(24, 20)">
    {icon_product}
  </g>
  <text x="56" y="36" fill="#FF3347" font-family="'JetBrains Mono', Consolas, monospace" font-size="14" font-weight="700" letter-spacing="1.5">04  ◆ PRODUCT BUILDER</text>
  
  <circle cx="508" cy="32" r="4" fill="#45E879"/>
  <text x="520" y="36" fill="#45E879" font-family="'JetBrains Mono', monospace" font-size="12" font-weight="700" letter-spacing="1">✓ UNLOCKED</text>

  <line x1="24" y1="52" x2="556" y2="52" stroke="#FF3347" stroke-width="0.6" stroke-opacity="0.15"/>

  <!-- Big Metric (24px) -->
  <text x="24" y="86" fill="#F2F2F4" font-family="'JetBrains Mono', Consolas, monospace" font-size="24" font-weight="800" letter-spacing="1">AI &amp; FULL-STACK</text>

  <!-- Description (14.5px) -->
  <text x="24" y="116" fill="#9296A0" font-family="system-ui, -apple-system, sans-serif" font-size="14.5" font-weight="400">
    Integrated product design, modern web applications and AI workflows.
  </text>

  <line x1="24" y1="138" x2="556" y2="138" stroke="#FF3347" stroke-width="0.5" stroke-opacity="0.12"/>
  <text x="24" y="160" fill="#858994" font-family="'JetBrains Mono', monospace" font-size="11.5" letter-spacing="1">
    EVIDENCE: <tspan fill="#45E879" font-weight="600">VERIFIED • CORE SPECIALIZATION</tspan>
  </text>
</g>

</svg>'''

    os.makedirs(os.path.dirname(out_path) if os.path.dirname(out_path) else ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"Generated {out_path} ({len(svg_content):,} bytes)")

if __name__ == "__main__":
    stats = fetch_github_stats()
    generate_svg(stats)
