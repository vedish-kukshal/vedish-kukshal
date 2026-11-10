#!/usr/bin/env python3
"""Draws the animated SVG cards for the vedish-kukshal profile README.

One script, three commands:
  python scripts/build_cards.py fonts   one-off: subset the two fonts into fonts/*.woff (needs fonttools + the source TTFs)
  python scripts/build_cards.py fetch   pull the public contribution calendar into data/contributions.json (no login, no token)
  python scripts/build_cards.py build   draw every card into cards/ (including the contribution graph)
  python scripts/build_cards.py sample <repo>...   preview only: fill the graph from local git logs

Set STATIC=1 to draw the end state with no animation (use this for screenshots).

Method: GitHub strips scripts and CSS from README HTML but shows <img> SVGs, and an SVG shown
through <img> can carry its own <style> keyframes, SMIL and base64 fonts. So every visual block is
an SVG. Method credit: Avi Vashishta, "I Redesigned My GitHub Profile README With Animated SVG Cards".
Design, palette and copy here are Vedish's own.
"""
import base64, datetime, json, math, os, re, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC = os.environ.get("STATIC") == "1"
USER = "vedish-kukshal"

# palette: Snowball blue on paper, one accent
PAPER, EDGE, INK, MUTE = "#F6F8FC", "#DCE4F0", "#0F2440", "#5B6B82"
BLUE, BLUE_DEEP, ICE = "#2563EB", "#1D4ED8", "#E3EDFC"
SHINE = "#8FB4FF"

SRC_SERIF = os.environ.get("SERIF_TTF", "InstrumentSerif-Regular.ttf")  # Instrument Serif Regular, SIL OFL
SRC_SANS = os.environ.get("SANS_TTF", "Geist.ttf")  # Geist, SIL OFL


# ---------------------------------------------------------------- fonts
def make_fonts():
    from fontTools.ttLib import TTFont
    from fontTools import subset
    from fontTools.varLib import instancer
    os.makedirs(os.path.join(ROOT, "fonts"), exist_ok=True)
    for src, out, wght in ((SRC_SERIF, "serif-400.woff", None), (SRC_SANS, "sans-400.woff", 400)):
        f = TTFont(src)
        if "fvar" in f and wght:
            f = instancer.instantiateVariableFont(f, {"wght": wght})
        # check the name table before trusting a filename (the blog's trap: italic vs regular)
        print(out, "->", f["name"].getDebugName(1), "|", f["name"].getDebugName(2))
        opts = subset.Options()
        opts.flavor = "woff"
        opts.layout_features = ["*"]
        s = subset.Subsetter(opts)
        s.populate(unicodes=list(range(0x20, 0x7F)))
        s.subset(f)
        f.flavor = "woff"
        f.save(os.path.join(ROOT, "fonts", out))
        print("  saved", os.path.getsize(os.path.join(ROOT, "fonts", out)), "bytes")


def font_css():
    css = ""
    for fam, fn in (("Instrument Serif", "serif-400.woff"), ("Geist", "sans-400.woff")):
        b64 = base64.b64encode(open(os.path.join(ROOT, "fonts", fn), "rb").read()).decode()
        css += "@font-face{font-family:'%s';src:url(data:font/woff;base64,%s) format('woff')}" % (fam, b64)
    return css


SERIF = "'Instrument Serif',Georgia,serif"
SANS = "'Geist','Segoe UI',Arial,sans-serif"

KEYFRAMES = """
@keyframes rise{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}
@keyframes swing{0%{opacity:0;transform:translateY(34px) rotate(-5deg)}55%{opacity:1;transform:translateY(-6px) rotate(1.2deg)}78%{transform:translateY(2px) rotate(-.4deg)}100%{opacity:1;transform:none}}
@keyframes dot{from{opacity:0;transform:scale(.2)}to{opacity:1;transform:scale(1)}}
@keyframes ring{0%{opacity:.28;transform:scale(.1)}100%{opacity:0;transform:scale(1)}}
@keyframes sweep{0%{transform:translateX(-340px)}35%,100%{transform:translateX(420px)}}
@keyframes nudge{0%,100%{transform:translateX(0)}50%{transform:translateX(4px)}}
@keyframes draw{from{stroke-dashoffset:784}to{stroke-dashoffset:0}}
@keyframes pop{from{opacity:0;transform:scale(.3)}to{opacity:1;transform:scale(1)}}
.fb{transform-box:fill-box;transform-origin:center}
.bottom{transform-box:fill-box;transform-origin:50% 100%}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
"""


def svg_open(w, h, title, desc):
    anim = "" if STATIC else KEYFRAMES
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" role="img" aria-label="%s">'
            '<title>%s</title><desc>%s</desc><style>%s%s</style>') % (w, h, w, h, title, title, desc, font_css(), anim)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;")


def anim(cls_style):
    """inline animation style, or nothing in STATIC mode"""
    return "" if STATIC else cls_style


# ---------------------------------------------------------------- hero
def hero():
    W, H = 880, 300
    o = [svg_open(W, H, "Vedish Kukshal", "Builder, 19. Co-founder of Snowball. Ex co-founder of AceCard. Student at Masters Union.")]
    shine_anim = "" if STATIC else (
        '<animateTransform attributeName="gradientTransform" type="translate" values="-330 0;330 0;330 0" '
        'keyTimes="0;0.22;1" dur="7s" begin="1.6s" repeatCount="indefinite"/>')
    o.append('<defs><linearGradient id="shine" gradientUnits="userSpaceOnUse" x1="48" y1="0" x2="340" y2="0" '
             'gradientTransform="translate(-330 0)">%s'
             '<stop offset="0" stop-color="%s"/><stop offset=".42" stop-color="%s"/><stop offset=".5" stop-color="%s"/>'
             '<stop offset=".58" stop-color="%s"/><stop offset="1" stop-color="%s"/></linearGradient></defs>'
             % (shine_anim, BLUE, BLUE, SHINE, BLUE, BLUE))
    o.append('<rect x=".5" y=".5" width="%d" height="%d" rx="18" fill="%s" stroke="%s"/>' % (W - 1, H - 1, PAPER, EDGE))

    def rise(delay):
        return anim("animation:rise .8s cubic-bezier(.2,.8,.2,1) both;animation-delay:%.2fs" % delay)

    o.append('<g class="fb" style="%s"><text x="46" y="118" font-family="%s" font-size="92" fill="%s">Vedish</text></g>' % (rise(.1), SERIF, INK))
    o.append('<g class="fb" style="%s"><text x="46" y="200" font-family="%s" font-size="92" fill="url(#shine)">Kukshal</text></g>' % (rise(.25), SERIF))
    o.append('<g class="fb" style="%s"><text x="50" y="238" font-family="%s" font-size="18" fill="%s">Builder, 19. Co-founder of Snowball. Ex co-founder of AceCard.</text></g>' % (rise(.5), SANS, INK))
    o.append('<g class="fb" style="%s"><text x="50" y="262" font-family="%s" font-size="15" fill="%s">Student at Masters Union.</text></g>' % (rise(.65), SANS, MUTE))
    o.append('<g class="fb" style="%s"><text x="50" y="284" font-family="%s" font-size="14" fill="%s">linkedin.com/in/vedish</text></g>' % (rise(.8), SANS, BLUE))

    # the snowball: a halftone sphere of dots that prints in left to right
    cx, cy, R, step = 700, 150, 112, 9
    L = (-0.5, -0.6, 0.62)
    n = math.sqrt(sum(c * c for c in L))
    L = tuple(c / n for c in L)
    dots = []
    for gy in range(-R, R + 1, step):
        for gx in range(-R, R + 1, step):
            d2 = gx * gx + gy * gy
            if d2 > (R - 2) ** 2:
                continue
            z = math.sqrt(R * R - d2)
            lum = max(0.0, (gx * L[0] + gy * L[1] + z * L[2]) / R)
            lum = 0.08 + 0.92 * lum
            r = 0.7 + 3.5 * lum
            delay = 0.3 + (gx + R) / (2 * R) * 1.4 + (gy + R) / (2 * R) * 0.2
            fill = BLUE if lum > 0.35 else "#7FA6F7"
            st = anim("animation:dot .5s cubic-bezier(.2,.8,.2,1) both;animation-delay:%.2fs" % delay)
            dots.append('<circle class="fb" cx="%d" cy="%d" r="%.2f" fill="%s" style="%s"/>' % (cx + gx, cy + gy, r, fill, st))
    o.append("<g>%s</g>" % "".join(dots))
    o.append("</svg>")
    return "".join(o)


# ---------------------------------------------------------------- tiles
def arrow(x, y, color, delay):
    st = anim("animation:nudge 2.4s ease-in-out infinite;animation-delay:%.2fs" % delay)
    return ('<g class="fb" style="%s"><path d="M%d %d h16 m-6 -6 l6 6 l-6 6" fill="none" stroke="%s" '
            'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></g>') % (st, x, y, color)


def tile(name, lines, foot, bg, fg, sub, delay, link=True, ring=True):
    W, H = 288, 200
    o = [svg_open(W, H, name, " ".join(lines))]
    o.append('<defs><clipPath id="c"><rect width="%d" height="%d" rx="18"/></clipPath></defs>' % (W, H))
    swing = anim("animation:swing .95s cubic-bezier(.2,.8,.2,1) both;animation-delay:%.2fs" % delay)
    o.append('<g class="bottom" style="%s">' % swing)
    o.append('<g clip-path="url(#c)"><rect width="%d" height="%d" fill="%s"/>' % (W, H, bg))
    if ring and not STATIC:
        rs = anim("animation:ring 5s ease-out infinite both;animation-delay:%.2fs" % (delay + 1.2))
        o.append('<circle class="fb" cx="%d" cy="0" r="150" fill="none" stroke="%s" stroke-width="1.5" style="%s"/>' % (W, fg, rs))
    if not STATIC:
        o.append('<rect x="0" y="-20" width="56" height="240" fill="#fff" opacity=".13" transform="rotate(18 28 100)" '
                 'style="animation:sweep 7s ease-in-out infinite both;animation-delay:%.2fs"/>' % (delay + 2.0))
    o.append("</g>")
    o.append('<text x="24" y="66" font-family="%s" font-size="40" fill="%s">%s</text>' % (SERIF, fg, esc(name)))
    for i, ln in enumerate(lines):
        o.append('<text x="24" y="%d" font-family="%s" font-size="14.5" fill="%s">%s</text>' % (104 + i * 21, SANS, fg, esc(ln)))
    o.append('<text x="24" y="176" font-family="%s" font-size="13" fill="%s">%s</text>' % (SANS, sub, esc(foot)))
    if link:
        o.append(arrow(W - 44, 171, fg, delay + 1.0))
    o.append("</g></svg>")
    return "".join(o)


# ---------------------------------------------------------------- Starter Pack card
# Every line below is from the live page https://snowballgtm.com/starter/ (read 11 Nov 2026).
# No price, no client names, no client numbers on purpose.
STARTER_URL = "https://snowballgtm.com/starter/"
STARTER_ALT = ("Snowball 3 Day Personal Brand Starter Pack, for executive coaches. "
               "Executive coaches: you're better than your LinkedIn shows. In 3 days, it shows. "
               "Day 1: a call, and your LinkedIn connected without your password. "
               "Day 3: your strategy, a rewritten profile and your own website. "
               "Monday: one line runs your week, and comments and outreach run while you coach. "
               "USD 997 once, then USD 29 a month. You also bring your own Claude Pro plan, about USD 20 a month, paid to Anthropic. "
               "See what a CEO finds, free.")
STARTER_COLS = [
    ("Day 1", ["A call. We connect your", "LinkedIn with you, and you", "never hand over a password."]),
    ("Day 3", ["Your strategy, a rewritten", "profile and your own website."]),
    ("Monday", ["One line runs your week.", "Comments and outreach run", "while you coach."]),
]


def starter():
    W, H = 880, 396
    o = [svg_open(W, H, "3 Day Personal Brand Starter Pack", STARTER_ALT)]
    o.append('<rect x=".5" y=".5" width="%d" height="%d" rx="18" fill="%s" stroke="%s"/>' % (W - 1, H - 1, PAPER, EDGE))

    def rise(d):
        return anim("animation:rise .8s cubic-bezier(.2,.8,.2,1) both;animation-delay:%.2fs" % d)

    o.append('<g class="fb" style="%s"><text x="44" y="82" font-family="%s" font-size="44" fill="%s">3 Day Personal Brand <tspan fill="%s">Starter Pack</tspan></text></g>'
             % (rise(.1), SERIF, INK, BLUE))
    for i, ln in enumerate(["Executive coaches: you're better than your LinkedIn shows.", "In 3 days, it shows."]):
        o.append('<g class="fb" style="%s"><text x="46" y="%d" font-family="%s" font-size="17" fill="%s">%s</text></g>'
                 % (rise(.25 + i * .12), 118 + i * 24, SANS, INK, esc(ln)))

    # the button, same blue as the Snowball tile
    bx, by, bw, bh = 584, 100, 252, 46
    o.append('<g class="fb" style="%s"><rect x="%d" y="%d" width="%d" height="%d" rx="12" fill="%s"/>'
             '<text x="%d" y="%d" font-family="%s" font-size="15" fill="#FFFFFF">See what a CEO finds, free</text>%s</g>'
             % (rise(.5), bx, by, bw, bh, BLUE, bx + 20, by + 28, SANS, arrow(bx + bw - 36, by + 23, "#FFFFFF", 1.5)))

    # the price, as the launch files state it (Snowball/pipeline/starter-pack-launch/README.md, COPY-DECK)
    o.append('<g class="fb" style="%s"><text x="44" y="196" font-family="%s" font-size="34" fill="%s"><tspan fill="%s">USD 997</tspan> once, then USD 29 a month.</text></g>'
             % (rise(.6), SERIF, INK, BLUE))
    o.append('<g class="fb" style="%s"><text x="46" y="222" font-family="%s" font-size="14.5" fill="%s">You also bring your own Claude Pro plan, about USD 20 a month, paid to Anthropic.</text></g>'
             % (rise(.7), SANS, MUTE))

    # the visual: one line from the call to the handover to the weekly rhythm
    ty = 258
    xs = [52, 348, 644]
    track = anim("stroke-dasharray:784;animation:draw 1.6s cubic-bezier(.4,0,.2,1) both;animation-delay:.7s")
    o.append('<line x1="52" y1="%d" x2="836" y2="%d" stroke="%s" stroke-width="2" stroke-linecap="round"/>' % (ty, ty, EDGE))
    o.append('<line x1="52" y1="%d" x2="836" y2="%d" stroke="%s" stroke-width="2" stroke-linecap="round" style="%s"/>' % (ty, ty, BLUE, track))
    for k, (x, (label, lines)) in enumerate(zip(xs, STARTER_COLS)):
        d = .8 + k * .55
        pop = anim("animation:pop .5s cubic-bezier(.2,.8,.2,1) both;animation-delay:%.2fs" % d)
        o.append('<circle class="fb" cx="%d" cy="%d" r="9" fill="%s" stroke="%s" stroke-width="3" style="%s"/>' % (x, ty, BLUE, PAPER, pop))
        st = rise(d + .1)
        body = '<text x="%d" y="%d" font-family="%s" font-size="30" fill="%s">%s</text>' % (x - 8, ty + 46, SERIF, INK, esc(label))
        body += "".join('<text x="%d" y="%d" font-family="%s" font-size="14.5" fill="%s">%s</text>' % (x - 8, ty + 72 + i * 21, SANS, MUTE, esc(t))
                        for i, t in enumerate(lines))
        o.append('<g class="fb" style="%s">%s</g>' % (st, body))
    o.append("</svg>")
    return "".join(o)


# ---------------------------------------------------------------- how I build / what I solve
# Wording sources (all Vedish's own, from the vault): CLAUDE.md (partially technical, understands
# architecture, does not code), Snowball build principles (first principles, borrow the best base,
# document everything), the Snowball positioning page (gap between how good you are and how known
# you are), the AceCard project note (if the meeting happened, the system knows).
HOW = [
    ["I don't write the code by hand.", "I design the system, then direct AI", "agents to build it."],
    ["I start from first principles, strip", "it down, and borrow the best base", "instead of building from zero."],
    ["I write everything down, so the next", "build starts smarter than the last."],
]
SOLVE = [
    ["People whose work is bigger than", "their reach. Snowball gets them known", "for what they have already done."],
    ["The meeting that never reaches the", "CRM. AceCard turns what was said", "into the record."],
]


def how():
    W, H = 880, 330
    o = [svg_open(W, H, "How I build, and what I solve",
                  "How I build: " + " ".join(" ".join(i) for i in HOW) + " What I solve: " + " ".join(" ".join(i) for i in SOLVE))]
    o.append('<rect x=".5" y=".5" width="%d" height="%d" rx="18" fill="%s" stroke="%s"/>' % (W - 1, H - 1, PAPER, EDGE))
    o.append('<line x1="440" y1="36" x2="440" y2="%d" stroke="%s"/>' % (H - 36, EDGE))

    def col(x, title, items, base_delay, accent):
        st = anim("animation:rise .8s cubic-bezier(.2,.8,.2,1) both;animation-delay:%.2fs" % base_delay)
        g = ['<g class="fb" style="%s"><text x="%d" y="72" font-family="%s" font-size="38" fill="%s">%s<tspan fill="%s">%s</tspan></text></g>'
             % (st, x, SERIF, INK, esc(title[0]), accent, esc(title[1]))]
        y = 116
        for k, item in enumerate(items):
            d = base_delay + 0.25 + k * 0.2
            st = anim("animation:rise .8s cubic-bezier(.2,.8,.2,1) both;animation-delay:%.2fs" % d)
            ds = anim("animation:pop .5s cubic-bezier(.2,.8,.2,1) both;animation-delay:%.2fs" % d)
            g.append('<circle class="fb" cx="%d" cy="%d" r="4" fill="%s" style="%s"/>' % (x + 4, y - 5, accent, ds))
            lines = "".join('<text x="%d" y="%d" font-family="%s" font-size="14.5" fill="%s">%s</text>' % (x + 20, y + i * 21, SANS, INK, esc(t))
                            for i, t in enumerate(item))
            g.append('<g class="fb" style="%s">%s</g>' % (st, lines))
            y += len(item) * 21 + 18
        return "".join(g)

    o.append(col(44, ("How I ", "build"), HOW, 0.1, BLUE))
    o.append(col(480, ("What I ", "solve"), SOLVE, 0.4, BLUE))
    o.append("</svg>")
    return "".join(o)


# ---------------------------------------------------------------- optional graph (off by default)
def graph():
    data = json.load(open(os.path.join(ROOT, "data", "contributions.json")))
    days = data["days"]
    W, cell, gap = 880, 12, 3
    cols = max(d["col"] for d in days) + 1
    gw = cols * (cell + gap)
    H = 230
    o = [svg_open(W, H, "Contributions in the last year", "%d contributions in the last year." % data["total"])]
    o.append('<rect x=".5" y=".5" width="%d" height="%d" rx="18" fill="%s" stroke="%s"/>' % (W - 1, H - 1, PAPER, EDGE))
    o.append('<text x="40" y="64" font-family="%s" font-size="34" fill="%s">The last year, <tspan fill="%s">in blue</tspan></text>' % (SERIF, INK, BLUE))
    o.append('<text x="%d" y="62" text-anchor="end" font-family="%s" font-size="14" fill="%s">%s contributions</text>' % (W - 40, SANS, MUTE, format(data["total"], ",")))
    palette = ["#E4EAF5", "#BFD3FB", "#7FA6F7", "#3D75EE", "#1D4ED8"]
    x0, y0 = (W - gw + gap) / 2, 92
    for d in days:
        x = x0 + d["col"] * (cell + gap)
        y = y0 + d["row"] * (cell + gap)
        st = anim("animation:pop .4s cubic-bezier(.2,.8,.2,1) both;animation-delay:%.2fs" % (0.2 + d["col"] * 0.025))
        o.append('<rect class="fb" x="%.1f" y="%.1f" width="%d" height="%d" rx="3" fill="%s" style="%s"/>' % (x, y, cell, cell, palette[d["level"]], st))
    o.append("</svg>")
    return "".join(o)


# ---------------------------------------------------------------- data
def fetch():
    req = urllib.request.Request("https://github.com/users/%s/contributions" % USER, headers={"User-Agent": "Mozilla/5.0"})
    h = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
    tips = {}
    for m in re.finditer(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)</tool-tip>', h):
        t = m.group(2).strip()
        c = re.match(r"(\d+) contribution", t)
        tips[m.group(1)] = int(c.group(1)) if c else 0
    days = []
    for m in re.finditer(r'<td[^>]*data-date="([^"]+)"[^>]*id="(contribution-day-component-(\d+)-(\d+))"[^>]*data-level="(\d)"', h):
        date, cid, row, col, lvl = m.groups()
        days.append({"date": date, "row": int(row), "col": int(col), "level": int(lvl), "count": tips.get(cid, 0)})
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    out = {"user": USER, "fetched": datetime.date.today().isoformat(), "total": sum(d["count"] for d in days), "days": days}
    json.dump(out, open(os.path.join(ROOT, "data", "contributions.json"), "w"), indent=1)
    print("fetched", len(days), "days,", out["total"], "contributions")


def sample():
    """PREVIEW ONLY: python scripts/build_cards.py sample <repo> [<repo> ...]
    Fills the graph grid from the local git log of the repos given, to show what GitHub would count once
    'Include private contributions' is on. Run `fetch` to replace it with GitHub's real numbers."""
    import collections, math, subprocess
    path = os.path.join(ROOT, "data", "contributions.json")
    data = json.load(open(path))
    per = collections.Counter()
    for repo in sys.argv[2:]:
        out = subprocess.run(["git", "-C", repo, "log", "--since=1 year ago", "--format=%ad", "--date=short"],
                             capture_output=True, text=True).stdout.split()
        per.update(out)
    top = max([per.get(d["date"], 0) for d in data["days"]] + [1])
    for d in data["days"]:
        c = per.get(d["date"], 0)
        d["count"], d["level"] = c, (0 if c == 0 else min(4, math.ceil(4 * c / top)))
    data["total"] = sum(d["count"] for d in data["days"])
    data["source"] = "local git log, preview only"
    json.dump(data, open(path, "w"), indent=1)
    print("sampled", data["total"], "commits, busiest day", top)


# ---------------------------------------------------------------- build
def build():
    os.makedirs(os.path.join(ROOT, "cards"), exist_ok=True)
    cards = {
        "cards/hero.svg": hero(),
        "cards/snowball.svg": tile(
            "Snowball", ["AI-native LinkedIn growth for", "investors and founders."], "Since 2024",
            BLUE, "#FFFFFF", "#DBE7FF", 1.0),
        "cards/acecard.svg": tile(
            "AceCard", ["A digital business card that", "turns what you say after a", "meeting into a CRM record."], "Ex co-founder",
            ICE, INK, MUTE, 1.15, link=False),
        "cards/masters-union.svg": tile(
            "Masters Union", ["Studying here while I", "build Snowball."], "Currently enrolled",
            INK, "#FFFFFF", "#93C5FD", 1.3, link=False),
    }
    cards["cards/starter-pack.svg"] = starter()
    cards["cards/how-i-build.svg"] = how()
    if os.path.exists(os.path.join(ROOT, "data", "contributions.json")):
        cards["cards/graph.svg"] = graph()
    for p, s in cards.items():
        open(os.path.join(ROOT, p), "w", encoding="utf-8", newline="\n").write(s)
        print("wrote", p, len(s) // 1024, "KB", "(static)" if STATIC else "")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    {"fonts": make_fonts, "fetch": fetch, "build": build, "sample": sample}[cmd]()
