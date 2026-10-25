"""Genera los SVG del README de perfil (Repo Galaxy, Brightest stars, Language Stack,
Transmission) con datos de la API de GitHub y actualiza la frase de números del README.
Proyectos destacados: manuales, desde config.json. Solo stdlib."""
import json, os, random, math, html, re, urllib.request, datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "assets") + os.sep
CFG = json.load(open(os.path.join(ROOT, "config.json"), encoding="utf-8"))
USER = CFG["username"]
TOKEN = os.environ.get("GITHUB_TOKEN", "")

# ------------------------------------------------------------ datos
def api(url, data=None):
    h = {"Accept": "application/vnd.github+json", "User-Agent": "profile-readme"}
    if TOKEN: h["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, data=data, headers=h)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)

def get_data():
    d = {"stats": dict(CFG["fallback_stats"]), "langs": dict(CFG["fallback_languages"]),
         "repos": [{"name": p["repo"].split("/")[-1], "stars": 0, "language": p.get("language")} for p in CFG["projects"]]}
    try:
        u = api(f"https://api.github.com/users/{USER}")
        d["stats"]["repos"], d["stats"]["followers"] = u["public_repos"], u["followers"]
        repos, page = [], 1
        while True:
            r = api(f"https://api.github.com/users/{USER}/repos?per_page=100&page={page}")
            repos += r
            if len(r) < 100: break
            page += 1
        repos = [r for r in repos if not r["fork"]]
        d["stats"]["stars"] = sum(r["stargazers_count"] for r in repos)
        d["repos"] = [{"name": r["name"], "stars": r["stargazers_count"], "language": r["language"]} for r in repos]
        langs = {}
        for r in repos:
            try:
                for k, v in api(r["languages_url"]).items(): langs[k] = langs.get(k, 0) + v
            except Exception: pass
        tot = sum(langs.values())
        if tot: d["langs"] = {k: round(v*100/tot) for k, v in sorted(langs.items(), key=lambda x: -x[1])}
    except Exception as e:
        print("REST falló, uso valores de respaldo:", e)
    try:
        q = {"query": "query($l:String!){user(login:$l){contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{contributionCount}}}}}}",
             "variables": {"l": USER}}
        cal = api("https://api.github.com/graphql", json.dumps(q).encode())["data"]["user"]["contributionsCollection"]["contributionCalendar"]
        d["stats"]["contributions"] = cal["totalContributions"]
        best = cur = 0
        for w in cal["weeks"]:
            for day in w["contributionDays"]:
                cur = cur + 1 if day["contributionCount"] > 0 else 0
                best = max(best, cur)
        d["stats"]["streak"] = best
    except Exception as e:
        print("GraphQL falló, uso valores de respaldo:", e)
    return d

def rel(ts):
    try:
        t = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        s = (datetime.datetime.now(datetime.timezone.utc) - t).total_seconds()
        for n, u in ((86400*30, "mo"), (86400, "d"), (3600, "h"), (60, "m")):
            if s >= n: return f"updated {int(s//n)}{u} ago"
        return "updated just now"
    except Exception: return "updated recently"

def get_projects(d):
    out = []
    for p in CFG["projects"]:
        name = p["repo"].split("/")[-1]
        info = dict(name=name, desc=p.get("description", ""), stars=0, lang=p.get("language"), pct=None, upd="updated recently")
        try:
            r = api(f"https://api.github.com/repos/{p['repo']}")
            info["stars"] = r["stargazers_count"]; info["lang"] = r["language"] or info["lang"]
            info["upd"] = rel(r["pushed_at"])
            if not info["desc"]: info["desc"] = r.get("description") or ""
            ls = api(r["languages_url"]); tot = sum(ls.values())
            if tot and info["lang"] in ls: info["pct"] = round(ls[info["lang"]]*100/tot)
        except Exception as e:
            print(f"No pude leer {p['repo']}:", e)
        out.append(info)
    return out

# ------------------------------------------------------------ diseño
SANS = "'Segoe UI','Helvetica Neue',Arial,sans-serif"
MONO = "'JetBrains Mono','SFMono-Regular',Consolas,'Courier New',monospace"
BG1, BG2 = "#06050f", "#150a2b"
AC, AC2, AC3 = "#a855f7", "#c084fc", "#e879f9"
TX, MUTED = "#f5ebff", "#9d8ec4"
LC = {"JavaScript": "#f1d948", "HTML": "#ef5b3c", "Java": "#e8a33d", "CSS": "#9b5de5", "TypeScript": "#4c8dff",
      "Python": "#5b9bd5", "Dockerfile": "#7a8b99", "Shell": "#7ee081", "C#": "#4cc38a", "PHP": "#8892bf"}
def lc(n): return LC.get(n, AC2)
esc = html.escape

def defs(w, h):
    return f'''<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BG1}"/><stop offset="1" stop-color="{BG2}"/></linearGradient>
<linearGradient id="ln" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{AC3}"/><stop offset="1" stop-color="#6d28d9"/></linearGradient>
<linearGradient id="glass" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".07"/><stop offset="1" stop-color="#fff" stop-opacity=".015"/></linearGradient>
<radialGradient id="orb1" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{AC}" stop-opacity=".45"/><stop offset="1" stop-color="{AC}" stop-opacity="0"/></radialGradient>
<radialGradient id="orb2" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#22d3ee" stop-opacity=".22"/><stop offset="1" stop-color="#22d3ee" stop-opacity="0"/></radialGradient>
<radialGradient id="core" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#fff" stop-opacity=".9"/><stop offset=".25" stop-color="{AC2}" stop-opacity=".55"/><stop offset="1" stop-color="{AC}" stop-opacity="0"/></radialGradient>
<filter id="glow" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="2.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<clipPath id="clip"><rect width="{w}" height="{h}" rx="20"/></clipPath>
</defs>'''

def frame(w, h, body, seed=1, stars=30):
    random.seed(seed); s = ""
    for _ in range(stars):
        x, y = random.randint(8, w-8), random.randint(8, h-8)
        s += f'<circle cx="{x}" cy="{y}" r="{random.choice([.6,.9,1.1])}" fill="#fff" opacity=".6"><animate attributeName="opacity" values=".1;.8;.1" dur="{random.uniform(2,5):.1f}s" begin="{random.uniform(0,4):.1f}s" repeatCount="indefinite"/></circle>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="{SANS}">
{defs(w,h)}
<g clip-path="url(#clip)">
<rect width="{w}" height="{h}" fill="url(#bg)"/>
<circle cx="{w*0.12}" cy="{h*0.1}" r="{max(w,h)*0.35}" fill="url(#orb1)"/>
<circle cx="{w*0.9}" cy="{h*0.95}" r="{max(w,h)*0.3}" fill="url(#orb2)"/>
{s}{body}
<text x="{w-14}" y="{h-10}" text-anchor="end" font-size="9" fill="{MUTED}" opacity=".7" font-family="{MONO}">profile.dev</text>
</g>
<rect x=".75" y=".75" width="{w-1.5}" height="{h-1.5}" rx="20" fill="none" stroke="url(#ln)" stroke-opacity=".5" stroke-width="1.5"/>
</svg>'''

def panel(x, y, w, h, r=14, op=.5, fill="url(#glass)"):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{AC}" stroke-opacity="{op}"/>'

def save(name, svg):
    os.makedirs(OUT, exist_ok=True)
    open(OUT + name, "w", encoding="utf-8").write(svg)

def clip(t, n): return t if len(t) <= n else t[:n-1] + "…"

# ---------- 1) Repo Galaxy
def galaxy(d):
    W, H = 840, 330; cx, cy = 585, 168
    langs = list(d["langs"].items())[:4]
    stats = d["stats"]; nrepos = stats["repos"]
    random.seed(42); dots = ""
    tot = sum(max(p, 1) for _, p in langs) or 1
    for k, (ln, pct) in enumerate(langs):
        n = int(40 + 220 * max(pct, 1) / tot); col = lc(ln)
        for i in range(n):
            t = random.random()**0.8; r = 14 + t*150
            a = k*math.pi/2 + t*3.4 + random.gauss(0, .22)
            x = cx + r*math.cos(a)*1.55*math.cos(-.25) - r*math.sin(a)*.8*math.sin(-.25)
            y = cy + r*math.cos(a)*1.55*math.sin(-.25) + r*math.sin(a)*.8*math.cos(-.25)
            if 20 < x < W-20 and 20 < y < H-20:
                dots += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{random.choice([.6,.9,1.2,1.6]):.1f}" fill="{col}" opacity="{random.uniform(.35,.9):.2f}"/>'
    labels = ""; angs = [200, 150, 105, 20, 330, 70, 255]; rads = [78, 62, 70, 84, 70, 58, 66]
    for i, r in enumerate(d["repos"][:7]):
        a = math.radians(angs[i]); dx, dy = rads[i]*math.cos(a)*1.3, rads[i]*math.sin(a)*.95
        x, y = cx+dx, cy+dy; col = lc(r["language"]); rr = 3 + min(r["stars"], 20)*.3
        right = dx >= 0
        labels += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rr+4:.1f}" fill="{col}" opacity=".18"/><circle cx="{x:.1f}" cy="{y:.1f}" r="{rr:.1f}" fill="{col}" filter="url(#glow)"/>'
        nm = clip(r["name"], 20); st = f"★ {r['stars']}"; sw = len(st)*6.6 + 8; nw = len(nm)*6.6 + 8
        if right:
            x0 = x + rr + 6
            labels += f'<text x="{x0:.1f}" y="{y+4:.1f}" font-size="11" font-weight="600" fill="{TX}">{esc(nm)}</text><text x="{x0+nw:.1f}" y="{y+4:.1f}" font-size="11" fill="{AC2}">{st}</text>'
        else:
            x0 = x - rr - 6
            labels += f'<text x="{x0:.1f}" y="{y+4:.1f}" text-anchor="end" font-size="11" fill="{AC2}">{st}</text><text x="{x0-sw:.1f}" y="{y+4:.1f}" text-anchor="end" font-size="11" font-weight="600" fill="{TX}">{esc(nm)}</text>'
    legend = ""
    for i, (ln, pct) in enumerate(langs):
        y = 232 + i*20
        legend += f'<circle cx="52" cy="{y-4}" r="4.5" fill="{lc(ln)}"/><text x="66" y="{y}" font-size="11" font-weight="700" fill="{TX}" font-family="{MONO}">{esc(ln)}</text><text x="236" y="{y}" text-anchor="end" font-size="11" fill="{MUTED}" font-family="{MONO}">{pct}%</text>'
    body = panel(18, 18, W-36, H-36, 16, .55) + f'''
<ellipse cx="{cx}" cy="{cy}" rx="190" ry="105" fill="none" stroke="{AC}" stroke-opacity=".12" transform="rotate(-14 {cx} {cy})"/>
<ellipse cx="{cx}" cy="{cy}" rx="110" ry="62" fill="none" stroke="{AC2}" stroke-opacity=".18" transform="rotate(-14 {cx} {cy})"/>
{dots}
<circle cx="{cx}" cy="{cy}" r="38" fill="url(#core)"><animate attributeName="r" values="34;42;34" dur="4s" repeatCount="indefinite"/></circle>
<circle cx="{cx}" cy="{cy}" r="3" fill="#fff"/>
{labels}
<text x="52" y="68" font-size="10" letter-spacing="3" fill="{AC2}" font-family="{MONO}">REPO GALAXY</text>
<text x="52" y="102" font-size="26" font-weight="700" fill="{TX}">@{esc(USER)}</text>
<text x="52" y="126" font-size="12" font-weight="600" fill="{AC2}" font-family="{MONO}">{stats["stars"]} stars · {nrepos} repositories</text>
<text x="52" y="150" font-size="10.5" fill="{MUTED}">Each star is a repository, sized by its stars.</text>
<text x="52" y="204" font-size="9" letter-spacing="2.5" fill="{AC2}" font-family="{MONO}">ARMS</text>
{legend}'''
    save("galaxy.svg", frame(W, H, body, 3, 24))

# ---------- 2) Brightest stars (projects)
def projects(plist):
    W = 840; cw, ch, gx, gy = 372, 150, 24, 16
    rows = (len(plist)+1)//2; H = 74 + rows*ch + (rows-1)*gy + 36
    body = panel(18, 18, W-36, H-36, 16, .5) + f'''
<text x="44" y="52" font-size="11" letter-spacing="2" fill="{AC2}" font-family="{MONO}">PROJECTS.LIST</text>
<text x="190" y="52" font-size="11" fill="{MUTED}" font-family="{MONO}">./projects.sh --all</text>
<text x="{W-44}" y="52" text-anchor="end" font-size="11" fill="{MUTED}" font-family="{MONO}">{len(plist)} projects</text>
<line x1="44" y1="62" x2="{W-44}" y2="62" stroke="{AC}" stroke-opacity=".35"/>'''
    for i, p in enumerate(plist):
        x = 44 + (i % 2)*(cw+gx - 8); y = 78 + (i//2)*(ch+gy); w = cw - 8
        body += panel(x, y, w, ch, 12, .5, "#0d0820")
        body += f'''<text x="{x+16}" y="{y+26}" font-size="10" fill="{AC2}" font-family="{MONO}">• {esc(clip(p["name"],26))}</text>
<circle cx="{x+w-16}" cy="{y+22}" r="3.5" fill="#34d399" filter="url(#glow)"/>
<text x="{x+16}" y="{y+62}" font-size="19" font-weight="700" fill="{TX}" font-family="{MONO}">{esc(clip(p["name"],22))}</text>
<text x="{x+16}" y="{y+84}" font-size="11.5" fill="{MUTED}">{esc(clip(p["desc"] or "No description provided.",42))}</text>'''
        if p["lang"]:
            lw = len(p["lang"])*7 + 22
            body += f'<rect x="{x+16}" y="{y+96}" width="{lw}" height="20" rx="10" fill="{lc(p["lang"])}" fill-opacity=".12" stroke="{lc(p["lang"])}" stroke-opacity=".6"/><text x="{x+16+lw/2}" y="{y+110}" text-anchor="middle" font-size="10" fill="{TX}" font-family="{MONO}">{esc(p["lang"])}</text>'
        body += f'<text x="{x+16}" y="{y+ch-14}" font-size="10.5" fill="{AC2}" font-family="{MONO}">★ {p["stars"]}  <tspan fill="{MUTED}">{esc(p["upd"])}</tspan></text>'
        if p["pct"] is not None:
            cxx, cyy, r = x+w-46, y+ch-48, 20; circ = 2*math.pi*r
            body += f'''<circle cx="{cxx}" cy="{cyy}" r="{r}" fill="none" stroke="{AC}" stroke-opacity=".2" stroke-width="5"/>
<circle cx="{cxx}" cy="{cyy}" r="{r}" fill="none" stroke="{lc(p["lang"])}" stroke-width="5" stroke-dasharray="{circ*p["pct"]/100:.1f} {circ:.1f}" transform="rotate(-90 {cxx} {cyy})" stroke-linecap="round"/>
<text x="{cxx}" y="{cyy+4}" text-anchor="middle" font-size="10" font-weight="700" fill="{TX}" font-family="{MONO}">{p["pct"]}%</text>'''
    save("projects.svg", frame(W, H, body, 5, 20))

# ---------- 3) Language Stack
def languages(d):
    items = list(d["langs"].items())[:6]; W = 840; H = 162 + len(items)*38
    body = panel(18, 18, W-36, H-36, 16, .5) + panel(34, 34, W-68, H-68, 12, .45, "#0b0720") + f'''
<text x="58" y="78" font-size="26" font-weight="800" fill="{TX}">Language Stack</text>
<text x="58" y="100" font-size="11.5" font-weight="700" fill="{AC2}" font-family="{MONO}">Repository-weighted technologies</text>
<text x="{W-70}" y="74" text-anchor="end" font-size="12" fill="{AC2}" font-family="{MONO}">&gt; stack.scan <tspan>_<animate attributeName="opacity" values="1;0;1" dur="1.2s" repeatCount="indefinite"/></tspan></text>'''
    for i, (ln, pct) in enumerate(items):
        y = 140 + i*38; col = lc(ln); bw = max(8, 470*pct/100)
        body += f'''<circle cx="64" cy="{y-4}" r="5" fill="{col}"/>
<text x="82" y="{y}" font-size="13" font-weight="700" fill="{TX}" font-family="{MONO}">{esc(ln)}</text>
<text x="250" y="{y}" text-anchor="end" font-size="13" font-weight="800" fill="{col}" font-family="{MONO}">{pct}%</text>
<rect x="290" y="{y-10}" width="480" height="10" rx="5" fill="#fff" fill-opacity=".08"/>
<rect x="290" y="{y-10}" width="{bw}" height="10" rx="5" fill="{col}" filter="url(#glow)"/>'''
    save("languages.svg", frame(W, H, body, 7, 14))

# ---------- 4) Transmission
def transmission():
    W, H = 840, 150
    body = panel(18, 18, W-36, H-36, 16, .5) + panel(34, 34, W-68, H-68, 12, .4, "#0b0720") + f'''
<g transform="translate({W/2-110},{H/2-26})"><rect width="220" height="52" rx="26" fill="{AC}" fill-opacity=".16" stroke="url(#ln)" stroke-width="1.6" filter="url(#glow)"/>
<circle cx="28" cy="26" r="15" fill="#120a26" stroke="{AC2}" stroke-opacity=".7"/><text x="28" y="31" text-anchor="middle" font-size="14" font-weight="700" fill="{TX}">G</text>
<text x="54" y="21" font-size="9" fill="{AC2}" font-family="{MONO}">GitHub</text>
<text x="54" y="38" font-size="14" font-weight="700" fill="{TX}">@{esc(USER)}</text></g>'''
    save("transmission.svg", frame(W, H, body, 11, 14))

# ---------- README: frase de números
def update_readme(s):
    path = os.path.join(ROOT, "README.md")
    if not os.path.exists(path): return
    fol = "follower" if s["followers"] == 1 else "followers"
    day = "day" if s["streak"] == 1 else "days"
    line = (f"**{s['repos']}** public repositories, **{s['stars']}** stars, **{s['contributions']}** contributions in the last year, "
            f"a longest streak of **{s['streak']}** {day} and **{s['followers']}** {fol}.")
    txt = open(path, encoding="utf-8").read()
    new = re.sub(r"(<!--STATS-->).*?(<!--/STATS-->)", lambda m: f"{m.group(1)}\n{line}\n{m.group(2)}", txt, flags=re.S)
    if new != txt: open(path, "w", encoding="utf-8").write(new)

if __name__ == "__main__":
    d = get_data(); print("stats:", d["stats"]); print("langs:", d["langs"])
    galaxy(d); projects(get_projects(d)); languages(d); transmission(); update_readme(d["stats"])
    print("listo")
