"""Step 3 of the pipeline (python make.py build).  THIS IS THE FILE TO EDIT for any change to the website.
Build the e-invite website from the extracted PDF model.
Unchanged text is drawn with the PDF's own glyph outlines at their exact positions.
Only the items in the CHANGES list are altered."""
import json, re, os, sys, html
from svgpathtools import parse_path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths, shutil
S = paths.DATA                     # model.json, opacity.json, svgsrc/ live here
SITE = paths.WEBSITE               # output: Website/index.html (+ images/, fonts/)
MODE = sys.argv[1] if len(sys.argv) > 1 else "site"   # "site" -> index.html, "test" -> test.html (all images load at once)
model = json.load(open(f"{S}/model.json", encoding="utf-8"))
OPAC = json.load(open(f"{S}/opacity.json", encoding="utf-8"))
os.makedirs(f"{SITE}/fonts", exist_ok=True)
for _f in os.listdir(paths.FONTS):
    shutil.copy2(os.path.join(paths.FONTS, _f), os.path.join(SITE, "fonts", _f))

# ---------------- decisions agreed with the user ----------------
PARENTS = {
    "soumya": ["Daughter of Mrs. Rashmi Gupta &", "Mr. Umakant Gupta"],
    "madhur": ["Son of Mrs. Bhavna Gupta &", "Mr. Santosh Gupta"],
}
NAME_SHRINK = 0.05          # script names: line 5% narrower via tighter letter spacing
HINDI_TRACK_CUT = 0.86      # pt removed between glyphs (the line's added tracking)
VENUE_SIZE = 31.0           # was 34.5 semibold italic -> 31 regular italic
SMALL_AMP = 0.5             # "&" in split titles at half the title size

MAPS = {"havana": "https://maps.app.goo.gl/NSd9deR3CCMiEXvz9",
        "royal": "https://www.google.com/maps/search/?api=1&amp;query=The+Royal+Resort+Orchha+Tigela+Orchha"}

# ---------------- glyphs from the PDF ----------------
glyph_defs = {}             # id -> d (font units, y up)
glyph_bbox = {}             # id -> (xmin, xmax, ymin, ymax) font units

def load_svg(n):
    s = open(f"{S}/svgsrc/p{n}.svg", encoding="utf-8").read()
    for m in re.finditer(r'<path id="(font_[0-9_]+)" d="([^"]*)"', s):
        gid, d = m.group(1), m.group(2)
        key = f"p{n}_{gid}"
        glyph_defs[key] = d
        if d.strip():
            try:
                xmin, xmax, ymin, ymax = parse_path(d).bbox()
            except Exception:
                xmin = xmax = ymin = ymax = 0
            glyph_bbox[key] = (xmin, xmax, ymin, ymax)
        else:
            glyph_bbox[key] = None
    for m in re.finditer(r'<g id="(font_[0-9_]+)">\s*<path transform="matrix\(\.001,0,0,-\.001,0,0\)" d="([^"]*)"/>\s*</g>', s):
        key = f"p{n}_{m.group(1)}"
        d = parse_path(m.group(2)).scaled(0.001, -0.001).d()
        glyph_defs[key] = d
        xmin, xmax, ymin, ymax = parse_path(d).bbox()
        glyph_bbox[key] = (xmin, xmax, ymin, ymax)
    uses = []
    for m in re.finditer(r'<use data-text="([^"]*)" xlink:href="#(font_[0-9_]+)" transform="matrix\(([^)]*)\)"(?: fill="([^"]*)")?', s):
        a, b, c, d, e, f = [float(v) for v in m.group(3).split(",")]
        uses.append({"t": html.unescape(m.group(1)), "g": f"p{n}_{m.group(2)}",
                     "size": a, "x": e, "y": f, "fill": m.group(4) or "#000000"})
    return uses

def ink(u):
    """ink box of one placed glyph in page coords (x0, x1, top, bottom)"""
    bb = glyph_bbox.get(u["g"])
    if not bb:
        return None
    s = u.get("scale", 1) * u["size"]
    return (u["x"] + bb[0] * s, u["x"] + bb[1] * s, u["y"] - bb[3] * s, u["y"] - bb[2] * s)

def group_ink(us):
    boxes = [b for b in (ink(u) for u in us) if b]
    return (min(b[0] for b in boxes), max(b[1] for b in boxes),
            min(b[2] for b in boxes), max(b[3] for b in boxes))

def line_uses(uses, L):
    return [u for u in uses if abs(u["y"] - L["y"]) < 0.6 and abs(u["size"] - L["size"]) < 0.2
            and L["x"] - 0.6 <= u["x"] <= L["x_end"] + 0.6]

def shift(us, dx=0, dy=0):
    for u in us:
        u["x"] += dx; u["y"] += dy

def retrack(us, delta):
    """remove `delta` pt after every glyph, keeping the ink centre where it was"""
    c0 = sum(group_ink(us)[:2]) / 2
    for i, u in enumerate(sorted(us, key=lambda u: u["x"])):
        u["x"] -= i * delta
    c1 = sum(group_ink(us)[:2]) / 2
    shift(us, c0 - c1)

def use_svg(u):
    s = u["size"] * u.get("scale", 1)
    return (f'<use href="#{u["g"]}" transform="matrix({s:.4f},0,0,{-s:.4f},{u["x"]:.3f},{u["y"]:.3f})" '
            f'fill="{u["fill"]}"/>')

# Crimson Text metrics for live text (cap height ratio from the font file)
from fontTools.ttLib import TTFont
_ct = TTFont(os.path.join(paths.FONTS, "crimson-text-latin-400-italic.woff2"))
CAP = _ct["OS/2"].sCapHeight / _ct["head"].unitsPerEm if getattr(_ct["OS/2"], "sCapHeight", 0) else 0.59

def live_text(lines, cx, y0, pitch, size, fill, weight, style, track_em):
    ls = track_em * size
    out = []
    for i, t in enumerate(lines):
        out.append(f'<text x="{cx + ls/2:.3f}" y="{y0 + i*pitch:.3f}" text-anchor="middle" '
                   f'font-family="Crimson Text" font-weight="{weight}" font-style="{style}" '
                   f'font-size="{size}" letter-spacing="{ls:.3f}" fill="{fill}">{html.escape(t)}</text>')
    return out

# ---------------- page builder ----------------
checklist = []
pages_svg = []
pages_text = []        # plain text for screen readers / search

for P in model:
    n = P["n"]
    uses = load_svg(n)
    body = []
    fill = (P.get("fills") or ["#ffffff"])[-1]
    body.append(f'<rect width="810" height="1440" fill="{fill}"/>')
    import xml.etree.ElementTree as ET
    XL = '{http://www.w3.org/1999/xlink}href'
    order = []
    def walk(el, tf):
        tag = el.tag.split('}')[1]
        if tag in ('defs', 'mask', 'clipPath', 'symbol'):
            return
        t = tf + ([el.get('transform')] if el.get('transform') else [])
        if tag == 'image' or (tag == 'use' and el.get(XL, '').startswith('#image')):
            order.append(('img', None))
        elif tag == 'path' and el.get('fill') and el.get('fill-opacity') != '0' and 'H1080V1920' not in el.get('d', ''):
            order.append(('path', f'<path transform="{" ".join(t)}" d="{el.get("d")}" fill="{el.get("fill")}"'
                                  + (f' fill-rule="{el.get("fill-rule")}"' if el.get("fill-rule") else '') + '/>'))
        for c in el:
            walk(c, t)
    walk(ET.parse(f"{S}/svgsrc/p{n}.svg").getroot(), [])
    i = 0
    for kind, val in order:
        if kind == 'path':
            body.append(val); continue
        im = P["images"][i]; a, b, c, d, e, f = im["m"]
        eager = MODE == "test" or n <= 2
        attr = f'href="images/{im["file"]}"' if eager else f'data-src="images/{im["file"]}"'
        op = OPAC[str(n)][i]
        opa = "" if op == 1 else f' opacity="{op}"'
        body.append(f'<image {attr}{opa} width="1" height="1" preserveAspectRatio="none" '
                    f'transform="matrix({a},{b},{c},{d},{e},{f})"/>')
        i += 1
    assert i == len(P["images"]), (n, i)

    lines = P["lines"]
    text_uses = []      # final glyph uses for the page
    extra = []          # live text elements
    plain = []

    if n == 2:
        hindi = [u for u in uses if abs(u["y"] - 332.407) < 0.5]
        retrack(hindi, HINDI_TRACK_CUT)
        text_uses += hindi
        plain.append("॥ श्री गणेशाय नमः ॥")
        for L in lines:
            lu = line_uses(uses, L)
            if L["font"].startswith(("Type3", "NotoSans")):
                continue
            if L["font"] == "Amoresa":
                adv = L["x_end"] - L["x"]
                retrack(lu, NAME_SHRINK * adv / (len(L["text"]) - 1))
                text_uses += lu
            elif "lorem" in L["text"]:
                continue   # replaced below
            else:
                text_uses += lu
        # parent lines: same baselines, size, colour, tracking; centred on the original lines
        def block(key, l1, l2):
            L1 = next(L for L in lines if L["text"].startswith(l1))
            L2 = next(L for L in lines if L["text"].startswith(l2))
            cx = sum((group_ink(line_uses(uses, L))[0] + group_ink(line_uses(uses, L))[1]) / 2 for L in (L1, L2)) / 2
            return live_text(PARENTS[key], cx, L1["y"], L2["y"] - L1["y"], L1["size"], L1["color"],
                             600, "normal", L1["track"] / L1["size"])
        extra += block("soumya", "Daughter of", "Mr lorem")
        extra += block("madhur", "Son of", "Mr. lorem")
        plain += ["With the blessings of Lord Ganesha and our beloved elders, we invite you to the wedding festivities of",
                  "Soumya Gupta", " ".join(PARENTS["soumya"]), "&", "Madhur Gupta", " ".join(PARENTS["madhur"])]
        checklist.append(("2", "Parent names", f"Replaced with “{' '.join(PARENTS['soumya'])}” and “{' '.join(PARENTS['madhur'])}”; same size (28 pt), colour, weight, line breaks and centring"))
        checklist.append(("2", "Script names spacing", f"“Soumya Gupta” and “Madhur Gupta” tightened so each line is {int(NAME_SHRINK*100)}% narrower; centre unchanged"))
        checklist.append(("2", "Hindi line spacing", f"Added tracking of {HINDI_TRACK_CUT} pt per glyph removed from “॥ श्री गणेशाय नमः ॥”; centre unchanged"))

    elif 3 <= n <= 7:
        venue = [L for L in lines if L["font"] == "Crimson-SemiboldItalic"]
        title = [L for L in lines if L["font"] in ("Alta_regular", "Amoresa")]
        date = next(L for L in lines if L["text"].strip().endswith("2026,"))
        others = [L for L in lines if L not in venue and L not in title]
        for L in others:
            text_uses += line_uses(uses, L)
        date_top = group_ink(line_uses(uses, date))[2]
        tuses = {L["text"]: line_uses(uses, L) for L in title}
        P["_title_uses"], P["_date_top"] = tuses, date_top
        P["_venue"], P["_text_uses"] = venue, text_uses
        P["_uses"] = uses
        plain_title = " ".join(L["text"].strip() for L in title)
        P["_plain"] = [plain_title] + [L["text"].strip() for L in others] + [" ".join(L["text"].strip() for L in venue)]

    else:
        for L in lines:
            text_uses += line_uses(uses, L)
        if n == 8:
            plain.append(" ".join(L["text"].strip() for L in lines))

    P["_body"], P["_extra"], P["_plain_list"] = body, extra, plain
    if n not in range(3, 8):
        P["_text_uses"] = text_uses

# ---------- event pages: shared title gap, titles, venue ----------
# reference gap = the gap already used on Engagement (p4) and Baraat (p6)
def title_bottom(us):
    return group_ink([u for u in us if u["t"].strip()])[3]
gaps = {}
for P in model[2:7]:
    allu = [u for us in P["_title_uses"].values() for u in us]
    gaps[P["n"]] = P["_date_top"] - title_bottom(allu)
GAP = round((gaps[4] + gaps[6]) / 2, 2)
print("ink gaps before:", {k: round(v, 2) for k, v in gaps.items()}, "-> target", GAP)

def split_title(P, first, second_line, amp_src):
    """first line as-is; small '&'; second word; stacked, centred, bottom GAP above the date"""
    tu = P["_title_uses"]
    l1 = [dict(u) for u in tu[first] if u["t"].strip()]
    src = [dict(u) for u in tu[second_line] if u["t"].strip()]
    amp = [u for u in src if u["t"] == "&"]
    w2 = [u for u in src if u["t"] != "&"]
    for u in amp:
        u["scale"] = SMALL_AMP
    i1 = group_ink(l1)
    cx = (i1[0] + i1[1]) / 2
    cap = i1[3] - i1[2]
    pitch = abs(P["_orig_pitch"])
    g0 = pitch - cap                         # original space between stacked title lines
    # vertical: line1 baseline b1, amp, word2 baseline b3
    ia = group_ink(amp); amp_h = ia[3] - ia[2]
    b3_target = P["_date_top"] - GAP
    i2 = group_ink(w2)
    shift(w2, cx - (i2[0] + i2[1]) / 2, b3_target - i2[3])
    amp_bottom = group_ink(w2)[2] - g0
    ia = group_ink(amp)
    shift(amp, cx - (ia[0] + ia[1]) / 2, amp_bottom - ia[3])
    l1_bottom = group_ink(amp)[2] - g0
    shift(l1, 0, l1_bottom - i1[3])
    return l1 + amp + w2

for P in model[2:7]:
    n = P["n"]
    tu = P["_title_uses"]
    keys = list(tu)
    if n == 4:
        P["_orig_pitch"] = tu[keys[1]][0]["y"] - tu[keys[0]][0]["y"]
        new = split_title(P, "Engagement", "& Sangeet ", "&")
        P["_plain"][0] = "Engagement & Sangeet"
        checklist.append(("4", "Title", "Now “ENGAGEMENT” / small “&” (half size) / “SANGEET” on three lines; “CEREMONY” removed; same title font, colour and centre"))
    elif n == 5:
        P["_orig_pitch"] = tu[keys[1]][0]["y"] - tu[keys[0]][0]["y"]
        new = split_title(P, "Haldi", "& Mehendi", "&")
        P["_plain"][0] = "Haldi & Mehendi"
        checklist.append(("5", "Title", "Now “HALDI” / small “&” (half size) / “MEHENDI” on three lines; same title font, colour and centre"))
    else:
        new = [dict(u) for us in tu.values() for u in us]
        shift(new, 0, P["_date_top"] - GAP - title_bottom(new))
    for u in new: u["title"] = True
    P["_text_uses"] = P["_text_uses"] + new

    # venue: regular italic, smaller; same colour, tracking ratio, line breaks, centre; top of ink kept
    V = P["_venue"]
    v_ink = [group_ink(line_uses(P["_uses"], L)) for L in V]
    cx = sum((b[0] + b[1]) / 2 for b in v_ink) / len(v_ink)
    old = V[0]["size"]
    pitch = (V[1]["y"] - V[0]["y"]) * VENUE_SIZE / old if len(V) > 1 else 0
    y0 = V[0]["y"] - CAP * (old - VENUE_SIZE)
    P["_extra"] += live_text([L["text"].strip() for L in V], cx, y0, pitch, VENUE_SIZE, V[0]["color"],
                             400, "italic", V[0]["track"] / old)
    last_base = y0 + pitch * (len(V) - 1)
    url = MAPS["havana"] if "Havana" in V[0]["text"] else MAPS["royal"]
    col = V[0]["color"]
    bw, bh, by = 250, 54, last_base + 40
    if n == 7:   # Jaimala: the peacock's neck sits under the centre, so the button sits in the clear sky beside it
        bw, cx = 214, 487
    if True:
      P["_extra"].append(
        f'<a class="dir" href="{url}" target="_blank" rel="noopener" aria-label="Directions to {html.escape(V[0]["text"].split(",")[0])}">'
        f'<rect x="{cx-bw/2:.2f}" y="{by:.2f}" width="{bw}" height="{bh}" rx="27" fill="none" stroke="{col}" stroke-width="1.6"/>'
        f'<rect class="dir-hit" x="{cx-bw/2:.2f}" y="{by:.2f}" width="{bw}" height="{bh}" rx="27" fill="{col}" fill-opacity="0"/>'
        f'<text x="{cx+1.2:.2f}" y="{by+bh/2+7:.2f}" text-anchor="middle" font-family="Crimson Text" font-weight="600" '
        f'font-size="21" letter-spacing="2.4" fill="{col}">GET DIRECTIONS</text></a>')

checklist.append(("3–7", "Venue address", f"Bold removed (Crimson semibold italic → regular italic) and size 34.5 pt → {VENUE_SIZE:g} pt on all five event pages; colour, line breaks and centring kept"))
checklist.append(("3–7", "Title-to-date gap", f"Every event page now has the same {GAP:.1f} pt gap from the bottom of the title to the top of the date (before: " + ", ".join(f"p{k} {v:.1f}" for k, v in gaps.items()) + " pt)"))

# ---------- page 1: "Soumya & Madhur" under the monogram, styled like page 2 ----------
from PIL import Image as _Im
p2 = model[1]
p2_uses = [u for u in p2["_text_uses"]]
def word_from(line_text, word):
    L = next(L for L in p2["lines"] if L["text"] == line_text)
    us = sorted([u for u in p2_uses if abs(u["y"] - L["y"]) < 0.6 and u["size"] > 60], key=lambda u: u["x"])
    i = next(k for k in range(len(us)) if "".join(v["t"] for v in us[k:k+len(word)]) == word)
    return [dict(u) for u in us[i:i+len(word)]], us
soumya, s_line = word_from("Soumya Gupta", "Soumya")
madhur, _ = word_from("Madhur Gupta", "Madhur")
gupta = [u for u in s_line if u not in soumya and u["t"].strip()]
word_gap = group_ink(gupta)[0] - group_ink(soumya)[1]          # space between names on page 2
amp = [dict(u) for u in p2_uses if u["t"] == "&" and abs(u["size"] - 38.64) < 0.1]
COVER_SCALE = 0.7          # names on the cover at 70% of the page-2 size
COVER_GAP = 14             # pt below the monogram
for grp in (soumya, madhur, amp):
    x0 = grp[0]["x"]
    for u in grp:
        u["x"] = x0 + (u["x"] - x0) * COVER_SCALE
        u["scale"] = COVER_SCALE
word_gap *= COVER_SCALE
# monogram ink bottom (from the image's own transparency)
mono = model[0]["images"][1]
alpha_bb = _Im.open(f"{SITE}/images/{mono['file']}").getchannel("A").getbbox()
a, b, c, d, e, f = mono["m"]
mono_bottom = f + d * alpha_bb[3] / mono["h"]
# vertical gap: same as page 2 between the intro text and "Soumya Gupta"
intro = next(L for L in p2["lines"] if L["text"].startswith("festivities"))
intro_bottom = group_ink(line_uses(load_svg(2), intro))[3]
gap_v = COVER_GAP
# lay out on one line: Soumya  &  Madhur, centred under the monogram
baseline_shift = (mono_bottom + gap_v) - group_ink(soumya + madhur)[2]
shift(soumya, 0, baseline_shift)
shift(madhur, 0, soumya[0]["y"] - madhur[0]["y"])
shift(amp, 0, soumya[0]["y"] - amp[0]["y"])
x = 0
for grp in (soumya, amp, madhur):
    ib = group_ink(grp); shift(grp, x - ib[0]); x = group_ink(grp)[1] + word_gap
allg = soumya + amp + madhur
mono_cx = e + a / 2
ib = group_ink(allg); shift(allg, mono_cx - (ib[0] + ib[1]) / 2)
model[0]["_text_uses"] = model[0]["_text_uses"] + allg
model[0]["_plain_list"] = ["Soumya & Madhur"]
model[0]["_extra"].append(
    f'<a class="open" href="#page-2" aria-label="Open the invitation">'
    f'<text x="{mono_cx:.2f}" y="{group_ink(allg)[3] + 46:.2f}" text-anchor="middle" font-family="Crimson Text" '
    f'font-style="italic" font-size="25" letter-spacing="1.2" fill="#784646">Tap to open</text></a>')
print("page1 names: monogram bottom", round(mono_bottom, 1), "gap", round(gap_v, 1), "ink box", [round(v, 1) for v in group_ink(allg)])
checklist.append(("1", "Names on cover", f"“Soumya & Madhur” added below the monogram in the same lettering as the names on page 2 (script names, 63 pt, #784646; italic “&”, #b85c1d), centred under the monogram, {gap_v:.0f} pt below it (the same gap as above the names on page 2)"))

# ---------- website sections between the cards (card fonts, colours, divider) ----------
ORN = "images/" + model[2]["images"][1]["file"]
DIV = f'<div class="divider" aria-hidden="true"><span></span><img src="{ORN}" alt=""><span></span></div>'
CORNERS = "".join(f'<img class="corner {c}" src="{ORN}" alt="" aria-hidden="true">' for c in ("tl", "tr", "bl", "br"))
def ev(name, time):
    return f'<li><span class="n">{name}</span><span class="t">{time}</span></li>'
bride = [("Grandparents", ["Late Smt. Mannu Devi Gupta & Shri Nathuram Gupta", "Smt. Shashi Gupta & Shri Amarnath Gupta"]),
         ("Parents", ["Smt. Rashmi Gupta & Shri Umakant Gupta"]),
         ("Tauji & Tayji", ["Late Smt. Vimla Devi Gupta & Dr. P. D. Gupta", "Smt. Usha Gupta & Shri Ramakant Gupta"]),
         ("Bua & Fufa Ji", ["Smt. Susheela Gupta & Shri Ramprakash Gupta", "Smt. Malti Gupta & Late Shri Santosh Kumar Gupta"]),
         ("Mausi & Mausa", ["Smt. Ruchi Gupta & Shri Sanjay Gupta", "Smt. Rati Gupta & Shri Amit Gupta"]),
         ("Brothers & Sisters", ["Ramdevi • Annu • Vedprakash • Satya Prakash • Harishchandra • Gyandevi • Gyan Chand • Gyan Bharti • Anurag Gupta • Ashish Gupta",
                                 "Saurav • Achin • Simran • Arnav • Sameeksha • Netra • Anmol • Yashita"])]
groom = [("Nana Ji & Nani Ji", ["Late Shri Seetaram Gupta & Smt. Rukmani Gupta"]),
         ("Fufa Ji & Bua Ji", ["Shri Narayan Das Gupta & Smt. Uma Gupta", "Late Shri Udit Narayan Gupta & Smt. Kamlesh Gupta", "Shri Rakesh Gupta & Smt. Jayanti Gupta"]),
         ("Didi & Jiju", ["Geeta & Dinesh Gupta", "Shivani & Ashish Gupta"]),
         ("Mausi & Mausa Ji", ["Vandana & Ashok Nayak", "Archana & Ajay Gupta", "Shivani & Yogesh Gupta"]),
         ("Mama & Mami", ["Amit Gupta & Deepti Gupta", "Ankit Gupta & Noopur Gupta"])]
def side(title, rows, cls):
    out = f'<div class="side {cls}"><h3 class="band">{title}</h3><dl>'
    for k, vs in rows:
        out += f'<div class="rel"><dt>{html.escape(k)}</dt>' + "".join(f'<dd>{html.escape(v)}</dd>' for v in vs) + '</div>'
    return out + '</dl></div>'
GUEST_OPTS = "".join(f'<option value="{i}">{i}</option>' for i in range(1, 21))
def evcheck(i, val, label, date):
    return (f'<label class="chip" for="ev-{i}"><input id="ev-{i}" type="checkbox" name="events" value="{val}" checked>'
            f'<span class="box" aria-hidden="true"></span><span class="lbl">{label}</span><span class="dt">{date}</span></label>')
EXTRA_SECTIONS = f"""
<section class="web theme-night" id="venues" aria-labelledby="venues-h"><canvas class="petals" data-n="7" aria-hidden="true"></canvas><div class="col"><div class="frame">{CORNERS}
  <p class="label">Where we celebrate</p>
  <h2 id="venues-h">Two Days, Two Venues</h2>
  <div class="count" id="countdown" aria-live="off">
    <div><b data-u="d">–</b><span>Days</span></div><div><b data-u="h">–</b><span>Hours</span></div>
    <div><b data-u="m">–</b><span>Mins</span></div><div><b data-u="s">–</b><span>Secs</span></div>
  </div>
  <p class="count-note">until the Tilak, 24 November 2026</p>
  {DIV}
  <article class="tile">
    <p class="band">Day 1 &middot; Tuesday, 24 November</p>
    <div class="tile-body">
      <h3>Havana Restro</h3>
      <p class="addr">Opposite Bus Stand, Kanpur Road, Cantt, Jhansi</p>
      <ul class="events">{ev("Tilak", "4:30 PM")}{ev("Engagement &amp; Sangeet", "7:00 PM")}</ul>
      <a class="btn" href="{MAPS['havana']}" target="_blank" rel="noopener">Get Directions</a>
    </div>
  </article>
  <article class="tile">
    <p class="band">Day 2 &middot; Wednesday, 25 November</p>
    <div class="tile-body">
      <h3>The Royal Resort Orchha</h3>
      <p class="addr">Tigela, Orchha</p>
      <ul class="events">{ev("Haldi &amp; Mehendi", "11:30 AM")}{ev("Baraat", "7:00 PM")}{ev("Jaimala", "9:00 PM")}</ul>
      <a class="btn" href="{MAPS['royal']}" target="_blank" rel="noopener">Get Directions</a>
    </div>
  </article>
</div></div></section>
<section class="web theme-rose" id="rsvp" aria-labelledby="rsvp-h"><canvas class="petals" data-n="6" aria-hidden="true"></canvas><div class="col"><div class="frame">{CORNERS}
  <p class="label">Kindly reply</p>
  <h2 id="rsvp-h">RSVP</h2>
  <p class="lead">We would love to know if you can join us.</p>
  {DIV}
  <form id="rsvp-form" novalidate>
    <div class="f"><label for="rsvp-name">Your name</label>
      <input id="rsvp-name" name="name" type="text" autocomplete="name" placeholder="Full name" required></div>
    <div class="f"><label for="rsvp-phone">Mobile number</label>
      <input id="rsvp-phone" name="phone" type="tel" autocomplete="tel" inputmode="tel" placeholder="10-digit mobile" required></div>
    <fieldset class="f"><legend>Will you join us?</legend>
      <div class="choices">
        <label class="pill"><input id="rsvp-yes" type="radio" name="attending" value="Joyfully attending" required><span>Joyfully attending</span></label>
        <label class="pill"><input id="rsvp-no" type="radio" name="attending" value="Regretfully unable"><span>Regretfully unable</span></label>
      </div></fieldset>
    <div id="rsvp-more">
      <div class="f"><label for="rsvp-guests">Number of guests, including you</label>
        <select id="rsvp-guests" name="guests">{GUEST_OPTS}</select></div>
      <fieldset class="f"><legend>Which events will you attend?</legend>
        <div class="checks">
          {evcheck("tilak", "Tilak", "Tilak", "24 Nov")}
          {evcheck("sangeet", "Engagement &amp; Sangeet", "Engagement &amp; Sangeet", "24 Nov")}
          {evcheck("haldi", "Haldi &amp; Mehendi", "Haldi &amp; Mehendi", "25 Nov")}
          {evcheck("baraat", "Baraat", "Baraat", "25 Nov")}
          {evcheck("jaimala", "Jaimala", "Jaimala", "25 Nov")}
        </div></fieldset>
    </div>
    <div class="f"><label for="rsvp-msg">A message for Soumya &amp; Madhur <small>(optional)</small></label>
      <textarea id="rsvp-msg" name="message" rows="3" placeholder="Your wishes and blessings"></textarea></div>
    <p class="err" id="rsvp-err" role="alert" hidden></p>
    <button class="btn wide" type="submit" id="rsvp-send">Send RSVP</button>
  </form>
  <div id="rsvp-done" class="done" hidden tabindex="-1">
    <h3>Thank you!</h3>
    <p class="lead" id="rsvp-done-msg"></p>
  </div>
</div></div></section>
<section class="web theme-marigold" id="blessings" aria-labelledby="bless-h"><canvas class="petals" data-n="9" aria-hidden="true"></canvas><div class="col"><div class="frame">{CORNERS}
  <div class="hosts-box">
    <p class="label">Lovingly invited by</p>
    <p class="hosts">Umakant Gupta<span>&amp;</span>Santosh Gupta</p>
    <p class="lead">With love, the Gupta families, eagerly awaiting the pleasure of your presence and blessings.</p>
  </div>
  {DIV}
  <h2 id="bless-h">With Blessings Of</h2>
  <p class="label">The Bride’s Family</p>
  <div class="sides">{side("Bride’s Side", bride, "bride")}</div>
</div></div></section>
<section class="web theme-night" id="blessings-groom" aria-labelledby="bless-g-h"><canvas class="petals" data-n="8" aria-hidden="true"></canvas><div class="col"><div class="frame">{CORNERS}
  <p class="label">With blessings of</p>
  <h2 id="bless-g-h">The Groom’s Family</h2>
  {DIV}
  <div class="sides">{side("Groom’s Side", groom, "groom")}</div>
</div></div></section>
"""

# ---------- assemble ----------
used_glyphs = set()
sections = []
for P in model:
    tu = P["_text_uses"]
    used_glyphs.update(u["g"] for u in tu)
    plain = P.get("_plain") or P["_plain_list"]
    label = {1: "Cover", 2: "Families", 8: "Closing"}.get(P["n"], "Event")
    svg = (f'<svg class="pg" viewBox="0 0 810 1440" role="img" aria-label="{html.escape(" ".join(plain) or "Soumya and Madhur monogram")}">'
           + "".join(P["_body"])
           + '<g class="rv rv1">' + "".join(use_svg(u) for u in tu if u.get("title") or (P["n"] in (1, 2) and u.get("scale", 1) * u["size"] > 40)) + '</g>'
           + '<g class="rv rv2">' + "".join(use_svg(u) for u in tu if not (u.get("title") or (P["n"] in (1, 2) and u.get("scale", 1) * u["size"] > 40))) + '</g>'
           + '<g class="rv rv3">' + "".join(P["_extra"]) + '</g>'
           + ('<canvas class="petals" aria-hidden="true"></canvas>' if False else '')
           + "</svg>")
    if P["n"] == 8:
        sections.append(EXTRA_SECTIONS)
    petals = '<canvas class="petals" aria-hidden="true"></canvas>'
    sections.append(f'<section class="page" id="page-{P["n"]}" data-label="{label}">{svg}{petals}</section>')

defs = "".join(f'<path id="{g}" d="{glyph_defs[g]}"/>' for g in sorted(used_glyphs) if glyph_defs.get(g))

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Soumya & Madhur</title>
<meta name="description" content="You are invited to the wedding of Soumya & Madhur.">
<meta name="theme-color" content="#fdf5ef">
<script>document.documentElement.className += " js locked";/* always start from the envelope: no restored scroll position, no #section jump */try {{ if ("scrollRestoration" in history) history.scrollRestoration = "manual"; }} catch (e) {{}}if (location.hash) {{ try {{ history.replaceState(null, "", location.href.split("#")[0]); }} catch (e) {{}} }}window.scrollTo(0, 0);function top0() {{ window.scrollTo(0, 0); }} addEventListener("DOMContentLoaded", top0); addEventListener("load", function () {{ top0(); setTimeout(top0, 0); }});addEventListener("pageshow", function (e) {{ if (e.persisted) location.reload(); }});</script>
<meta property="og:type" content="website">
<meta property="og:title" content="Soumya & Madhur \u2022 24\u201325 November 2026">
<meta property="og:description" content="You are invited to the wedding of Soumya & Madhur. Jhansi &amp; Orchha.">
<meta property="og:image" content="https://soumyamadhurweddinginvitation.vercel.app/og-cover.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<style>
@font-face {{ font-family: "Crimson Text"; font-style: normal; font-weight: 600; font-display: block;
  src: url("fonts/crimson-text-latin-600-normal.woff2") format("woff2"); }}
@font-face {{ font-family: "Crimson Text"; font-style: italic; font-weight: 400; font-display: block;
  src: url("fonts/crimson-text-latin-400-italic.woff2") format("woff2"); }}
@font-face {{ font-family: "Crimson Text"; font-style: normal; font-weight: 400; font-display: block;
  src: url("fonts/crimson-text-latin-400-normal.woff2") format("woff2"); }}
:root {{ color-scheme: light; }}
html, body {{ margin: 0; padding: 0; background: #fdf5ef; }}
html {{ scroll-snap-type: y proximity; scroll-behavior: smooth; }}
@media (prefers-reduced-motion: reduce) {{ html {{ scroll-behavior: auto; }} .open text {{ animation: none !important; }} }}
.page {{ height: 100vh; height: 100svh; display: grid; place-items: center; scroll-snap-align: start; overflow: hidden; }}
.pg {{ display: block; height: min(100svh, calc(100vw * 16 / 9)); width: auto; aspect-ratio: 9 / 16; }}
@media (max-aspect-ratio: 9/16) {{ .page {{ height: calc(100vw * 16 / 9); }} }}
/* ---------- animation ---------- */
.page {{ position: relative; }}
.petals {{ position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; z-index: 2; }}
.js .page .rv {{ opacity: 0; transform: translateY(14px); transform-box: fill-box; }}
.js .page.seen .rv {{ animation: rise 1s cubic-bezier(.2,.7,.2,1) forwards; }}
.js .page.seen .rv2 {{ animation-delay: .35s; }}
.js .page.seen .rv3 {{ animation-delay: .6s; }}
.js .web .frame > *:not(.corner) {{ opacity: 0; transform: translateY(16px); }}
.js .web.seen .frame > *:not(.corner) {{ animation: rise .9s cubic-bezier(.2,.7,.2,1) forwards; }}
.js .web.seen .frame > *:nth-child(6) {{ animation-delay: .1s; }}
.js .web.seen .frame > *:nth-child(7) {{ animation-delay: .2s; }}
.js .web.seen .frame > *:nth-child(n+8) {{ animation-delay: .3s; }}
@keyframes rise {{ to {{ opacity: 1; transform: none; }} }}
/* envelope intro */
.intro {{ position: fixed; inset: 0; z-index: 50; display: none; place-items: center; align-content: center; gap: 22px;
  background: radial-gradient(120% 80% at 50% 40%, #fdf5ef 0%, #f3e2d2 100%); }}
.js .intro {{ display: grid; }}
.intro.gone {{ opacity: 0; visibility: hidden; transition: opacity .6s ease, visibility .6s; }}
.env {{ position: relative; width: min(78vw, 400px); aspect-ratio: 7 / 5; perspective: 1600px; }}
.env > * {{ will-change: transform, opacity; backface-visibility: hidden; }}
.intro {{ will-change: opacity; }}
.env-back {{ position: absolute; inset: 0; z-index: 0; background: #ead2bd; border-radius: 6px; box-shadow: 0 18px 40px rgba(120,70,70,.18); }}
.env-letter {{ position: absolute; left: 6%; right: 6%; top: 6%; height: 88%; background: #fdf5ef; border-radius: 3px; z-index: 1;
  display: grid; place-items: center; align-content: center; gap: 4%; box-shadow: 0 2px 8px rgba(120,70,70,.12); }}
.env-letter img {{ width: 52%; height: auto; }}
.env-letter span {{ font-family: "Crimson Text", Georgia, serif; font-style: italic; color: #784646; font-size: clamp(14px, 4.4vw, 22px); letter-spacing: .04em; }}
.env-front {{ position: absolute; inset: 0; z-index: 2; border-radius: 6px; pointer-events: none; background: #f2dfcd;
  clip-path: polygon(0 0, 50% 56%, 100% 0, 100% 100%, 0 100%); }}
.env-flap {{ position: absolute; left: 0; right: 0; top: 0; height: 60%; z-index: 3; transform-origin: 50% 0;
  background: #ecd5c0; clip-path: polygon(0 0, 100% 0, 50% 100%); }}
.seal {{ position: absolute; left: 50%; top: 60%; z-index: 4; width: 21%; aspect-ratio: 1; transform: translate(-50%, -50%);
  border: 0; border-radius: 50%; cursor: pointer; padding: 0;
  background: radial-gradient(circle at 38% 32%, #d47a3d 0%, #b85c1d 45%, #8e4313 100%);
  box-shadow: 0 3px 8px rgba(90,40,20,.35), inset 0 0 0 3px rgba(255,220,180,.25);
  animation: pulse 2.2s ease-in-out infinite; }}
.seal img {{ width: 46%; height: auto; display: block; margin: auto; filter: brightness(0) invert(1); opacity: .9; }}
.seal:focus-visible, .intro-skip:focus-visible {{ outline: 2px solid #784646; outline-offset: 4px; }}
@keyframes pulse {{ 0%, 100% {{ transform: translate(-50%, -50%) scale(1); }} 50% {{ transform: translate(-50%, -50%) scale(1.06); }} }}
.intro-hint {{ margin: 0; font-family: "Crimson Text", Georgia, serif; font-style: italic; color: #784646; font-size: 18px; letter-spacing: .04em; }}
.intro-skip {{ position: absolute; right: max(16px, env(safe-area-inset-right, 0px)); bottom: calc(16px + env(safe-area-inset-bottom, 0px));
  background: none; border: 0; color: #784646; font: italic 16px "Crimson Text", Georgia, serif; text-decoration: underline; cursor: pointer; padding: 8px; }}
.burst {{ position: fixed; inset: 0; width: 100%; height: 100%; pointer-events: none; z-index: 5; }}
html.locked {{ overflow: hidden; }}
@media (prefers-reduced-motion: reduce) {{
  .js .page .rv, .js .web .frame > * {{ opacity: 1 !important; transform: none !important; animation: none !important; }}
  .seal {{ animation: none; }}
  .env-flap, .env-letter {{ transition: none; }}
}}
/* links drawn inside the cards */
.dir, .open {{ cursor: pointer; }}
.dir:hover .dir-hit, .dir:focus-visible .dir-hit {{ fill-opacity: .12; }}
.dir:focus-visible rect:first-child {{ stroke-width: 3; }}
.open text {{ animation: breathe 2.4s ease-in-out infinite; }}
@keyframes breathe {{ 0%, 100% {{ opacity: .55; }} 50% {{ opacity: 1; }} }}
/* website sections: framed stationery panels in colours from the artwork; sized like the card pages */
.web {{ position: relative; display: flex; justify-content: center; scroll-snap-align: start; color: #784646;
  --band: #b85c1d; --band-ink: #fdf5ef; --gold: #c99a3e; --paper: #fdf5ef; }}
.web.theme-night {{ background: radial-gradient(120% 70% at 50% 0%, #1d2f5c 0%, #0b1838 55%, #060f26 100%); --band: #1d2f5c; }}
.web.theme-rose {{ background: linear-gradient(180deg, #f7d6cf 0%, #efbcb3 100%); --band: #b85c1d; }}
.web.theme-marigold {{ background: linear-gradient(180deg, #f9dfa0 0%, #f2c46a 100%); --band: #784646; }}
.web .col {{ position: relative; z-index: 1; container-type: inline-size; width: min(100vw, calc(100svh * 9 / 16)); box-sizing: border-box;
  min-height: min(100svh, calc(100vw * 16 / 9)); display: flex;
  padding: 6cqw max(4.5cqw, env(safe-area-inset-right, 0px)) 6cqw max(4.5cqw, env(safe-area-inset-left, 0px)); }}
.web .frame {{ position: relative; flex: 1; box-sizing: border-box; background: var(--paper);
  border: 2px solid var(--gold); outline: 1px solid var(--gold); outline-offset: -9px;
  box-shadow: 0 1.5cqw 5cqw rgba(60,20,10,.25);
  padding: 11cqw 7cqw 10cqw; text-align: center; font-family: "Crimson Text", Georgia, serif;
  font-size: 4.6cqw; line-height: 1.45; display: flex; flex-direction: column; gap: 3.2cqw; }}
.web .corner {{ position: absolute; width: 7cqw; height: auto; opacity: .9; }}
.web .corner.tl {{ top: 3.2cqw; left: 3.2cqw; }} .web .corner.tr {{ top: 3.2cqw; right: 3.2cqw; }}
.web .corner.bl {{ bottom: 3.2cqw; left: 3.2cqw; }} .web .corner.br {{ bottom: 3.2cqw; right: 3.2cqw; }}
.web .label {{ margin: 0; font-size: 3.7cqw; letter-spacing: .22em; text-transform: uppercase; color: #b85c1d; font-weight: 600; }}
.web h2 {{ margin: 0; font-weight: 600; font-size: 8.8cqw; line-height: 1.1; color: #784646; letter-spacing: .02em; text-wrap: balance; }}
.web h3 {{ margin: 0; font-weight: 600; font-size: 6.6cqw; line-height: 1.15; color: #784646; }}
.web .lead {{ margin: 0 auto; max-width: 30em; font-style: italic; font-size: 4.6cqw; text-wrap: balance; }}
.web .divider {{ display: flex; align-items: center; gap: 3cqw; margin: 1.5cqw 0; }}
.web .divider span {{ flex: 1; height: 1px; background: linear-gradient(90deg, transparent, var(--gold), transparent); }}
.web .divider img {{ width: 6cqw; height: auto; }}
.web .btn {{ display: inline-block; align-self: center; padding: 3cqw 8cqw; border-radius: 999px; border: 0; cursor: pointer;
  background: #b85c1d; color: #fdf5ef; text-decoration: none; font: 600 4.2cqw/1 "Crimson Text", Georgia, serif; letter-spacing: .12em;
  text-transform: uppercase; box-shadow: 0 1cqw 2.4cqw rgba(184,92,29,.3); }}
.web .btn:hover {{ background: #9e4c15; }}
.web .btn:focus-visible {{ outline: 3px solid #784646; outline-offset: 3px; }}
.web .btn.wide {{ align-self: stretch; padding: 4cqw; font-size: 4.6cqw; }}
/* countdown */
.web .count {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 2.4cqw; margin-top: 1cqw; }}
.web .count div {{ display: grid; gap: .6cqw; padding: 2.6cqw 0; border-radius: 2.5cqw; background: #1d2f5c; color: #f7d77a;
  box-shadow: inset 0 0 0 1px rgba(247,215,122,.45); }}
.web .count b {{ font-weight: 600; font-size: 8.4cqw; line-height: 1; font-variant-numeric: tabular-nums; }}
.web .count span {{ font-size: 3.2cqw; letter-spacing: .16em; text-transform: uppercase; color: #fdf5ef; }}
.web .count-note {{ margin: 0; font-style: italic; font-size: 4.2cqw; }}
/* venue tiles */
.web .tile {{ border: 1.5px solid var(--gold); border-radius: 3cqw; overflow: hidden; background: #fffaf4; text-align: center; }}
.web .band {{ margin: 0; padding: 2.6cqw 3cqw; background: var(--band); color: var(--band-ink); font-weight: 600;
  font-size: 4.2cqw; letter-spacing: .1em; text-transform: uppercase; }}
.web .tile-body {{ display: flex; flex-direction: column; gap: 2.4cqw; padding: 5cqw 5cqw 6cqw; }}
.web .addr {{ margin: 0; font-style: italic; font-size: 4.4cqw; }}
.web .events {{ list-style: none; margin: 1cqw 0; padding: 0; display: grid; gap: 2cqw; text-align: left; }}
.web .events li {{ display: flex; align-items: center; justify-content: space-between; gap: 3cqw; padding: 2.8cqw 3.6cqw;
  border-radius: 2cqw; background: #fbeee3; border-left: 1.2cqw solid #b85c1d; }}
.web .events .n {{ font-weight: 600; font-size: 4.8cqw; min-width: 0; }}
.web .events .t {{ flex: none; font-size: 4.2cqw; color: #b85c1d; font-weight: 600; font-variant-numeric: tabular-nums; white-space: nowrap; }}
/* RSVP form */
.web form {{ display: flex; flex-direction: column; gap: 5cqw; text-align: left; }}
.web .f {{ display: grid; gap: 2cqw; border: 0; padding: 0; margin: 0; min-width: 0; }}
.web .f label, .web legend {{ font-size: 4cqw; font-weight: 600; letter-spacing: .06em; color: #784646; padding: 0; }}
.web .f small {{ font-weight: 400; font-style: italic; letter-spacing: 0; }}
.web input[type=text], .web input[type=tel], .web textarea, .web select {{
  font: inherit; font-size: max(16px, 4.6cqw); color: #4f2c2c; background: #fff; box-sizing: border-box; width: 100%;
  border: 1.5px solid #e2c3b3; border-radius: 2.4cqw; padding: 3cqw 3.6cqw; }}
.web select {{ width: 40%; appearance: none; -webkit-appearance: none; cursor: pointer;
  background: #fff linear-gradient(45deg, transparent 50%, #b85c1d 50%) right 5.4cqw center / 1.6cqw 1.6cqw no-repeat,
              linear-gradient(-45deg, transparent 50%, #b85c1d 50%) right 3.8cqw center / 1.6cqw 1.6cqw no-repeat; }}
.web ::placeholder {{ color: #b9998c; font-style: italic; }}
.web input:focus, .web textarea:focus, .web select:focus {{ outline: none; border-color: #b85c1d; box-shadow: 0 0 0 3px rgba(184,92,29,.18); }}
.web textarea {{ resize: vertical; min-height: 24cqw; }}
.web .choices {{ display: grid; grid-template-columns: 1fr 1fr; gap: 2.6cqw; }}
.web .pill {{ position: relative; display: block; }}
.web .pill input {{ position: absolute; opacity: 0; inset: 0; margin: 0; cursor: pointer; }}
.web .pill span {{ display: grid; place-items: center; min-height: 13cqw; padding: 2cqw; text-align: center; box-sizing: border-box;
  border: 1.5px solid #e2c3b3; border-radius: 2.4cqw; background: #fff; font-size: 4.3cqw; font-weight: 600; letter-spacing: 0; color: #784646; }}
.web .pill input:checked + span {{ background: #784646; border-color: #784646; color: #fdf5ef; }}
.web .pill input:focus-visible + span {{ outline: 3px solid #b85c1d; outline-offset: 2px; }}
.web .checks {{ display: grid; gap: 2.2cqw; }}
.web .f .chip {{ position: relative; display: flex !important; align-items: center; gap: 3cqw; padding: 3cqw 3.6cqw; cursor: pointer;
  border: 1.5px solid #e2c3b3; border-radius: 2.4cqw; background: #fff; letter-spacing: 0 !important; }}
.web .chip input {{ position: absolute; opacity: 0; width: 1px; height: 1px; }}
.web .chip .box {{ flex: none; width: 5.6cqw; height: 5.6cqw; border-radius: 1.2cqw; border: 1.5px solid #b85c1d; display: grid; place-items: center; background: #fff; }}
.web .chip input:checked ~ .box {{ background: #b85c1d; }}
.web .chip input:checked ~ .box::after {{ content: ""; width: 1.6cqw; height: 3cqw; border: solid #fff; border-width: 0 .7cqw .7cqw 0; transform: translateY(-.3cqw) rotate(45deg); }}
.web .chip input:checked ~ .lbl {{ color: #4f2c2c; }}
.web .chip:has(input:checked) {{ border-color: #b85c1d; background: #fff7f0; }}
.web .chip input:focus-visible ~ .box {{ outline: 3px solid #784646; outline-offset: 2px; }}
.web .chip .lbl {{ flex: 1; min-width: 0; font-size: 4.6cqw; font-weight: 600; }}
.web .chip .dt {{ font-size: 3.8cqw; font-style: italic; color: #b85c1d; font-weight: 400; }}
.web .err {{ margin: 0; padding: 3cqw 3.6cqw; border-radius: 2cqw; background: #fde8e4; color: #a3261a; font-size: 4.2cqw; font-style: italic; }}
.web .done {{ display: flex; flex-direction: column; gap: 3cqw; padding: 8cqw 0; outline: none; }}
.web .done h3 {{ font-size: 8.8cqw; color: #b85c1d; }}
#rsvp-more {{ display: flex; flex-direction: column; gap: 5cqw; }}
/* blessings */
.web .hosts-box {{ display: flex; flex-direction: column; gap: 2.4cqw; padding: 6cqw 5cqw; border-radius: 3cqw;
  background: #784646; color: #fdf5ef; border: 1.5px solid var(--gold); outline: 1px solid rgba(247,215,122,.6); outline-offset: -6px; }}
.web .hosts-box .label {{ color: #f7d77a; }}
.web .hosts {{ margin: 0; font-weight: 600; font-size: 7cqw; line-height: 1.2; display: flex; flex-direction: column; align-items: center; }}
.web .hosts span {{ font-style: italic; font-weight: 400; font-size: .7em; color: #f7d77a; }}
.web .hosts-box .lead {{ color: #fbe9dc; }}
.web .sides {{ display: grid; gap: 5cqw; margin-top: 1cqw; }}
.web .side {{ border: 1.5px solid var(--gold); border-radius: 3cqw; overflow: hidden; background: #fffaf4; }}
.web .side.bride .band {{ background: #b85c1d; }}
.web .side.groom .band {{ background: #1d2f5c; }}
.web .side dl {{ margin: 0; padding: 4cqw 4.5cqw 5cqw; display: grid; gap: 3.6cqw; }}
.web .rel {{ display: grid; gap: 1cqw; padding-bottom: 3.4cqw; border-bottom: 1px dashed #e2c3b3; }}
.web .rel:last-child {{ border-bottom: 0; padding-bottom: 0; }}
.web dt {{ justify-self: center; padding: .8cqw 3.2cqw; border-radius: 999px; background: #fbeee3; color: #b85c1d;
  font-size: 3.5cqw; font-weight: 600; letter-spacing: .14em; text-transform: uppercase; }}
.web dd {{ margin: 0; font-size: 4.5cqw; line-height: 1.4; }}
[hidden] {{ display: none !important; }}
</style>
</head>
<body>
<div class="intro" id="intro" role="dialog" aria-label="Wedding invitation of Soumya and Madhur">
  <div class="env" id="env">
    <div class="env-back"></div>
    <div class="env-letter"><img src="images/{model[0]["images"][1]["file"]}" alt=""><span>Soumya &amp; Madhur</span></div>
    <div class="env-front"></div>
    <div class="env-flap"></div>
    <button class="seal" id="seal" type="button" aria-label="Open the invitation"><img src="images/{model[2]["images"][1]["file"]}" alt=""></button>
  </div>
  <canvas class="burst" id="burst" aria-hidden="true"></canvas>
  <p class="intro-hint">Tap the seal to open</p>
  <button class="intro-skip" id="intro-skip" type="button">Skip</button>
</div>
<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>{defs}</defs></svg>
{''.join(sections)}
<script>
(function () {{
  var imgs = document.querySelectorAll('image[data-src]');
  function load(img) {{ img.setAttribute('href', img.getAttribute('data-src')); img.removeAttribute('data-src'); }}
  if (!('IntersectionObserver' in window)) {{ imgs.forEach(load); return; }}
  var io = new IntersectionObserver(function (es) {{
    es.forEach(function (e) {{ if (e.isIntersecting) {{
      e.target.querySelectorAll('image[data-src]').forEach(load); io.unobserve(e.target); }} }});
  }}, {{ rootMargin: '150% 0px' }});
  document.querySelectorAll('.page').forEach(function (p) {{ io.observe(p); }});
}})();


/* ---------- envelope intro: seal -> flap opens -> card slides fully out -> envelope fades -> card crossfades into the cover ---------- */
(function () {{
  var intro = document.getElementById('intro'), root = document.documentElement;
  if (!intro) return;
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var $ = function (s) {{ return intro.querySelector(s); }};
  var seal = $('#seal'), flap = $('.env-flap'), letter = $('.env-letter'), logo = $('.env-letter img'), env = $('#env');
  var busy = false, done = false;
  function wait(ms) {{ return new Promise(function (r) {{ setTimeout(r, ms); }}); }}
  function anim(el, frames, opt) {{
    if (!el.animate) {{ return Promise.resolve(); }}
    opt.fill = 'forwards'; return el.animate(frames, opt).finished.catch(function () {{}});
  }}
  function coverLogo() {{
    var f = logo.getAttribute('src').split('/').pop();
    return document.querySelector('#page-1 image[href$="' + f + '"]');
  }}
  function finish() {{
    if (done) return; done = true;
    window.scrollTo(0, 0); root.classList.remove('locked');
    var p1 = document.getElementById('page-1'); if (p1) p1.classList.add('seen');
    intro.classList.add('gone'); setTimeout(function () {{ intro.remove(); }}, 700);
  }}
  function burst() {{
    if (reduce || !window.__sparkStar) return;
    var cv = document.getElementById('burst'), ctx = cv.getContext('2d'), dpr = Math.min(2, devicePixelRatio || 1);
    cv.width = innerWidth * dpr; cv.height = innerHeight * dpr;
    var sr = seal.getBoundingClientRect(), cx = sr.left + sr.width / 2, cy = sr.top + sr.height / 2;
    var cols = ['#f7d77a', '#e9b949', '#fff1c4', '#d9a43a'], ps = [];
    for (var i = 0; i < 30; i++) {{ var a = Math.random() * 6.283, v = 80 + Math.random() * 220;
      ps.push({{ x: cx, y: cy, vx: Math.cos(a) * v, vy: Math.sin(a) * v - 50, r: 3 + Math.random() * 5, life: .8 + Math.random() * .8, t: 0, c: cols[i % 4] }}); }}
    var last = 0;
    (function frame(t) {{
      var dt = Math.min(.034, (t - (last || t)) / 1000); last = t; var alive = false;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.clearRect(0, 0, innerWidth, innerHeight);
      for (var i = 0; i < ps.length; i++) {{ var p = ps[i]; p.t += dt; if (p.t > p.life) continue; alive = true;
        p.vx *= .965; p.vy = p.vy * .965 + 110 * dt; p.x += p.vx * dt; p.y += p.vy * dt;
        var k = 1 - p.t / p.life, r = p.r * (.5 + .5 * k);
        ctx.globalAlpha = k; ctx.fillStyle = p.c; ctx.beginPath();          /* plain 4-point star: cheap to draw every frame */
        ctx.moveTo(p.x, p.y - r); ctx.lineTo(p.x + r * .28, p.y - r * .28); ctx.lineTo(p.x + r, p.y); ctx.lineTo(p.x + r * .28, p.y + r * .28);
        ctx.lineTo(p.x, p.y + r); ctx.lineTo(p.x - r * .28, p.y + r * .28); ctx.lineTo(p.x - r, p.y); ctx.lineTo(p.x - r * .28, p.y - r * .28); ctx.fill(); }}
      ctx.globalAlpha = 1;
      if (alive) requestAnimationFrame(frame); else ctx.clearRect(0, 0, innerWidth, innerHeight);
    }})(performance.now());
  }}
  async function open() {{
    if (busy) return; busy = true;
    if (reduce || !document.body.animate) {{ finish(); return; }}
    var ease = 'cubic-bezier(.45,0,.2,1)', soft = 'cubic-bezier(.4,0,.2,1)';
    anim($('.intro-hint'), [{{ opacity: 1 }}, {{ opacity: 0 }}], {{ duration: 300 }});
    anim($('.intro-skip'), [{{ opacity: 1 }}, {{ opacity: 0 }}], {{ duration: 300 }});
    seal.style.animation = 'none';
    burst();
    anim(seal, [{{ transform: 'translate(-50%,-50%) scale(1)', opacity: 1 }}, {{ transform: 'translate(-50%,-50%) scale(.35)', opacity: 0 }}],
         {{ duration: 420, easing: ease }});
    /* 1. the flap swings open (it passes behind the card halfway, like a real flap) */
    await anim(flap, [
      {{ transform: 'rotateX(0deg)', zIndex: 3 }},
      {{ transform: 'rotateX(90deg)', zIndex: 3, offset: .5 }},
      {{ transform: 'rotateX(90deg)', zIndex: 0, offset: .5001 }},
      {{ transform: 'rotateX(180deg)', zIndex: 0 }}], {{ duration: 950, delay: 180, easing: 'cubic-bezier(.4,0,.3,1)' }});
    /* 2. the card slides all the way out of the envelope */
    var envBox = env.getBoundingClientRect(), card = letter.getBoundingClientRect();
    var out = -(card.bottom - envBox.top) - 12;            /* card's bottom edge clears the top of the envelope */
    await anim(letter, [{{ transform: 'translateY(0)' }}, {{ transform: 'translateY(' + out + 'px)' }}],
               {{ duration: 1300, easing: 'cubic-bezier(.3,.7,.25,1)' }});
    /* 3. the empty envelope fades away gently while the card settles with its logo over the cover's logo */
    var pieces = intro.querySelectorAll('.env-back, .env-front, .env-flap');
    pieces.forEach(function (el) {{
      var t = getComputedStyle(el).transform; t = (t && t !== 'none') ? t : '';
      anim(el, [{{ opacity: 1, transform: t || 'translateY(0)' }}, {{ opacity: 0, transform: (t ? t + ' ' : '') + 'translateY(24px)' }}], {{ duration: 900, easing: soft }});
    }});
    var target = coverLogo(), lr = logo.getBoundingClientRect(), settle = out;
    if (target) {{
      var to = target.getBoundingClientRect();
      settle = out + ((to.top + to.height / 2) - (lr.top + lr.height / 2));
    }}
    await anim(letter, [{{ transform: 'translateY(' + out + 'px)' }}, {{ transform: 'translateY(' + settle + 'px)' }}],
               {{ duration: 1000, easing: soft }});
    await wait(250);
    /* 4. crossfade: the card and its logo fade out while the cover and its logo fade in */
    var p1 = document.getElementById('page-1');
    window.scrollTo(0, 0);
    root.classList.remove('locked');
    setTimeout(function () {{ if (p1) p1.classList.add('seen'); }}, 500);
    await anim(intro, [{{ opacity: 1 }}, {{ opacity: 0 }}], {{ duration: 1400, easing: 'ease-in-out' }});
    finish();
  }}
  seal.addEventListener('click', open);
  env.addEventListener('click', open);
  $('#intro-skip').addEventListener('click', finish);
  document.querySelectorAll('a.open').forEach(function (a) {{
    a.addEventListener('click', function (e) {{ e.preventDefault(); document.getElementById('page-2').scrollIntoView({{ behavior: reduce ? 'auto' : 'smooth' }}); }});
  }});
}})();

/* ---------- reveal sections as they scroll into view ---------- */
(function () {{
  var els = document.querySelectorAll('.page, .web');
  if (!('IntersectionObserver' in window)) {{ els.forEach(function (e) {{ e.classList.add('seen'); }}); return; }}
  var io = new IntersectionObserver(function (es) {{
    es.forEach(function (e) {{
      if (e.isIntersecting && !document.documentElement.classList.contains('locked')) {{ e.target.classList.add('seen'); io.unobserve(e.target); }}
    }});
  }}, {{ threshold: 0.25 }});
  els.forEach(function (e) {{ io.observe(e); }});
  // safety: anything still hidden after the intro shows anyway
  setTimeout(function () {{ if (!document.documentElement.classList.contains('locked')) return; }}, 0);
  window.addEventListener('scroll', function once() {{
    els.forEach(function (e) {{ var r = e.getBoundingClientRect(); if (r.top < innerHeight * .75 && r.bottom > 0) e.classList.add('seen'); }});
  }}, {{ passive: true }});
}})();

/* ---------- countdown to the Tilak (24 Nov 2026, 4:30 PM IST) ---------- */
(function () {{
  var box = document.getElementById('countdown'); if (!box) return;
  var target = Date.parse('2026-11-24T16:30:00+05:30');
  var u = {{}}; box.querySelectorAll('b').forEach(function (b) {{ u[b.dataset.u] = b; }});
  function tick() {{
    var t = Math.max(0, target - Date.now()) / 1000;
    u.d.textContent = Math.floor(t / 86400); u.h.textContent = Math.floor(t % 86400 / 3600);
    u.m.textContent = Math.floor(t % 3600 / 60); u.s.textContent = Math.floor(t % 60);
    if (t <= 0) {{ box.nextElementSibling.textContent = 'The celebrations have begun!'; return; }}
    setTimeout(tick, 1000 - Date.now() % 1000);
  }}
  tick();
}})();

/* ---------- falling petals, marigolds and leaves on every page ---------- */
(function () {{
  if (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  var PETAL = ['#e8829b', '#f2a7b6', '#d9577a', '#f6c4cc', '#e0607e'];
  var MARI = ['#f39a1f', '#f8b733', '#ef8a17'];
  var LEAF = ['#7da46a', '#5f8a4f', '#9cbf84'];
  function pick(a) {{ return a[Math.floor(Math.random() * a.length)]; }}
  var GOLD = ['#f7d77a', '#e9b949', '#fff1c4', '#d9a43a'];
  function star(ctx, x, y, r, a, c) {{           /* a soft glow with a four-point twinkle */
    ctx.save(); ctx.globalAlpha = a; ctx.translate(x, y);
    var g = ctx.createRadialGradient(0, 0, 0, 0, 0, r * 1.6);
    g.addColorStop(0, 'rgba(255,244,205,.95)'); g.addColorStop(.35, 'rgba(247,215,122,.45)'); g.addColorStop(1, 'rgba(247,215,122,0)');
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(0, 0, r * 1.6, 0, 6.283); ctx.fill();
    ctx.fillStyle = c; ctx.beginPath();
    ctx.moveTo(0, -r); ctx.quadraticCurveTo(r * .12, -r * .12, r, 0); ctx.quadraticCurveTo(r * .12, r * .12, 0, r);
    ctx.quadraticCurveTo(-r * .12, r * .12, -r, 0); ctx.quadraticCurveTo(-r * .12, -r * .12, 0, -r); ctx.fill();
    ctx.restore();
  }}
  window.__sparkStar = star;
  function shape(ctx, p) {{
    var s = p.s;
    if (p.k === 'leaf') {{
      ctx.fillStyle = p.c; ctx.beginPath(); ctx.moveTo(0, -s * 1.3);
      ctx.quadraticCurveTo(s * .9, 0, 0, s * 1.3); ctx.quadraticCurveTo(-s * .9, 0, 0, -s * 1.3); ctx.fill();
      ctx.strokeStyle = 'rgba(255,255,255,.35)'; ctx.lineWidth = Math.max(.6, s * .08);
      ctx.beginPath(); ctx.moveTo(0, -s * 1.1); ctx.lineTo(0, s * 1.1); ctx.stroke();
    }} else if (p.k === 'mari') {{
      ctx.fillStyle = p.c;
      for (var i = 0; i < 8; i++) {{ ctx.rotate(Math.PI / 4); ctx.beginPath(); ctx.ellipse(0, -s * .55, s * .32, s * .55, 0, 0, 6.283); ctx.fill(); }}
      ctx.fillStyle = '#c96a10'; ctx.beginPath(); ctx.arc(0, 0, s * .3, 0, 6.283); ctx.fill();
    }} else {{
      ctx.fillStyle = p.c; ctx.beginPath(); ctx.moveTo(0, -s);
      ctx.bezierCurveTo(s * .9, -s * .6, s * .7, s * .7, 0, s); ctx.bezierCurveTo(-s * .7, s * .7, -s * .9, -s * .6, 0, -s); ctx.fill();
    }}
  }}
  document.querySelectorAll('canvas.petals').forEach(function (cv) {{
    var ctx = cv.getContext('2d'), sec = cv.parentElement, box = sec.querySelector('svg') || sec.querySelector('.col') || sec;
    var COUNT = +(cv.dataset.n || 12), SPARKS = cv.dataset.n ? 5 : 9, W = 0, H = 0, dpr = 1, ps = [], sp = [], run = false, last = 0;
    function size() {{
      var r = box.getBoundingClientRect(), s = sec.getBoundingClientRect();
      dpr = Math.min(2, window.devicePixelRatio || 1);
      cv.style.left = (r.left - s.left) + 'px'; cv.style.top = (r.top - s.top) + 'px';
      cv.style.width = r.width + 'px'; cv.style.height = r.height + 'px';
      W = r.width; H = r.height; cv.width = W * dpr; cv.height = H * dpr;
    }}
    function item(init) {{
      var r = Math.random(), k = r < .62 ? 'petal' : (r < .82 ? 'mari' : 'leaf');
      var base = Math.min(W, 560);
      var s = (k === 'mari' ? .016 : .013 + Math.random() * .01) * base;
      return {{ k: k, x: Math.random() * W, y: init ? Math.random() * H : -s * 3, s: s,
        vy: (40 + Math.random() * 45) * (k === 'leaf' ? 1.15 : 1),       /* px per second, like a leaf drifting down */
        sway: 14 + Math.random() * 30, ph: Math.random() * 6.28, sw: .6 + Math.random() * .7,
        rot: Math.random() * 6.28, vr: (Math.random() - .5) * 1.8, flip: Math.random() * 6.28, vf: 1.4 + Math.random() * 1.6,
        c: pick(k === 'leaf' ? LEAF : k === 'mari' ? MARI : PETAL) }};
    }}
    function spark(init) {{
      return {{ x: Math.random() * W, y: Math.random() * H * .92, r: (3 + Math.random() * 5) * Math.min(1.4, W / 400),
        life: 1.4 + Math.random() * 1.8, t: init ? -Math.random() * 3 : -Math.random() * .8, rot: Math.random() * .8, c: pick(GOLD) }};
    }}
    function draw(t) {{
      if (!run) return;
      var dt = Math.min(0.05, (t - (last || t)) / 1000); last = t;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.clearRect(0, 0, W, H);
      for (var j = 0; j < sp.length; j++) {{
        var q = sp[j]; q.t += dt;
        if (q.t > q.life) {{ sp[j] = spark(false); continue; }}
        if (q.t < 0) continue;
        var k = Math.sin(Math.PI * q.t / q.life);             /* fade in, peak, fade out */
        ctx.save(); ctx.translate(q.x, q.y); ctx.rotate(q.rot + q.t * .6); star(ctx, 0, 0, q.r * (.4 + .6 * k), k * .95, q.c); ctx.restore();
      }}
      for (var i = 0; i < ps.length; i++) {{
        var p = ps[i];
        p.y += p.vy * dt; p.ph += dt * p.sw; p.rot += p.vr * dt + Math.cos(p.ph) * dt * .8; p.flip += dt * p.vf;
        var x = p.x + Math.sin(p.ph) * p.sway;
        if (p.y > H + p.s * 3) {{ ps[i] = item(false); continue; }}
        ctx.save(); ctx.translate(x, p.y); ctx.rotate(p.rot);
        ctx.scale(1, .3 + .7 * Math.abs(Math.cos(p.flip)));      /* tumbling, the way leaves fall */
        ctx.globalAlpha = .88; shape(ctx, p); ctx.restore();
      }}
      requestAnimationFrame(draw);
    }}
    function start() {{ if (run) return; if (document.documentElement.classList.contains('locked')) {{ setTimeout(function () {{ if (vis) start(); }}, 300); return; }} size(); if (!ps.length) for (var i = 0; i < COUNT; i++) ps.push(item(true)); if (!sp.length) for (var j = 0; j < SPARKS; j++) sp.push(spark(true)); run = true; last = 0; requestAnimationFrame(draw); }}
    function stop() {{ run = false; }}
    var vis = false;
    new IntersectionObserver(function (es) {{ es.forEach(function (e) {{ vis = e.isIntersecting; vis ? start() : stop(); }}); }}).observe(sec);
    window.addEventListener('resize', function () {{ if (run) {{ size(); ps = []; sp = []; for (var i = 0; i < COUNT; i++) ps.push(item(true)); for (var j = 0; j < SPARKS; j++) sp.push(spark(true)); }} }});
  }});
}})();

/* RSVP: replies go straight into the Google Form (see Guides/RSVP-SETUP.md) */
(function () {{
  /* Connected to Google Form "💍 Madhur & Soumya | Wedding RSVP 🎉" */
  var GOOGLE_FORM = {{
    id: "1FAIpQLSfnBOj2V0I5WwqbaIJzzUCkaqaY4ZEuZ3dqVqI0_m0bwpd1yA",
    name: "127160018", phone: "1746679459", attending: "55150948",
    guests: "798723131", events: "142255648", message: "1689328520",
    /* website answer -> the exact option text in the Google Form */
    options: {{
      "Joyfully attending": "🎉 Joyfully attending",
      "Regretfully unable": "💌 Regretfully unable",
      "Tilak": "🌸 Tilak (24 Nov)",
      "Engagement & Sangeet": "💃 Engagement & Sangeet (24 Nov)",
      "Haldi & Mehendi": "🌼 Haldi & Mehendi (25 Nov)",
      "Baraat": "🥁 Baraat (25 Nov)",
      "Jaimala": "💐 Jaimala (25 Nov)"
    }}
  }};
  var f = document.getElementById('rsvp-form'); if (!f) return;
  var more = document.getElementById('rsvp-more'), err = document.getElementById('rsvp-err');
  var btn = document.getElementById('rsvp-send'), done = document.getElementById('rsvp-done');
  f.addEventListener('change', function (e) {{
    if (e.target.name === 'attending') more.hidden = e.target.value === 'Regretfully unable';
  }});
  f.addEventListener('input', function () {{ err.hidden = true; }});
  function fail(msg, el) {{ err.textContent = msg; err.hidden = false; if (el) el.focus(); }}
  f.addEventListener('submit', function (e) {{
    e.preventDefault(); err.hidden = true;
    var name = f.elements['name'].value.trim(), phone = f.phone.value.trim(), att = f.querySelector('input[name=attending]:checked');
    if (!name) return fail('Please enter your name.', f.elements['name']);
    if (phone.replace(/\\D/g, '').length < 10) return fail('Please enter a mobile number with at least 10 digits.', f.phone);
    if (!att) return fail('Please choose whether you can join us.', document.getElementById('rsvp-yes'));
    var coming = att.value === 'Joyfully attending';
    var evs = coming ? [].map.call(f.querySelectorAll('input[name=events]:checked'), function (c) {{ return c.value; }}) : [];
    if (coming && !evs.length) return fail('Please tick at least one event.', document.getElementById('ev-tilak'));
    var G = GOOGLE_FORM, data = new URLSearchParams();
    function put(k, v) {{ if (G[k] && v !== '') data.append('entry.' + G[k], G.options[v] || v); }}
    put('name', name); put('phone', phone); put('attending', att.value);
    if (coming) {{ put('guests', f.guests.value || '1'); evs.forEach(function (v) {{ put('events', v); }}); }}
    put('message', f.message.value.trim());
    data.append('pageHistory', coming ? '0,1' : '0');   // the form's 2nd section is only for guests who are coming
    var SCRIPT_URL = G.id ? 'https://docs.google.com/forms/d/e/' + G.id + '/formResponse' : '';
    if (!SCRIPT_URL) return fail('RSVP is not connected yet. Please contact the family directly.');
    btn.disabled = true; btn.textContent = 'Sending…';
    fetch(SCRIPT_URL, {{ method: 'POST', mode: 'no-cors', body: data }}).then(function () {{
      f.hidden = true; done.hidden = false;
      document.getElementById('rsvp-done-msg').textContent = coming
        ? 'We have received your RSVP, ' + name + '. We look forward to celebrating with you.'
        : 'Thank you for letting us know, ' + name + '. You will be missed, and your blessings mean a lot to us.';
      done.focus();
    }}).catch(function () {{
      btn.disabled = false; btn.textContent = 'Send RSVP';
      fail('Your RSVP could not be sent. Please check your internet connection and try again.');
    }});
  }});
}})();
</script>
</body>
</html>
"""
out = f"{SITE}/index.html" if MODE == "site" else f"{SITE}/test.html"
open(out, "w", encoding="utf-8", newline="\n").write(page)
json.dump(checklist, open(f"{S}/checklist.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", out, len(page) // 1024, "KB; glyphs", len(used_glyphs))
