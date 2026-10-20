"""Build the e-invite website from the extracted PDF model.
Unchanged text is drawn with the PDF's own glyph outlines at their exact positions.
Only the items in the CHANGES list are altered."""
import json, re, os, sys, html, math
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
os.makedirs(f"{SITE}/audio", exist_ok=True)
shutil.copy2(os.path.join(paths.SOURCE, "audio", "chaap-tilak.mp3"), os.path.join(SITE, "audio", "chaap-tilak.mp3"))
os.makedirs(f"{SITE}/images", exist_ok=True)
shutil.copy2(os.path.join(paths.SOURCE, "assets", "jaimala-page.png"),
             os.path.join(SITE, "images", "jaimala-page.png"))

# ---------------- decisions agreed with the user ----------------
PARENTS = {
    "soumya": ["Daughter of Mrs. Rashmi Gupta &", "Mr. Umakant Gupta"],
    "madhur": ["Son of Mrs. Bhawana Gupta &", "Mr. Santosh Gupta"],
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

    if n == 7:
        # The approved high-resolution composition replaces the page artwork;
        # original text glyphs remain vector layers above it.
        body = ['<image href="images/jaimala-page.png" x="0" y="0" width="810" height="1440" preserveAspectRatio="xMidYMid slice"/>',
                '<image href="images/img-16-251x251.png" width="1" height="1" preserveAspectRatio="none" transform="matrix(42.75,0,0,42.75,383.7828,617.9515)"/>']
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
    if n == 7:
        y0 -= 30  # separate the venue address from the groom's pagdi
        checklist.append(("7", "Venue address position", "Moved the Jaimala venue address up 30 pt to clear the groom's pagdi"))
    P["_extra"] += live_text([L["text"].strip() for L in V], cx, y0, pitch, VENUE_SIZE, V[0]["color"],
                             400, "italic", V[0]["track"] / old)
    last_base = y0 + pitch * (len(V) - 1)
    url = MAPS["havana"] if "Havana" in V[0]["text"] else MAPS["royal"]
    col = V[0]["color"]
    bw, bh, by = 250, 54, last_base + 40
    if n in (5, 6):   # Haldi & Mehendi and Baraat: the button sits a little higher, clear of the artwork below it
        by -= 24 if n == 5 else 28
    if n == 7:   # Jaimala: the peacock's neck sits under the centre, so the button sits in the clear sky beside it
        bw, cx = 214, 487
    if n != 7:
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
mono_top = f + d * alpha_bb[1] / mono["h"]
_gy = mono_top - 14        # baseline of the guest's name, just above the monogram
model[0]["_extra"].append(
    f'<g id="cover-guest" class="cg" aria-live="polite">'
    f'<text x="{mono_cx:.2f}" y="{_gy - 66:.2f}" text-anchor="middle" font-family="Crimson Text" font-weight="600" font-size="23" '
    f'letter-spacing="4.6" fill="#784646">WITH LOVE, TO</text>'
    f'<text id="cover-guest-name" x="{mono_cx:.2f}" y="{_gy:.2f}" text-anchor="middle" font-family="Crimson Text" font-style="italic" '
    f'font-weight="600" font-size="58" fill="#b85c1d"></text></g>')
model[0]["_extra"].append(
    f'<a class="open" href="#page-2" aria-label="Scroll down to the invitation">'
    f'<text x="{mono_cx:.2f}" y="{group_ink(allg)[3] + 50:.2f}" text-anchor="middle" font-family="Crimson Text" '
    f'font-style="italic" font-size="29" letter-spacing="1.6" fill="#784646">Scroll down</text>'
    f'<path class="chev" d="M{mono_cx - 15:.2f} {group_ink(allg)[3] + 70:.2f} L{mono_cx:.2f} {group_ink(allg)[3] + 86:.2f} L{mono_cx + 15:.2f} {group_ink(allg)[3] + 70:.2f}" '
    f'fill="none" stroke="#784646" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/></a>')
print("page1 names: monogram bottom", round(mono_bottom, 1), "gap", round(gap_v, 1), "ink box", [round(v, 1) for v in group_ink(allg)])
checklist.append(("1", "Names on cover", f"“Soumya & Madhur” added below the monogram in the same lettering as the names on page 2 (script names, 63 pt, #784646; italic “&”, #b85c1d), centred under the monogram, {gap_v:.0f} pt below it (the same gap as above the names on page 2)"))

# ---------- website sections between the cards (card fonts, colours, divider) ----------
ORN = "images/" + model[2]["images"][1]["file"]
DIV = f'<div class="divider" aria-hidden="true"><span></span><img src="{ORN}" alt=""><span></span></div>'
# The sections reuse the card artwork, untouched, exactly as pages 2 and 8 place it:
#   sky = the page-2/8 sky (tiled, every other tile mirrored so the joins are seamless),
#   head = the garland and the two top leaf sprigs, foot = the flower clusters along the bottom of page 8.
SKY = model[1]["images"][0]["file"]
def _lay(im, op=1):
    a, b, c, d, e, f = im["m"]
    opa = "" if op == 1 else f' opacity="{op}"'
    return (f'<image href="images/{im["file"]}"{opa} width="1" height="1" preserveAspectRatio="none" '
            f'transform="matrix({a},{b},{c},{d},{e},{f})"/>')
_p8 = list(zip(model[7]["images"], OPAC["8"]))
_garland = next(k for k, (im, _) in enumerate(_p8) if im["file"].startswith("img-08"))
ART_HEAD = ('<svg class="head" viewBox="0 0 810 340" aria-hidden="true">'
            + "".join(_lay(im, op) for im, op in [_p8[_garland]] + [t for t in _p8[_garland + 1:] if t[0]["m"][5] < 200])
            + '</svg>')
ART_FOOT = ('<svg class="foot" viewBox="0 780 810 660" aria-hidden="true">'
            + "".join(_lay(im, op) for im, op in _p8 if im["m"][5] >= 990)
            + '</svg>')
def _marigold(cx, cy, r=15):
    out = "".join(f'<circle cx="{cx + r * .72 * math.cos(k * math.pi / 4):.1f}" cy="{cy + r * .72 * math.sin(k * math.pi / 4):.1f}" r="{r * .42:.1f}" fill="#f7b32f"/>' for k in range(8))
    return out + f'<circle cx="{cx}" cy="{cy}" r="{r * .66:.1f}" fill="#ee8f12"/><circle cx="{cx}" cy="{cy}" r="{r * .24:.1f}" fill="#b85a06"/>'
_strands = [(30, 7), (92, 9), (156, 6), (222, 8), (288, 9), (352, 6), (418, 8), (484, 9), (548, 6), (614, 8), (680, 9), (748, 7), (796, 5)]
MARIGOLDS = ('<svg class="head" viewBox="0 0 810 380" aria-hidden="true"><line x1="0" y1="14" x2="810" y2="14" stroke="#7a4a12" stroke-width="3"/>'
             + "".join(f'<line x1="{x}" y1="14" x2="{x}" y2="{14 + n * 34}" stroke="#7a4a12" stroke-width="2"/>'
                       + "".join(_marigold(x, 34 + i * 34) for i in range(n)) for x, n in _strands)
             + '</svg>')
# ---- bride's side: the Jaimala candle scene (pillar candles, a floor of tea-lights, red roses) ----
_FLAME = "M0 -46 C11 -28 10 -9 0 -4 C-10 -9 -11 -28 0 -46Z"
def _pillar(x, top, w=24, flame="f1"):
    return (f'<ellipse cx="{x}" cy="196" rx="{w * .8}" ry="5" fill="#2a0a12" opacity=".5"/>'
            f'<circle class="halo" cx="{x}" cy="{top - 24}" r="52" fill="url(#cg)"/>'
            f'<rect x="{x - w / 2}" y="{top}" width="{w}" height="{196 - top}" rx="3" fill="url(#cb)"/>'
            f'<ellipse cx="{x}" cy="{top + 1}" rx="{w / 2}" ry="3.6" fill="#fff8e6"/>'
            f'<line x1="{x}" y1="{top}" x2="{x}" y2="{top - 8}" stroke="#4a3320" stroke-width="2.2"/>'
            f'<g transform="translate({x} {top - 6}) scale(.8)"><path class="flame {flame}" d="{_FLAME}" fill="url(#cf)"/></g>')
def _tealight(x, y, flame="f1"):
    return (f'<ellipse cx="{x}" cy="{y + 12}" rx="5" ry="15" fill="#ffd27a" opacity=".22"/>'
            f'<circle class="halo" cx="{x}" cy="{y - 8}" r="26" fill="url(#cg)"/>'
            f'<path d="M{x - 9} {y} q0 8 9 8 q9 0 9 -8z" fill="#e6cba0"/><ellipse cx="{x}" cy="{y}" rx="9" ry="3.2" fill="#f6e6c6"/>'
            f'<g transform="translate({x} {y - 1}) scale(.42)"><path class="flame {flame}" d="{_FLAME}" fill="url(#cf)"/></g>')
def _rose(cx, cy, r):
    return (f'<ellipse cx="{cx - r * .9}" cy="{cy - r * .2}" rx="{r * .6}" ry="{r * .26}" fill="#2f5a2a" transform="rotate(-25 {cx - r * .9} {cy - r * .2})"/>'
            f'<ellipse cx="{cx + r * .9}" cy="{cy - r * .3}" rx="{r * .6}" ry="{r * .26}" fill="#3a6a31" transform="rotate(25 {cx + r * .9} {cy - r * .3})"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#9b1028"/><circle cx="{cx}" cy="{cy}" r="{r * .8}" fill="#bd1a38"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r * .58}" fill="#d12a47"/><circle cx="{cx}" cy="{cy}" r="{r * .36}" fill="#a3122b"/>'
            f'<path d="M{cx - r * .55} {cy - r * .1} Q{cx} {cy - r * .75} {cx + r * .55} {cy - r * .05} M{cx - r * .3} {cy + r * .35} Q{cx + r * .1} {cy + r * .05} {cx + r * .35} {cy + r * .3}" '
            f'fill="none" stroke="#6d0a1d" stroke-width="2" stroke-linecap="round"/>'
            f'<path d="M{cx - r * .5} {cy - r * .45} Q{cx - r * .1} {cy - r * .8} {cx + r * .3} {cy - r * .55}" fill="none" stroke="#e8586f" stroke-width="2" opacity=".7" stroke-linecap="round"/>')
_L = [(70, 100, 24, "f1"), (112, 62, 26, "f2"), (152, 104, 24, "f3"), (192, 84, 22, "f1")]
_R = [(618, 88, 24, "f2"), (660, 104, 24, "f3"), (702, 60, 26, "f1"), (746, 98, 24, "f2")]
_TEA = [(95, 236), (150, 266), (212, 226), (262, 290), (306, 246), (350, 304), (402, 232), (444, 278), (486, 312), (524, 242), (568, 292), (612, 228),
        (656, 270), (706, 240), (752, 290), (28, 272), (788, 240), (376, 266)]
SCENE = ('<svg class="scene" viewBox="0 0 810 330" aria-hidden="true"><defs>'
         '<radialGradient id="cg"><stop offset="0" stop-color="#ffd27a" stop-opacity=".95"/><stop offset="1" stop-color="#ffb347" stop-opacity="0"/></radialGradient>'
         '<linearGradient id="cb" x1="0" x2="1"><stop offset="0" stop-color="#f1d9b0"/><stop offset=".45" stop-color="#fff4dc"/><stop offset="1" stop-color="#e8c994"/></linearGradient>'
         '<linearGradient id="cf" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#ff9d1c"/><stop offset=".55" stop-color="#ffd35a"/><stop offset="1" stop-color="#fff3b0"/></linearGradient>'
         '<linearGradient id="fl" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5a1522" stop-opacity="0"/><stop offset=".22" stop-color="#4a1220" stop-opacity=".92"/><stop offset="1" stop-color="#22070e"/></linearGradient>'
         '<linearGradient id="lg1" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#ffb23d"/><stop offset="1" stop-color="#ff7a2a"/></linearGradient>'
         '<linearGradient id="lg2" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#ffd56a"/><stop offset="1" stop-color="#f59a2e"/></linearGradient>'
         '<linearGradient id="lg3" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#ff9f6a"/><stop offset="1" stop-color="#e8506e"/></linearGradient>'
         '</defs><rect x="0" y="110" width="810" height="220" fill="url(#fl)"/>'
         + "".join(_pillar(*t) for t in _L + _R)
         + "".join(_tealight(x, y, ("f1", "f2", "f3")[i % 3]) for i, (x, y) in enumerate(_TEA))
         + "".join(_rose(x, y, r) for x, y, r in [(30, 316, 40), (92, 326, 36), (156, 332, 34), (62, 276, 30), (118, 296, 28),
                                                   (780, 316, 40), (718, 326, 36), (654, 332, 34), (748, 276, 30), (692, 296, 28)])
         + '</svg>')

# ---- groom's side: the Haldi & Mehendi page's yellow curtains, bell-and-flower strings and bougainvillea ----
def _bead(x, y, k):
    return (f'<circle cx="{x}" cy="{y}" r="7" fill="#e8508a"/><circle cx="{x}" cy="{y}" r="3" fill="#f7b6cc"/>' if k % 2 == 0
            else f'<circle cx="{x}" cy="{y}" r="7.5" fill="#f59a1b"/><circle cx="{x}" cy="{y}" r="3" fill="#c76a06"/>')
def _bell(x, y):
    return (f'<path d="M{x - 15} {y} C{x - 15} {y - 22} {x - 8} {y - 30} {x} {y - 30} C{x + 8} {y - 30} {x + 15} {y - 22} {x + 15} {y} L{x + 20} {y + 9} H{x - 20}Z" fill="url(#bg)"/>'
            f'<path d="M{x - 9} {y - 24} Q{x - 11} {y - 8} {x - 12} {y + 6} M{x + 9} {y - 24} Q{x + 11} {y - 8} {x + 12} {y + 6}" fill="none" stroke="#7a4d10" stroke-width="1.4" opacity=".6"/>'
            f'<circle cx="{x}" cy="{y - 32}" r="3.4" fill="#b9801f"/><circle cx="{x}" cy="{y + 12}" r="3.6" fill="#7a4d10"/>'
            + "".join(f'<circle cx="{x}" cy="{y + 22 + i * 12}" r="{7 - i}" fill="#f59a1b"/><circle cx="{x}" cy="{y + 22 + i * 12}" r="{2.6 - i * .5}" fill="#c76a06"/>' for i in range(3)))
_P = {f: x for f, x in ((m["file"][:6], m["file"]) for m in model[7]["images"])}
def _img(key, a, d, e, f, flip=False):
    m = f'matrix({-a if flip else a},0,0,{d},{e + a if flip else e},{f})'
    return f'<image href="images/{_P[key]}" width="1" height="1" preserveAspectRatio="none" transform="{m}"/>'
HALDI_HEAD = ('<svg class="head" viewBox="0 0 810 380" aria-hidden="true"><defs>'
              '<linearGradient id="cu" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fbe48c"/><stop offset="1" stop-color="#f1b73a"/></linearGradient>'
              '<linearGradient id="bg" x1="0" x2="1"><stop offset="0" stop-color="#a8721a"/><stop offset=".4" stop-color="#f0c15a"/><stop offset="1" stop-color="#8a5a14"/></linearGradient></defs>'
              '<g id="curl"><path d="M0 0 H178 C172 92 150 168 118 232 C96 282 56 322 0 344Z" fill="url(#cu)"/>'
              '<path d="M44 0 C46 100 36 200 0 300 M92 0 C96 100 84 190 40 290 M138 0 C142 96 126 180 84 262" fill="none" stroke="#c98a12" stroke-width="2" opacity=".35"/></g>'
              '<use href="#curl" transform="translate(810 0) scale(-1 1)"/>'
              + "".join(f'<line x1="{x}" y1="0" x2="{x}" y2="{y}" stroke="#7a4d10" stroke-width="1.6"/>'
                        + "".join(_bead(x, 22 + i * 26, i) for i in range((y - 40) // 26)) + _bell(x, y)
                        for x, y in [(212, 150), (262, 232), (312, 180), (362, 246), (412, 160), (462, 238), (512, 190), (562, 244), (612, 150)])
              + _img("img-06", 170, 219, -30, -64) + _img("img-06", 170, 219, 670, -64, True) + _img("img-06", 130, 168, 330, -92)
              + _img("img-07", 120, 120, 150, -36) + _img("img-07", 120, 120, 540, -40, True)
              + '</svg>')
HYDRANGEAS = "".join(f'<img class="hyd {c}" src="images/{_P["img-05"]}" alt="" aria-hidden="true">' for c in ("ha", "hb", "hc"))
LEAVES = "".join(f'<img class="leaf {c}" src="images/{_P["img-07"]}" alt="" aria-hidden="true">' for c in ("la", "lb", "lc", "ld"))
VINES = "".join(f'<img class="vine {c}" src="images/{_P["img-06"]}" alt="" aria-hidden="true">' for c in ("va", "vb", "vc", "vd", "ve", "vf"))
def _lantern(side, pos, top, w, grad, cls):
    return (f'<svg class="lantern {cls}" viewBox="0 0 60 100" aria-hidden="true" style="{side}:{pos}%;top:{top}%;width:{w}cqw">'
            f'<circle cx="30" cy="42" r="40" fill="url(#cg)" opacity=".75"/>'
            f'<path d="M30 6 L30 14" stroke="#8a3b12" stroke-width="2"/>'
            f'<path d="M12 22 Q30 12 48 22 L53 66 Q30 78 7 66 Z" fill="url(#{grad})" stroke="#9a4415" stroke-width="1.4"/>'
            f'<path d="M30 16 Q19 42 22 72 M30 16 Q41 42 38 72 M30 16 L30 74" fill="none" stroke="#9a4415" stroke-width="1" opacity=".55"/>'
            f'<ellipse cx="30" cy="46" rx="11" ry="17" fill="#fff6c2" opacity=".85"/>'
            f'<rect x="14" y="18" width="32" height="6" rx="3" fill="#8a3b12"/><rect x="11" y="64" width="38" height="7" rx="3" fill="#8a3b12"/>'
            f'<path d="M30 71 L30 86" stroke="#8a3b12" stroke-width="1.6"/><circle cx="30" cy="89" r="3.4" fill="#f2c14e"/>'
            f'<path d="M24 72 L22 84 M36 72 L38 84" stroke="#8a3b12" stroke-width="1.2"/></svg>')
LANTERNS = "".join(_lantern(*a) for a in [("left", 3, 12, 12, "lg1", "l1"), ("right", 4, 25, 10, "lg2", "l2"), ("left", 6, 41, 11, "lg3", "l3"),
                                          ("right", 3, 56, 12, "lg1", "l4"), ("left", 4, 71, 10, "lg2", "l5")])
# ---- colourful butterflies and birds drifting across the bright-sky sections ----
import random as _rnd
_BFLY = [("#ff7a1a", "#ffc23a"), ("#2f7cff", "#7fd1ff"), ("#e8429b", "#ffa6d0"), ("#8a4bd8", "#c9a4ff"), ("#ffd21a", "#ff9a1a"), ("#17b26a", "#9cf0c2")]
_BIRD = [("#2fb4e8", "#ffd23a", "#ff8a1a"), ("#ff6a3d", "#ffd23a", "#ffb000"), ("#2bc16b", "#ffe04a", "#ff7a1a"), ("#c04bd8", "#ffb3e6", "#ffb000")]
def _butterfly(c1, c2, f):
    return (f'<svg viewBox="0 0 60 50" style="--f:{f}s" aria-hidden="true">'
            f'<g class="wl"><path d="M30 24 C14 2 2 8 4 22 C5 30 20 30 30 26Z" fill="{c1}"/><path d="M30 26 C18 30 8 40 16 46 C24 50 30 38 30 28Z" fill="{c2}"/>'
            f'<circle cx="13" cy="16" r="3" fill="#fff" opacity=".8"/><circle cx="19" cy="40" r="2.2" fill="#fff" opacity=".8"/></g>'
            f'<g class="wr"><path d="M30 24 C46 2 58 8 56 22 C55 30 40 30 30 26Z" fill="{c1}"/><path d="M30 26 C42 30 52 40 44 46 C36 50 30 38 30 28Z" fill="{c2}"/>'
            f'<circle cx="47" cy="16" r="3" fill="#fff" opacity=".8"/><circle cx="41" cy="40" r="2.2" fill="#fff" opacity=".8"/></g>'
            f'<ellipse cx="30" cy="27" rx="1.9" ry="9" fill="#3a2418"/><path d="M29 18 Q26 10 22 8 M31 18 Q34 10 38 8" fill="none" stroke="#3a2418" stroke-width="1.1" stroke-linecap="round"/></svg>')
def _bird(body, wing, beak, f):
    return (f'<svg viewBox="0 0 80 50" style="--f:{f}s" aria-hidden="true">'
            f'<path d="M24 28 L4 21 L8 32Z" fill="{wing}"/><ellipse cx="38" cy="28" rx="18" ry="10" fill="{body}"/><ellipse cx="38" cy="32" rx="12" ry="5" fill="#fff" opacity=".35"/>'
            f'<circle cx="56" cy="22" r="7.5" fill="{body}"/><path d="M62 21 L73 24 L62 27Z" fill="{beak}"/><circle cx="58" cy="20.5" r="1.9" fill="#fff"/><circle cx="58.6" cy="20.5" r=".9" fill="#222"/>'
            f'<path class="bw" d="M32 27 C28 8 46 1 58 8 C48 14 44 22 42 29Z" fill="{wing}"/></svg>')
def critters(n_b, n_k, seed=3):
    r = _rnd.Random(seed); out = []
    for i in range(n_b):
        c1, c2 = _BFLY[i % len(_BFLY)]; rev = i % 3 == 1
        out.append(f'<div class="crit b{" rev" if rev else ""}" style="top:{6 + 86 * (i + r.random() * .6) / n_b:.1f}%;--t:{r.randint(30, 48)}s;--d:-{r.randint(0, 40)}s;--w:{r.randint(7, 10)}cqw">'
                   f'<div class="bob" style="--b:{r.uniform(2.2, 3.6):.1f}s">{_butterfly(c1, c2, round(r.uniform(.26, .4), 2))}</div></div>')
    for i in range(n_k):
        c = _BIRD[i % len(_BIRD)]; rev = i % 2 == 1
        out.append(f'<div class="crit k{" rev" if rev else ""}" style="top:{10 + 80 * (i + .4 + r.random() * .4) / n_k:.1f}%;--t:{r.randint(20, 30)}s;--d:-{r.randint(0, 25)}s;--w:{r.randint(12, 15)}cqw">'
                   f'<div class="bob" style="--b:{r.uniform(1.6, 2.4):.1f}s">{_bird(*c, round(r.uniform(.22, .32), 2))}</div></div>')
    return "".join(out)
def art(kind, fly=(5, 2)):
    sky = '<div class="sky" aria-hidden="true">' + ('<i></i><i></i><i></i><i></i>' if kind in ("day", "haldi") else '') + '</div>'
    head = HALDI_HEAD if kind == "haldi" else ART_HEAD
    foot = "" if kind == "dusk" else ART_FOOT
    extra = {"dusk": SCENE + LANTERNS + '<canvas class="glow" data-kind="fire" aria-hidden="true"></canvas>',
             "night": '<canvas class="glow" data-kind="fly" aria-hidden="true"></canvas>', "haldi": VINES + critters(fly[0], fly[1], 7),
             "day": VINES + HYDRANGEAS + LEAVES + critters(fly[0], fly[1], 3)}.get(kind, "")
    return sky + head + foot + extra
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
GUEST_OPTS = "".join(f'<option value="{i}">{i}</option>' for i in range(1, 11))
def evcheck(i, val, label, date):
    return (f'<label class="chip" for="ev-{i}"><input id="ev-{i}" type="checkbox" name="events" value="{val}" checked>'
            f'<span class="box" aria-hidden="true"></span><span class="lbl">{label}</span><span class="dt">{date}</span></label>')
EXTRA_SECTIONS = f"""
<section class="web theme-day" id="venues" aria-labelledby="venues-h"><canvas class="petals" data-n="7" aria-hidden="true"></canvas><div class="col">{art("day")}<div class="frame">
  <p class="label">Where we celebrate</p>
  <h2 id="venues-h">Come Celebrate With Us</h2>
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
  {DIV}
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
<section class="web theme-night" id="rsvp" aria-labelledby="rsvp-h"><canvas class="petals" data-n="6" aria-hidden="true"></canvas><div class="col">{art("night")}<div class="frame">
  <p class="label" id="rsvp-h">Kindly RSVP</p>
  <p class="lead">We would love to know if you can join us.</p>
  <aside class="rsvp-contact" aria-labelledby="rsvp-contact-h">
    <h3 id="rsvp-contact-h"><span>📞 Questions?</span><span>Get in touch!</span></h3>
    <ul class="rsvp-contact-grid">
      <li><span>Madhur</span><a href="tel:+919452730775">+91-9452730775</a></li>
      <li><span>Santosh Gupta</span><a href="tel:+91945004128">+91-9450040128</a></li>
      <li><span>Soumya</span><a href="tel:+917674981551">+91-7674981551</a></li>
      <li><span>Umakant Gupta</span><a href="tel:+918500669671">+91-8500669671</a></li>
    </ul>
  </aside>
  {DIV}
  <form id="rsvp-form" autocomplete="off" novalidate>
    <div class="f"><label for="rsvp-name">Your name</label>
      <input id="rsvp-name" name="name" type="text" autocomplete="off" placeholder="Full name" aria-describedby="rsvp-name-error" required>
      <p class="err field-err" id="rsvp-name-error" role="alert" hidden></p></div>
    <div class="f"><label for="rsvp-phone">Mobile number</label>
      <input id="rsvp-phone" name="phone" type="tel" autocomplete="off" inputmode="numeric" placeholder="10-digit mobile" aria-describedby="rsvp-phone-error" required>
      <p class="err field-err" id="rsvp-phone-error" role="alert" hidden></p></div>
    <fieldset class="f" id="rsvp-attending" aria-describedby="rsvp-attending-error"><legend>Will you join us?</legend>
      <div class="choices">
        <label class="pill"><input id="rsvp-yes" type="radio" name="attending" value="Joyfully attending" checked required><span>Joyfully attending</span></label>
        <label class="pill"><input id="rsvp-no" type="radio" name="attending" value="Regretfully unable"><span>Regretfully unable</span></label>
      </div><p class="err field-err" id="rsvp-attending-error" role="alert" hidden></p></fieldset>
    <div id="rsvp-more">
      <div class="f"><label for="rsvp-guests">Number of guests, including you</label>
        <select id="rsvp-guests" name="guests">{GUEST_OPTS}</select></div>
      <fieldset class="f" id="rsvp-events" aria-describedby="rsvp-events-error"><legend>Which events will you attend?</legend>
        <div class="checks">
          {evcheck("tilak", "Tilak", "Tilak", "24 Nov")}
          {evcheck("sangeet", "Engagement &amp; Sangeet", "Engagement &amp; Sangeet", "24 Nov")}
          {evcheck("haldi", "Haldi &amp; Mehendi", "Haldi &amp; Mehendi", "25 Nov")}
          {evcheck("baraat", "Baraat", "Baraat", "25 Nov")}
          {evcheck("jaimala", "Jaimala", "Jaimala", "25 Nov")}
        </div><p class="err field-err" id="rsvp-events-error" role="alert" hidden></p></fieldset>
      <div class="f"><label for="rsvp-travel">Tell us about your arrival &amp; departure <small>(optional)</small></label>
        <textarea id="rsvp-travel" name="travel" rows="3" placeholder="Let us know when you plan to arrive and leave. You can also share your train/flight details or any travel arrangements we should know about."></textarea></div>
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
<section class="web theme-day" id="blessings" aria-labelledby="bless-h"><canvas class="petals" data-n="9" aria-hidden="true"></canvas><div class="col">{art("day", (9, 4))}<div class="frame">
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
<section class="web theme-haldi" id="blessings-groom" aria-labelledby="bless-g-h"><canvas class="petals" data-n="8" aria-hidden="true"></canvas><div class="col">{art("haldi", (7, 3))}<div class="frame">
  <p class="label">With blessings of</p>
  <h2 id="bless-g-h">The Groom’s Family</h2>
  {DIV}
  <div class="sides">{side("Groom’s Side", groom, "groom")}</div>
</div></div></section>
"""

_i_rsvp = EXTRA_SECTIONS.index('<section class="web theme-night" id="rsvp"')
_i_bless = EXTRA_SECTIONS.index('<section class="web theme-day" id="blessings" ')
_VENUES, _RSVP, _BLESSINGS = EXTRA_SECTIONS[:_i_rsvp], EXTRA_SECTIONS[_i_rsvp:_i_bless], EXTRA_SECTIONS[_i_bless:]

# ---------- assemble ----------
used_glyphs = set()
sections = []
for P in model:
    tu = P["_text_uses"]
    used_glyphs.update(u["g"] for u in tu)
    plain = P.get("_plain") or P["_plain_list"]
    label = {1: "Cover", 2: "Families", 8: "Closing"}.get(P["n"], "Event")
    event_page = P["n"] in range(3, 8)
    svg = (f'<svg class="pg" viewBox="0 0 810 1440" role="img" aria-label="{html.escape(" ".join(plain) or "Soumya and Madhur monogram")}">'
           + "".join(P["_body"])
           + ('<g class="event-title">' + "".join(use_svg(u) for u in tu if u.get("title")) + '</g>' if event_page else '')
           + '<g class="rv rv1">' + "".join(use_svg(u) for u in tu if (not (event_page and u.get("title"))) and (u.get("title") or (P["n"] in (1, 2) and u.get("scale", 1) * u["size"] > 40))) + '</g>'
           + '<g class="rv rv2">' + "".join(use_svg(u) for u in tu if not (u.get("title") or (P["n"] in (1, 2) and u.get("scale", 1) * u["size"] > 40))) + '</g>'
           + '<g class="rv rv3">' + "".join(P["_extra"]) + '</g>'
           + ('<canvas class="petals" aria-hidden="true"></canvas>' if False else '')
           + "</svg>")
    if P["n"] == 8:     # venues, the two blessings pages and the RSVP come before the closing page, which stays last
        sections.append(_VENUES + _BLESSINGS + _RSVP)
    petals = ('<canvas class="petals" data-candles="true" aria-hidden="true"></canvas>'
              if P["n"] == 7 else '<canvas class="petals" aria-hidden="true"></canvas>')
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
@media (prefers-reduced-motion: reduce) {{ html {{ scroll-behavior: auto; }} .open text, .open .chev {{ animation: none !important; }} }}
.fluid-bg {{ position: fixed; inset: 0; z-index: 0; overflow: hidden; pointer-events: none;
  background: linear-gradient(116deg, var(--fluid-a, #f3e2d2) 0%, var(--fluid-base, #d7e9ef) 48%, var(--fluid-b, #15264b) 100%); }}
.fluid-bg .flow-lines {{ position: absolute; inset: -4%; width: 108%; height: 108%; overflow: visible; }}
.flow-lines .flow-set {{ transform-box: fill-box; transform-origin: center; will-change: transform; }}
.flow-lines .flow-set-a {{ animation: current-a 24s ease-in-out infinite alternate; }}
.flow-lines .flow-set-b {{ animation: current-b 29s ease-in-out infinite alternate; }}
.flow-lines .flow-set-c {{ animation: current-c 26s ease-in-out infinite alternate; }}
.flow-lines .current {{ fill: none; stroke-width: 1.2; stroke-linecap: round; opacity: .46; }}
.flow-lines .current-a {{ stroke: url(#metal-gold); }}
.flow-lines .current-b {{ stroke: url(#metal-blue); }}
.flow-lines .current-c {{ stroke: url(#metal-rose); }}
.flow-lines .glint {{ fill: none; stroke: url(#metal-glint); stroke-width: 1.5; stroke-linecap: round;
  stroke-dasharray: 240 2600; stroke-dashoffset: 0; opacity: .88; will-change: stroke-dashoffset; }}
.flow-lines .flow-set-a .glint {{ animation: glint-a 14s linear infinite; }}
.flow-lines .flow-set-b .glint {{ animation: glint-b 16s linear infinite; }}
.flow-lines .flow-set-c .glint {{ animation: glint-c 15s linear infinite; }}
@keyframes current-a {{ from {{ transform: translate(-3%, -4%); }} to {{ transform: translate(3%, 4%); }} }}
@keyframes current-b {{ from {{ transform: translate(3.5%, 3%); }} to {{ transform: translate(-3.5%, -3%); }} }}
@keyframes current-c {{ from {{ transform: translate(-3%, 3.5%); }} to {{ transform: translate(3%, -3.5%); }} }}
@keyframes glint-a {{ to {{ stroke-dashoffset: -2840; }} }}
@keyframes glint-b {{ to {{ stroke-dashoffset: -2840; }} }}
@keyframes glint-c {{ to {{ stroke-dashoffset: -2840; }} }}
.fluid-bg .sparkle {{ position: absolute; width: 11px; height: 11px; border-radius: 50%;
  background: radial-gradient(circle, #fff9df 0 14%, #f5d27d 22%, rgba(229,181,91,.25) 44%, transparent 72%);
  opacity: 0; animation: fluid-sparkle 5.8s ease-in-out infinite; will-change: transform, opacity; }}
.fluid-bg .sparkle::before, .fluid-bg .sparkle::after {{ content: ""; position: absolute; left: 48%; top: -72%; width: 1px; height: 244%;
  background: linear-gradient(transparent, rgba(255,246,207,.9), transparent); }}
.fluid-bg .sparkle::after {{ transform: rotate(90deg); }}
.fluid-bg .sparkle.s1 {{ left: 13%; top: 24%; animation-delay: -1.2s; }}
.fluid-bg .sparkle.s2 {{ left: 31%; top: 67%; animation-delay: -3.8s; }}
.fluid-bg .sparkle.s3 {{ left: 48%; top: 18%; animation-delay: -2.4s; }}
.fluid-bg .sparkle.s4 {{ left: 63%; top: 72%; animation-delay: -.6s; }}
.fluid-bg .sparkle.s5 {{ left: 78%; top: 35%; animation-delay: -4.6s; }}
.fluid-bg .sparkle.s6 {{ left: 89%; top: 61%; animation-delay: -2.9s; }}
@keyframes fluid-sparkle {{ 0%, 100% {{ opacity: 0; transform: scale(.5); }} 32%, 58% {{ opacity: .8; transform: scale(1.15); }} 76% {{ opacity: .18; transform: scale(.8); }} }}
@media (prefers-reduced-motion: reduce) {{ .flow-lines .flow-set, .flow-lines .glint, .fluid-bg .sparkle {{ animation: none !important; }} .flow-lines .glint, .fluid-bg .sparkle {{ display: none; }} }}
.page {{ height: 100vh; height: 100svh; display: grid; place-items: center; scroll-snap-align: start; overflow: hidden; }}
.pg {{ display: block; height: min(100svh, calc(100vw * 16 / 9)); width: auto; aspect-ratio: 9 / 16; }}
@media (max-aspect-ratio: 9/16) {{ .page {{ height: calc(100vw * 16 / 9); }} }}
/* ---------- animation ---------- */
.page, .web {{ position: relative; z-index: 1; }}
.petals {{ position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; z-index: 2; }}
.js .page .rv {{ opacity: 0; transform: translateY(14px); transform-box: fill-box; }}
.js .page.seen .rv {{ animation: rise 1s cubic-bezier(.2,.7,.2,1) forwards; }}
.js .page.seen .rv2 {{ animation-delay: .35s; }}
.js .page.seen .rv3 {{ animation-delay: .6s; }}
.js .web .frame > * {{ opacity: 0; transform: translateY(16px); }}
.js .web.seen .frame > * {{ animation: rise .9s cubic-bezier(.2,.7,.2,1) forwards; }}
.js .web.seen .frame > *:nth-child(2) {{ animation-delay: .1s; }}
.js .web.seen .frame > *:nth-child(3) {{ animation-delay: .2s; }}
.js .web.seen .frame > *:nth-child(n+4) {{ animation-delay: .3s; }}
@keyframes rise {{ to {{ opacity: 1; transform: none; }} }}
/* envelope intro */
.intro {{ position: fixed; inset: 0; z-index: 50; display: none; place-items: center; align-content: center; gap: 22px;
  background: radial-gradient(120% 80% at 50% 40%, #fdf5ef 0%, #f3e2d2 100%); }}
.js .intro {{ display: grid; }}
.intro.gone {{ opacity: 0; visibility: hidden; transition: opacity .6s ease, visibility .6s; }}
.env {{ position: relative; width: min(78vw, 400px); aspect-ratio: 7 / 5; perspective: 1600px; }}
.env > * {{ will-change: transform, opacity; backface-visibility: hidden; }}
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
.intro-to {{ margin: 0; max-width: min(84vw, 420px); text-align: center; font-family: "Crimson Text", Georgia, serif; font-style: italic; color: #b85c1d; font-size: clamp(22px, 6.4vw, 30px); line-height: 1.2; letter-spacing: .03em; overflow-wrap: anywhere; }}
.intro-hint {{ margin: 0; font-family: "Crimson Text", Georgia, serif; font-style: italic; color: #784646; font-size: 18px; letter-spacing: .04em; }}
.intro-skip {{ position: absolute; left: max(16px, env(safe-area-inset-left, 0px)); right: auto; bottom: calc(16px + env(safe-area-inset-bottom, 0px));
  background: none; border: 0; color: #784646; font: italic 16px "Crimson Text", Georgia, serif; text-decoration: underline; cursor: pointer; padding: 8px; }}
.music-toggle {{ position: fixed; right: max(16px, env(safe-area-inset-right, 0px)); bottom: calc(16px + env(safe-area-inset-bottom, 0px)); z-index: 70;
  padding: 9px 14px; border: 1px solid rgba(120,70,70,.45); border-radius: 999px; background: rgba(253,245,239,.94);
  color: #784646; box-shadow: 0 3px 12px rgba(90,40,20,.14); font: 15px "Crimson Text", Georgia, serif; cursor: pointer; }}
.music-toggle:hover {{ background: #f3e2d2; }}
.music-toggle:focus-visible {{ outline: 2px solid #b85c1d; outline-offset: 3px; }}
.burst {{ position: fixed; inset: 0; width: 100%; height: 100%; pointer-events: none; z-index: 5; }}
.fly-logo {{ position: fixed; z-index: 60; margin: 0; pointer-events: none; transform-origin: 0 0; will-change: transform, opacity; }}
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
#cover-guest {{ display: none; }}
.open text {{ animation: breathe 2.4s ease-in-out infinite; }}
.open .chev {{ animation: nudge 1.6s ease-in-out infinite; }}
@keyframes breathe {{ 0%, 100% {{ opacity: .7; }} 50% {{ opacity: 1; }} }}
@keyframes nudge {{ 0%, 100% {{ transform: translateY(0); opacity: .75; }} 50% {{ transform: translateY(9px); opacity: 1; }} }}
/* website sections: the same look as the cards. The card's own sky, garland and flowers sit behind
   the text; type is Crimson in the card colours (var(--ink) brown, var(--accent) rust); no panels, no coloured backgrounds */
.web {{ position: relative; display: flex; justify-content: center; scroll-snap-align: start; color: var(--ink); overflow: hidden; }}
.web .col {{ position: relative; z-index: 1; container-type: inline-size; width: min(100vw, calc(100svh * 9 / 16)); box-sizing: border-box;
  min-height: min(100svh, calc(100vw * 16 / 9)); display: flex; overflow: hidden; }}
.web .sky {{ position: absolute; inset: 0; z-index: 0; overflow: hidden; }}
.web .sky i {{ display: block; width: 100%; aspect-ratio: 941 / 1672; background: url("images/{SKY}") 0 0 / 100% 100% no-repeat; }}
.web .sky i:nth-child(even) {{ transform: scaleY(-1); }}
.web .head, .web .foot {{ position: absolute; left: 0; width: 100%; height: auto; display: block; pointer-events: none; z-index: 1; }}
.web .head {{ top: 0; }} .web .foot {{ bottom: 0; }}
.web .frame {{ position: relative; z-index: 2; flex: 1; box-sizing: border-box; padding: 41cqw 10cqw 50cqw; text-align: center;
  font-family: "Crimson Text", Georgia, serif; font-size: 4.6cqw; line-height: 1.45; display: flex; flex-direction: column; gap: 4cqw;
  text-shadow: var(--shadow); }}
.web form, .web .btn {{ text-shadow: none; }}
.web .label {{ margin: 0; font-size: 4cqw; letter-spacing: .2em; text-transform: uppercase; color: var(--ink); font-weight: 600; }}
.web h2 {{ margin: 0; font-weight: 600; font-size: 7.6cqw; line-height: 1.12; color: #d93774; letter-spacing: .05em; text-transform: uppercase; text-wrap: balance; }}
.web h3 {{ margin: 0; font-weight: 600; font-size: 6.4cqw; line-height: 1.15; color: var(--accent); letter-spacing: .06em; text-transform: uppercase; }}
.web .lead {{ margin: 0 auto; max-width: 30em; font-weight: 600; font-size: 4.6cqw; letter-spacing: .02em; text-wrap: balance; }}
.web .divider {{ display: flex; align-items: center; gap: 3cqw; margin: 1cqw 0; }}
.web .divider span {{ flex: 1; height: 1px; background: linear-gradient(90deg, transparent, var(--gold), transparent); }}
.web .divider img {{ width: 6cqw; height: auto; }}
/* outlined pill, like the cards' GET DIRECTIONS button */
.web .btn {{ display: inline-block; align-self: center; padding: 2.6cqw 7cqw; border-radius: 999px; border: 1.6px solid var(--ink); cursor: pointer;
  background: transparent; color: var(--ink); text-decoration: none; font: 600 4.2cqw/1.2 "Crimson Text", Georgia, serif; letter-spacing: .12em;
  text-transform: uppercase; }}
.web .btn:hover {{ background: var(--hover); }}
.web .btn:focus-visible {{ outline: 3px solid var(--accent); outline-offset: 3px; }}
.web .btn.wide {{ padding: 3.4cqw 9cqw; font-size: 4.4cqw; }}
/* countdown */
.web .count {{ display: grid; grid-template-columns: repeat(4, 1fr); margin-top: 1cqw; }}
.web .count div {{ display: grid; gap: .4cqw; padding: 1cqw 0; }}
.web .count div + div {{ border-left: 1px solid var(--gold); }}
.web .count b {{ font-weight: 600; font-size: 10cqw; line-height: 1; color: var(--accent); font-variant-numeric: tabular-nums; }}
.web .count span {{ font-size: 3.3cqw; letter-spacing: .18em; text-transform: uppercase; font-weight: 600; }}
.web .count-note {{ margin: 0; font-weight: 600; font-size: 4.6cqw; }}
/* venues */
.web .tile {{ display: flex; flex-direction: column; gap: 2.6cqw; text-align: center; }}
.web .band {{ margin: 0; font-weight: 600; font-size: 4.4cqw; letter-spacing: .06em; color: var(--ink); }}
.web .tile-body {{ display: flex; flex-direction: column; gap: 2.6cqw; }}
.web .addr {{ margin: 0; font-weight: 600; font-size: 4.6cqw; letter-spacing: .03em; }}
.web .events {{ list-style: none; margin: 1cqw 0 2cqw; padding: 0; display: grid; gap: 1.8cqw; }}
.web .events li {{ display: flex; align-items: baseline; justify-content: center; gap: 2.6cqw; }}
.web .events .n {{ font-weight: 600; font-size: 4.8cqw; letter-spacing: .03em; }}
.web .events .t {{ font-size: 4.6cqw; color: var(--accent2); font-weight: 600; font-variant-numeric: tabular-nums; white-space: nowrap; }}
.web .events .n::after {{ content: "\\2022"; margin-left: 2.6cqw; color: var(--gold); font-style: normal; }}
/* RSVP form */
.web form {{ display: flex; flex-direction: column; gap: 5cqw; text-align: left; }}
.web .rsvp-contact {{ padding: 4cqw; border: 1px solid var(--line); border-radius: 2.5cqw; background: var(--field2); }}
.web .rsvp-contact h3 {{ display: flex; flex-direction: column; gap: .8cqw; margin: 0 0 3cqw; font-size: 4.8cqw; color: var(--ink); }}
.web .rsvp-contact-grid {{ list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: 1fr 1fr; gap: 3cqw 2cqw; }}
.web .rsvp-contact-grid li {{ display: flex; flex-direction: column; gap: .8cqw; min-width: 0; font-size: 3.8cqw; }}
.web .rsvp-contact-grid a {{ color: var(--accent2); font-size: 3.9cqw; font-weight: 600; white-space: nowrap; text-underline-offset: .25em; }}
.web .f {{ display: grid; gap: 2cqw; border: 0; padding: 0; margin: 0; min-width: 0; }}
.web .f label, .web legend {{ font-size: 4.2cqw; font-weight: 600; letter-spacing: .04em; color: var(--ink); padding: 0; }}
.web .f small {{ font-weight: 400; font-style: italic; letter-spacing: 0; }}
.web input[type=text], .web input[type=tel], .web textarea, .web select {{
  font: inherit; font-size: max(16px, 4.6cqw); color: var(--field-ink); background: var(--field); box-sizing: border-box; width: 100%;
  border: 1.4px solid var(--line); border-radius: 2.4cqw; padding: 3cqw 3.6cqw; }}
.web select {{ width: 40%; appearance: none; -webkit-appearance: none; cursor: pointer;
  background: var(--field) linear-gradient(45deg, transparent 50%, var(--accent) 50%) right 5.4cqw center / 1.6cqw 1.6cqw no-repeat,
              linear-gradient(-45deg, transparent 50%, var(--accent) 50%) right 3.8cqw center / 1.6cqw 1.6cqw no-repeat; }}
.web ::placeholder {{ color: var(--ph); font-style: italic; }}
.web input:focus, .web textarea:focus, .web select:focus {{ outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px rgba(184,92,29,.2); }}
.web textarea {{ resize: vertical; min-height: 24cqw; }}
.web .choices {{ display: grid; grid-template-columns: 1fr 1fr; gap: 2.6cqw; }}
.web .pill {{ position: relative; display: block; }}
.web .pill input {{ position: absolute; opacity: 0; inset: 0; margin: 0; cursor: pointer; }}
.web .pill span {{ display: grid; place-items: center; min-height: 13cqw; padding: 2cqw; text-align: center; box-sizing: border-box;
  border: 1.4px solid var(--line); border-radius: 999px; background: transparent; font-size: 4.3cqw; font-weight: 600; letter-spacing: 0; color: var(--ink); }}
.web .pill input:checked + span {{ background: var(--ink); border-color: var(--ink); color: var(--paper); }}
.web .pill input:focus-visible + span {{ outline: 3px solid var(--accent); outline-offset: 2px; }}
.web .checks {{ display: grid; gap: 2.2cqw; }}
.web .f .chip {{ position: relative; display: flex !important; align-items: center; gap: 3cqw; padding: 2.8cqw 3.6cqw; cursor: pointer;
  border: 1.2px solid var(--line2); border-radius: 999px; background: transparent; letter-spacing: 0 !important; }}
.web .chip input {{ position: absolute; opacity: 0; width: 1px; height: 1px; }}
.web .chip .box {{ flex: none; width: 5.4cqw; height: 5.4cqw; border-radius: 50%; border: 1.4px solid var(--accent); display: grid; place-items: center; background: transparent; }}
.web .chip input:checked ~ .box {{ background: var(--accent); }}
.web .chip input:checked ~ .box::after {{ content: ""; width: 1.5cqw; height: 2.8cqw; border: solid var(--paper); border-width: 0 .6cqw .6cqw 0; transform: translateY(-.3cqw) rotate(45deg); }}
.web .chip:has(input:checked) {{ border-color: var(--accent); background: var(--field2); }}
.web .chip input:focus-visible ~ .box {{ outline: 3px solid var(--ink); outline-offset: 2px; }}
.web .chip .lbl {{ flex: 1; min-width: 0; font-size: 4.6cqw; font-weight: 600; }}
.web .chip .dt {{ font-size: 3.8cqw; font-style: italic; color: var(--accent); font-weight: 600; }}
.web .err {{ margin: 0; padding: 3cqw 3.6cqw; border-radius: 2cqw; background: rgba(253,232,228,.85); color: #a3261a; font-size: 4.2cqw; font-style: italic; }}
.web .field-err {{ margin: 1.5cqw 0 0; padding: 0 1cqw; background: transparent; font-size: 3.8cqw; }}
.web .done {{ display: flex; flex-direction: column; gap: 3cqw; padding: 8cqw 0; outline: none; }}
.web .done h3 {{ font-size: 8.8cqw; }}
#rsvp-more {{ display: flex; flex-direction: column; gap: 5cqw; }}
/* blessings */
.web .hosts-box {{ display: flex; flex-direction: column; gap: 2.4cqw; }}
.web .hosts {{ margin: 0; font-weight: 600; font-size: 8cqw; line-height: 1.2; color: var(--ink); display: flex; flex-direction: column; align-items: center; }}
.web .hosts span {{ font-size: .6em; color: var(--accent); }}
.web .sides {{ display: grid; gap: 5cqw; margin-top: 1cqw; }}
.web .side .band {{ font-size: 4.4cqw; font-weight: 600; letter-spacing: .2em; text-transform: uppercase; color: var(--accent); margin-bottom: 3cqw; }}
.web .side dl {{ margin: 0; padding: 0; display: grid; gap: 3.6cqw; }}
.web .rel {{ display: grid; gap: 1cqw; padding-bottom: 3.6cqw; border-bottom: 1px solid transparent;
  border-image: linear-gradient(90deg, transparent, var(--gold), transparent) 1; }}
.web .rel:last-child {{ border-bottom: 0; padding-bottom: 0; }}
.web dt {{ color: var(--accent2); font-size: 3.8cqw; font-weight: 600; letter-spacing: .18em; text-transform: uppercase; }}
.web dd {{ margin: 0; font-size: 4.7cqw; line-height: 1.4; font-weight: 600; letter-spacing: .02em; }}
/* one palette per section, taken from the cards: day sky (Tilak), starry night (Engagement), sunset (Jaimala), marigold (Haldi) */
.theme-day {{ --ink: #8a3340; --accent: #e65a0f; --accent2: #c9470a; --gold: #f0ae1c; --paper: #fdf5ef; --line: rgba(120,70,70,.6); --line2: rgba(120,70,70,.4);
  --hover: rgba(120,70,70,.12); --field: rgba(255,255,255,.55); --field2: rgba(255,255,255,.4); --field-ink: #4f2c2c; --ph: rgba(120,70,70,.6);
  --shadow: 0 0 1.4cqw rgba(253,245,239,.95), 0 0 .5cqw rgba(253,245,239,.9); }}
.theme-night {{ --ink: #fffaf2; --accent: #ffe066; --accent2: #ffe066; --gold: #f7cc55; --paper: #0f1d40; --line: rgba(247,215,122,.7); --line2: rgba(247,215,122,.4);
  --hover: rgba(247,215,122,.16); --field: rgba(255,255,255,.1); --field2: rgba(255,255,255,.1); --field-ink: #fdf5ef; --ph: rgba(253,245,239,.55);
  --shadow: 0 0 1.4cqw rgba(6,15,38,.9), 0 0 .5cqw rgba(6,15,38,.8); }}
.theme-dusk {{ --ink: #fff3ea; --accent: #ffd98a; --accent2: #ffd98a; --gold: #f0b95a; --paper: #32145e; --line: rgba(255,217,138,.75); --line2: rgba(255,217,138,.45);
  --hover: rgba(255,217,138,.18); --field: rgba(255,255,255,.12); --field2: rgba(255,255,255,.1); --field-ink: #fff3ea; --ph: rgba(255,243,234,.6);
  --shadow: 0 0 1.4cqw rgba(50,10,70,.9), 0 0 .5cqw rgba(50,10,70,.85); }}
.theme-haldi {{ --ink: #6b3510; --accent: #dd3510; --accent2: #b82a0a; --gold: #e0a80a; --paper: #fff6d6; --line: rgba(94,52,16,.55); --line2: rgba(94,52,16,.35);
  --hover: rgba(94,52,16,.12); --field: rgba(255,251,230,.65); --field2: rgba(255,251,230,.5); --field-ink: #3b200a; --ph: rgba(94,52,16,.55);
  --shadow: 0 0 1.4cqw rgba(255,246,205,.95), 0 0 .5cqw rgba(255,246,205,.9); }}
.theme-night .sky {{ background: linear-gradient(180deg, #0a1431 0%, #12234a 40%, #1d2f5c 72%, #2a3d70 100%); }}
.theme-dusk .sky {{ background: linear-gradient(180deg, #e13db0 0%, #b5329a 25%, #8a2686 50%, #5e1c73 75%, #32145e 100%); }}
.web .glow {{ position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; z-index: 1; }}
.web .scene {{ position: absolute; left: 0; bottom: 0; width: 100%; height: auto; display: block; pointer-events: none; z-index: 1; }}
.web .flame {{ transform-box: fill-box; transform-origin: 50% 100%; animation: flicker 1.7s ease-in-out infinite; }}
.web .flame.f2 {{ animation-duration: 1.3s; animation-delay: -.4s; }} .web .flame.f3 {{ animation-duration: 2.1s; animation-delay: -.9s; }}
.web .halo {{ animation: halo 2.2s ease-in-out infinite; }}
@keyframes flicker {{ 0%, 100% {{ transform: scale(1, 1) rotate(-1.5deg); }} 30% {{ transform: scale(.92, 1.08) rotate(2deg); }} 60% {{ transform: scale(1.06, .94) rotate(-2deg); }} }}
@keyframes halo {{ 0%, 100% {{ opacity: .5; }} 50% {{ opacity: .85; }} }}
@media (prefers-reduced-motion: reduce) {{ .web .flame, .web .halo {{ animation: none; }} }}
.web .lantern {{ position: absolute; height: auto; display: block; pointer-events: none; z-index: 1; overflow: visible; opacity: .92;
  animation: bob 5.5s ease-in-out infinite; transform-origin: 50% 0; filter: drop-shadow(0 0 1.6cqw rgba(255,170,60,.7)); }}
.web .lantern.l2 {{ animation-duration: 6.6s; animation-delay: -1.8s; }} .web .lantern.l3 {{ animation-duration: 5s; animation-delay: -3s; }}
.web .lantern.l4 {{ animation-duration: 7s; animation-delay: -.8s; }} .web .lantern.l5 {{ animation-duration: 6s; animation-delay: -2.4s; }}
@keyframes bob {{ 0%, 100% {{ transform: translateY(0) rotate(-2.5deg); }} 50% {{ transform: translateY(-2.4cqw) rotate(2.5deg); }} }}
@media (prefers-reduced-motion: reduce) {{ .web .lantern {{ animation: none; }} }}
.web .vine {{ position: absolute; width: 24cqw; height: auto; pointer-events: none; z-index: 1; }}
.web .vine.va {{ left: -9cqw; top: 22%; transform: rotate(70deg); }} .web .vine.vb {{ right: -9cqw; top: 34%; transform: scaleX(-1) rotate(70deg); }}
.web .vine.vc {{ left: -10cqw; top: 50%; transform: rotate(110deg); }} .web .vine.vd {{ right: -10cqw; top: 62%; transform: scaleX(-1) rotate(110deg); }}
.web .vine.ve {{ left: -9cqw; top: 76%; transform: rotate(80deg); }} .web .vine.vf {{ right: -9cqw; top: 86%; transform: scaleX(-1) rotate(80deg); }}
.web .hyd {{ position: absolute; width: 28cqw; height: auto; pointer-events: none; z-index: 1; }}
.web .hyd.ha {{ left: -12cqw; top: 40%; transform: rotate(20deg); }} .web .hyd.hb {{ right: -13cqw; top: 54%; transform: scaleX(-1) rotate(-15deg); }} .web .hyd.hc {{ left: -11cqw; top: 67%; transform: rotate(-10deg); }}
.web .leaf {{ position: absolute; width: 20cqw; height: auto; pointer-events: none; z-index: 1; }}
.web .leaf.la {{ right: -6cqw; top: 14%; transform: scaleX(-1) rotate(30deg); }} .web .leaf.lb {{ left: -6cqw; top: 31%; transform: rotate(-25deg); }}
.web .leaf.lc {{ right: -7cqw; top: 46%; transform: scaleX(-1) rotate(10deg); }} .web .leaf.ld {{ left: -7cqw; top: 58%; transform: rotate(35deg); }}
.web .crit {{ position: absolute; left: 0; width: var(--w); pointer-events: none; z-index: 1; animation: cross var(--t) linear var(--d) infinite; }}
.web .crit.rev {{ animation-direction: reverse; }} .web .crit.rev svg {{ transform: scaleX(-1); }}
.web .crit svg {{ display: block; width: 100%; height: auto; overflow: visible; filter: drop-shadow(0 .6cqw .8cqw rgba(60,40,20,.25)); }}
.web .crit .bob {{ animation: bob2 var(--b) ease-in-out infinite alternate; }}
.web .wl, .web .wr {{ transform-origin: 30px 26px; animation: flap var(--f, .32s) ease-in-out infinite alternate; }}
.web .bw {{ transform-origin: 36px 26px; animation: wing var(--f, .26s) ease-in-out infinite alternate; }}
@keyframes cross {{ from {{ transform: translateX(-22cqw); }} to {{ transform: translateX(118cqw); }} }}
@keyframes bob2 {{ from {{ transform: translateY(-2.4cqw) rotate(-3deg); }} to {{ transform: translateY(2.4cqw) rotate(3deg); }} }}
@keyframes flap {{ from {{ transform: scaleX(1); }} to {{ transform: scaleX(.2); }} }}
@keyframes wing {{ from {{ transform: rotate(-24deg); }} to {{ transform: rotate(26deg); }} }}
@media (prefers-reduced-motion: reduce) {{ .web .crit {{ display: none; }} }}
/* the venues and both blessings pages: body text in Crimson italic, like the venue lines on the Baraat and Jaimala cards */
:is(#venues, #blessings, #blessings-groom) :is(.lead, .addr, .count-note, dd, .hosts, .events .t) {{ font-style: italic; font-weight: 400; letter-spacing: .015em; }}
:is(#venues, #blessings, #blessings-groom) :is(.lead, .addr, .count-note) {{ font-size: 4.9cqw; }}
:is(#venues, #blessings, #blessings-groom) dd {{ font-size: 5cqw; }}
:is(#venues, #blessings, #blessings-groom) .events .t {{ font-size: 4.8cqw; }}
:is(#venues, #blessings, #blessings-groom) .hosts {{ font-size: 8.4cqw; }}
/* small headings (labels, day lines, relation tags, countdown captions) in the card's night blue: strong contrast on the sky */
:is(#venues, #blessings, #blessings-groom) :is(.label, .band, dt, .count span) {{ color: #1d2f5c; }}
/* no orange on these three pages: venue names, numbers and times in deep purple, lines and dots in pink */
#venues, #blessings, #blessings-groom {{ --accent: #5a2d8a; --accent2: #5a2d8a; --gold: #d9468a; }}
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
  <p class="intro-to" id="intro-to" hidden></p>
  <p class="intro-hint">Tap the seal to open</p>
  <button class="intro-skip" id="intro-skip" type="button">Skip</button>
</div>
<button class="music-toggle" id="music-toggle" type="button" aria-label="Mute music" aria-pressed="false">♪ Sound on</button>
<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>{defs}</defs></svg>
<div class="fluid-bg" aria-hidden="true"><svg class="flow-lines" viewBox="0 0 1600 900" preserveAspectRatio="none">
  <defs>
    <linearGradient id="metal-gold" x1="0" y1="0" x2="1" y2=".2"><stop stop-color="#b57c3d" stop-opacity=".12"/><stop offset=".22" stop-color="#fff0c2" stop-opacity=".76"/><stop offset=".38" stop-color="#d8a452" stop-opacity=".72"/><stop offset=".53" stop-color="#fffdf2" stop-opacity=".84"/><stop offset=".7" stop-color="#c58c49" stop-opacity=".66"/><stop offset=".86" stop-color="#f8e4ae" stop-opacity=".72"/><stop offset="1" stop-color="#fff9e8" stop-opacity=".14"/></linearGradient>
    <linearGradient id="metal-blue" x1="0" y1=".2" x2="1" y2=".7"><stop stop-color="#c5e8f5" stop-opacity=".12"/><stop offset=".2" stop-color="#fff" stop-opacity=".72"/><stop offset=".38" stop-color="#a6c9db" stop-opacity=".68"/><stop offset=".56" stop-color="#f5dfb3" stop-opacity=".82"/><stop offset=".74" stop-color="#bddbea" stop-opacity=".74"/><stop offset="1" stop-color="#fff" stop-opacity=".12"/></linearGradient>
    <linearGradient id="metal-rose" x1="0" y1=".7" x2="1" y2=".1"><stop stop-color="#d49b75" stop-opacity=".1"/><stop offset=".24" stop-color="#fff2d0" stop-opacity=".78"/><stop offset=".43" stop-color="#dcaa79" stop-opacity=".7"/><stop offset=".58" stop-color="#fff" stop-opacity=".84"/><stop offset=".78" stop-color="#d4b8ae" stop-opacity=".68"/><stop offset="1" stop-color="#fff2d7" stop-opacity=".12"/></linearGradient>
    <linearGradient id="metal-glint" x1="0" y1="0" x2="1" y2="0"><stop stop-color="#fff" stop-opacity="0"/><stop offset=".32" stop-color="#fff9e6" stop-opacity=".6"/><stop offset=".48" stop-color="#fff"/><stop offset=".62" stop-color="#edc56f" stop-opacity=".92"/><stop offset=".8" stop-color="#fff5d7" stop-opacity=".6"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
  </defs>
  <g class="flow-set flow-set-a">
    <path class="current current-a" d="M-100 145 C160 -65 280 400 520 200 S850 15 1090 185 S1440 415 1700 110"/><path class="glint" d="M-100 145 C160 -65 280 400 520 200 S850 15 1090 185 S1440 415 1700 110"/>
    <path class="current current-b" d="M-100 345 C160 600 300 70 590 330 S900 590 1120 280 S1460 70 1700 430"/><path class="glint" d="M-100 345 C160 600 300 70 590 330 S900 590 1120 280 S1460 70 1700 430"/>
    <path class="current current-c" d="M-100 540 C200 250 320 830 610 540 S960 250 1200 570 S1480 900 1700 460"/><path class="glint" d="M-100 540 C200 250 320 830 610 540 S960 250 1200 570 S1480 900 1700 460"/>
  </g>
  <g class="flow-set flow-set-b">
    <path class="current current-b" d="M-100 70 C190 350 370 -150 620 120 S930 390 1180 70 S1460 -100 1700 250"/><path class="glint" d="M-100 70 C190 350 370 -150 620 120 S930 390 1180 70 S1460 -100 1700 250"/>
    <path class="current current-a" d="M-100 440 C150 160 400 760 640 390 S960 100 1210 480 S1480 760 1700 320"/><path class="glint" d="M-100 440 C150 160 400 760 640 390 S960 100 1210 480 S1480 760 1700 320"/>
    <path class="current current-c" d="M-100 760 C180 500 400 980 650 680 S990 440 1210 800 S1480 1020 1700 590"/><path class="glint" d="M-100 760 C180 500 400 980 650 680 S990 440 1210 800 S1480 1020 1700 590"/>
  </g>
  <g class="flow-set flow-set-c">
    <path class="current current-c" d="M-100 225 C180 -50 360 540 610 210 S920 -50 1160 240 S1460 550 1700 150"/><path class="glint" d="M-100 225 C180 -50 360 540 610 210 S920 -50 1160 240 S1460 550 1700 150"/>
    <path class="current current-a" d="M-100 645 C150 950 360 350 610 680 S950 1030 1190 610 S1470 350 1700 780"/><path class="glint" d="M-100 645 C150 950 360 350 610 680 S950 1030 1190 610 S1470 350 1700 780"/>
  </g>
</svg>
  <i class="sparkle s1"></i><i class="sparkle s2"></i><i class="sparkle s3"></i><i class="sparkle s4"></i><i class="sparkle s5"></i><i class="sparkle s6"></i></div>
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

/* ---------- slow fluid background: continuous palette interpolation with cached section positions ---------- */
(function () {{
  var palettes = {{
    'page-1': ['#f3e2d2', '#e4c9b4', '#fdf5ef'],
    'page-2': ['#83c6f4', '#d8ebef', '#dff0f7'],
    'page-3': ['#83c6f4', '#e1d39c', '#d8edf5'],
    'page-4': ['#102044', '#394a70', '#15264b'],
    'page-5': ['#91d5f2', '#f1cc56', '#e7f1d1'],
    'page-6': ['#101e42', '#586f91', '#192b52'],
    'page-7': ['#e7a0b5', '#c9a2d5', '#eac1c7'],
    'venues': ['#83c6f4', '#d8ebef', '#dff0f7'],
    'blessings': ['#83c6f4', '#e1efcb', '#dff0f7'],
    'blessings-groom': ['#f4dc72', '#ecb847', '#fff0bb'],
    'rsvp': ['#102044', '#394a70', '#15264b'],
    'page-8': ['#a7d8ef', '#f3e2d2', '#e9f4f5']
  }};
  var pages = document.querySelectorAll('.page, .web');
  if (!pages.length) return;
  var bg = document.querySelector('.fluid-bg'), raf = 0, stops = [];
  if (!bg) return;
  function parse(hex) {{ return [parseInt(hex.slice(1, 3), 16), parseInt(hex.slice(3, 5), 16), parseInt(hex.slice(5, 7), 16)]; }}
  function rgb(a, b, t) {{
    return 'rgb(' + Math.round(a[0] + (b[0] - a[0]) * t) + ' ' +
      Math.round(a[1] + (b[1] - a[1]) * t) + ' ' + Math.round(a[2] + (b[2] - a[2]) * t) + ')';
  }}
  function measure() {{
    var y = window.scrollY;
    stops = Array.prototype.map.call(pages, function (page) {{
      return {{ center: page.getBoundingClientRect().top + y + page.offsetHeight * .5,
        colors: (palettes[page.id] || palettes['page-2']).map(parse) }};
    }});
    schedule();
  }}
  function paint() {{
    raf = 0;
    var y = window.scrollY + window.innerHeight * .5, i = 0;
    while (i < stops.length - 1 && y > stops[i + 1].center) i++;
    var left = stops[i], right = stops[Math.min(i + 1, stops.length - 1)];
    var span = right.center - left.center;
    var t = span > 0 ? Math.max(0, Math.min(1, (y - left.center) / span)) : 0;
    ['--fluid-a', '--fluid-b', '--fluid-base'].forEach(function (name, n) {{
      bg.style.setProperty(name, rgb(left.colors[n], right.colors[n], t));
    }});
  }}
  function schedule() {{ if (!raf) raf = requestAnimationFrame(paint); }}
  addEventListener('scroll', schedule, {{ passive: true }});
  addEventListener('resize', measure, {{ passive: true }});
  addEventListener('load', measure, {{ once: true }});
  measure();
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(measure);
}})();


/* ---------- envelope intro: seal -> flap opens -> card rises -> logo glides onto the cover's logo ---------- */
(function () {{
  var intro = document.getElementById('intro'), root = document.documentElement;
  if (!intro) return;
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var $ = function (s) {{ return intro.querySelector(s); }};
  var seal = $('#seal'), flap = $('.env-flap'), letter = $('.env-letter'), logo = $('.env-letter img'), env = $('#env');
  var busy = false, done = false;
  var song = new Audio('audio/chaap-tilak.mp3'), TARGET = 0.65, on = false, fadeId = 0, playId = 0;
  song.loop = true; song.preload = 'auto';
  var musicToggle = document.getElementById('music-toggle');
  function setLabel() {{
    musicToggle.textContent = on ? '♪ Sound on' : '♪ Sound off';
    musicToggle.setAttribute('aria-label', on ? 'Turn the music off' : 'Turn the music on');
    musicToggle.setAttribute('aria-pressed', on ? 'true' : 'false');
  }}
  function fadeVolume(target, then) {{                 /* phones (iOS) ignore volume, so the real on/off is play() and pause() */
    var from = song.volume, started = performance.now(), duration = 400, id = ++fadeId;
    function step(now) {{
      if (id !== fadeId) return;
      var t = Math.min(1, (now - started) / duration);
      try {{ song.volume = from + (target - from) * t; }} catch (e) {{}}
      if (t < 1) requestAnimationFrame(step); else if (then) then();
    }}
    requestAnimationFrame(step);
  }}
  function startSong() {{                              /* always called straight from a tap: iOS and Android only allow play() there */
    var id = ++playId; on = true; setLabel();
    try {{ song.volume = 0; }} catch (e) {{}}
    var pr = song.play();
    if (pr && pr.catch) pr.catch(function (err) {{
      if (id !== playId || (err && err.name === 'AbortError')) return;       /* a newer tap replaced this one: not a failure */
      on = false; setLabel();                          /* the browser refused: show "off" so the next tap tries again */
    }});
    fadeVolume(TARGET);
  }}
  function stopSong() {{
    ++playId; on = false; setLabel();
    fadeVolume(0, function () {{ if (!on) song.pause(); }});
  }}
  /* the phone paused it for us (call, lock screen, another app took the audio): show "off" so one tap resumes it */
  song.addEventListener('pause', function () {{ if (on) {{ on = false; setLabel(); }} }});
  setLabel();
  musicToggle.addEventListener('click', function () {{ if (on) stopSong(); else startSong(); }});
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
    if (!on) startSong();
    if (reduce || !document.body.animate) {{ finish(); return; }}
    var ease = 'cubic-bezier(.45,0,.2,1)';
    anim($('.intro-hint'), [{{ opacity: 1 }}, {{ opacity: 0 }}], {{ duration: 300 }});
    if (!$('.intro-to').hidden) anim($('.intro-to'), [{{ opacity: 1 }}, {{ opacity: 0 }}], {{ duration: 300 }});
    anim($('.intro-skip'), [{{ opacity: 1 }}, {{ opacity: 0 }}], {{ duration: 300 }});
    seal.style.animation = 'none';
    burst();
    anim(seal, [{{ transform: 'translate(-50%,-50%) scale(1)', opacity: 1 }}, {{ transform: 'translate(-50%,-50%) scale(.35)', opacity: 0 }}],
         {{ duration: 420, easing: ease }});
    /* 1. the flap swings open (it moves behind the card halfway, as a real flap would) */
    await anim(flap, [
      {{ transform: 'rotateX(0deg)', zIndex: 3 }},
      {{ transform: 'rotateX(90deg)', zIndex: 3, offset: .5 }},
      {{ transform: 'rotateX(90deg)', zIndex: 0, offset: .5001 }},
      {{ transform: 'rotateX(180deg)', zIndex: 0 }}], {{ duration: 950, delay: 180, easing: 'cubic-bezier(.4,0,.3,1)' }});
    /* 2. the card rises out, showing the logo */
    await anim(letter, [{{ transform: 'translateY(0)' }}, {{ transform: 'translateY(-44%)' }}], {{ duration: 1100, easing: 'cubic-bezier(.22,.8,.3,1)' }});
    await wait(350);
    /* 3. the logo lifts off and glides onto the cover's logo while the envelope fades away */
    var target = coverLogo(), from = logo.getBoundingClientRect();
    var to = target ? target.getBoundingClientRect() : null;
    if (to && to.width) {{
      var fly = logo.cloneNode(); fly.className = 'fly-logo'; fly.alt = '';
      fly.style.left = from.left + 'px'; fly.style.top = from.top + 'px'; fly.style.width = from.width + 'px'; fly.style.height = from.height + 'px';
      document.body.appendChild(fly); logo.style.visibility = 'hidden';
      var k = to.width / from.width;
      var envFade = anim(env, [{{ opacity: 1, transform: 'scale(1)' }}, {{ opacity: 0, transform: 'scale(1.04)' }}], {{ duration: 900, easing: 'ease-in-out' }});
      var bgFade = anim(intro, [{{ opacity: 1 }}, {{ opacity: 0 }}], {{ duration: 1100, delay: 250, easing: 'ease-in-out' }});
      var glide = anim(fly, [{{ transform: 'translate(0,0) scale(1)' }},
        {{ transform: 'translate(' + (to.left - from.left) + 'px,' + (to.top - from.top) + 'px) scale(' + k + ')' }}],
        {{ duration: 1350, easing: 'cubic-bezier(.45,0,.2,1)' }});
      setTimeout(function () {{ var p1 = document.getElementById('page-1'); if (p1) p1.classList.add('seen'); }}, 900);
      await Promise.all([envFade, bgFade, glide]);
      finish();
      /* the flying logo now sits exactly on the cover's own logo; let it melt into it */
      anim(fly, [{{ opacity: 1 }}, {{ opacity: 0 }}], {{ duration: 250 }}).then(function () {{ fly.remove(); }});
    }} else {{
      finish();
    }}
  }}
  seal.addEventListener('click', open);
  env.addEventListener('click', open);
  $('#intro-skip').addEventListener('click', function () {{ if (!on) startSong(); finish(); }});
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
  var candlePoints = [[60,1274],[115,1305],[150,1348],[183,1317],[296,1375],[355,1379],
    [445,1318],[476,1347],[514,1340],[552,1374],[690,1332],[742,1273]];
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
      if (cv.dataset.candles) {{
        var cr = 2.2 * Math.min(1.4, W / 400);
        for (var ci = 0; ci < candlePoints.length; ci++) {{
          var pulse = .5 + .5 * Math.sin(t / 360 + ci * 1.73);
          star(ctx, candlePoints[ci][0] * W / 810, candlePoints[ci][1] * H / 1440,
            cr, .14 + .24 * pulse, GOLD[ci % GOLD.length]);
        }}
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
    guests: "798723131", events: "142255648", travel: "136625829", message: "1689328520",
    /* website answer -> the exact option text in the Google Form */
    options: {{
      "Joyfully attending": "🎉 Joyfully attending",
      "Regretfully unable": "💌 Regretfully unable",
      "Tilak": "🌸 Tilak (24 Nov, 4:30 PM)",
      "Engagement & Sangeet": "💃 Engagement & Sangeet (24 Nov, 7:00 PM)",
      "Haldi & Mehendi": "🌼 Haldi & Mehendi (25 Nov, 11:30 AM)",
      "Baraat": "🥁 Baraat (25 Nov, 7:00 PM)",
      "Jaimala": "💐 Jaimala (25 Nov, 9:00 PM)"
    }}
  }};
  var f = document.getElementById('rsvp-form'); if (!f) return;
  var more = document.getElementById('rsvp-more'), err = document.getElementById('rsvp-err');
  var btn = document.getElementById('rsvp-send'), done = document.getElementById('rsvp-done');
  f.addEventListener('change', function (e) {{
    if (e.target.name === 'attending') {{ more.hidden = e.target.value === 'Regretfully unable'; clearField('attending'); err.hidden = true; }}
  }});
  function clearField(key) {{ var box = document.getElementById('rsvp-' + key + '-error'); if (box) box.hidden = true; var control = document.getElementById('rsvp-' + key); if (control) control.removeAttribute('aria-invalid'); }}
  f.addEventListener('input', function (e) {{ err.hidden = true; if (e.target.name === 'name') clearField('name'); if (e.target.name === 'phone') clearField('phone'); if (e.target.name === 'events') clearField('events'); }});
  function fail(msg, key, el) {{
    if (key) {{ var box = document.getElementById('rsvp-' + key + '-error'), control = document.getElementById('rsvp-' + key); box.textContent = msg; box.hidden = false; if (control) control.setAttribute('aria-invalid', 'true'); err.hidden = true; }}
    else {{ err.textContent = msg; err.hidden = false; }}
    if (el) el.focus();
  }}
  f.addEventListener('submit', function (e) {{
    e.preventDefault(); err.hidden = true;
    var name = f.elements['name'].value.trim(), phone = f.phone.value.trim(), att = f.querySelector('input[name=attending]:checked');
    if (!name) return fail('Please enter your name.', 'name', f.elements['name']);
    if (phone.length < 10 || !/^[0-9]+$/.test(phone)) return fail('Please enter at least 10 digits using numbers only.', 'phone', f.phone);
    if (!att) return fail('Please choose whether you can join us.', 'attending', document.getElementById('rsvp-yes'));
    var coming = att.value === 'Joyfully attending';
    var evs = coming ? [].map.call(f.querySelectorAll('input[name=events]:checked'), function (c) {{ return c.value; }}) : [];
    if (coming && !evs.length) return fail('Please tick at least one event.', 'events', document.getElementById('ev-tilak'));
    var G = GOOGLE_FORM, data = new URLSearchParams();
    function put(k, v) {{ if (G[k] && v !== '') data.append('entry.' + G[k], G.options[v] || v); }}
    put('name', name); put('phone', phone); put('attending', att.value);
    if (coming) {{ put('guests', f.guests.value || '1'); evs.forEach(function (v) {{ put('events', v); }}); put('travel', f.travel.value.trim()); }}
    put('message', f.message.value.trim());
    data.append('pageHistory', coming ? '0,1,2' : '0,2');   // attendees visit sections 1–3; decliners skip details and go to wishes
    var SCRIPT_URL = G.id ? 'https://docs.google.com/forms/d/e/' + G.id + '/formResponse' : '';
    if (!SCRIPT_URL) return fail('RSVP is not connected yet. Please contact the family directly.', null);
    btn.disabled = true; btn.textContent = 'Sending…';
    fetch(SCRIPT_URL, {{ method: 'POST', mode: 'no-cors', body: data }}).then(function () {{
      f.hidden = true; done.hidden = false;
      document.getElementById('rsvp-done-msg').textContent = coming
        ? 'We have received your RSVP, ' + name + '. We look forward to celebrating with you.'
        : 'Thank you for letting us know, ' + name + '. You will be missed, and your blessings mean a lot to us.';
      done.focus();
    }}).catch(function () {{
      btn.disabled = false; btn.textContent = 'Send RSVP';
      fail('Your RSVP could not be sent. Please check your internet connection and try again.', null);
    }});
  }});
}})();

/* ---------- fireflies and stars behind the RSVP, firecrackers (fireworks) over the bride's side ---------- */
(function () {{
  var cvs = document.querySelectorAll('canvas.glow');
  if (!cvs.length) return;
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var COLS = [[255, 170, 0], [226, 32, 110], [255, 96, 20], [196, 24, 64], [255, 200, 30]];
  cvs.forEach(function (cv) {{
    var fire = cv.getAttribute('data-kind') === 'fire';
    var ctx = cv.getContext('2d'), dots = [], stars = [], sparks = [], next = 0, W = 0, H = 0, run = false, dpr = Math.min(window.devicePixelRatio || 1, 2);
    function size() {{
      W = cv.clientWidth; H = cv.clientHeight; if (!W || !H) return;
      cv.width = W * dpr; cv.height = H * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      dots = []; stars = [];
      if (fire) return;
      for (var i = 0; i < Math.round(H / 48); i++) dots.push({{ x: Math.random() * W, y: Math.random() * H, r: 1.6 + Math.random() * 1.8,
        a: Math.random() * 6.28, ph: Math.random() * 6.28, sp: .7 + Math.random() * 1.3 }});
      for (var j = 0; j < Math.round(H / 12); j++) stars.push({{ x: Math.random() * W, y: Math.random() * H * .75, r: .4 + Math.random() * 1.0,
        ph: Math.random() * 6.28, sp: .5 + Math.random() * 1.5 }});
    }}
    function burst(t) {{
      var r = cv.getBoundingClientRect(), top = Math.max(0, -r.top), bot = Math.min(H, window.innerHeight - r.top);
      if (bot - top < 80) return;
      var x = W * (.15 + Math.random() * .7), y = top + (bot - top) * (.12 + Math.random() * .5), c = COLS[Math.floor(Math.random() * COLS.length)];
      var n = 34 + Math.floor(Math.random() * 22), sp = 1.4 + Math.random() * 1.6;
      for (var k = 0; k < n; k++) {{
        var a = k / n * 6.283 + Math.random() * .2, v = sp * (.55 + Math.random() * .55);
        sparks.push({{ x: x, y: y, vx: Math.cos(a) * v, vy: Math.sin(a) * v, life: 1, c: c, d: .011 + Math.random() * .012 }});
      }}
    }}
    function frame(ms) {{
      if (!run) return;
      var t = ms / 1000; ctx.clearRect(0, 0, W, H);
      if (fire) {{
        if (t > next) {{ burst(t); if (Math.random() < .4) burst(t); next = t + 1.3 + Math.random() * 1.8; }}
        sparks = sparks.filter(function (p) {{ return p.life > 0; }});
        sparks.forEach(function (p) {{
          p.x += p.vx; p.y += p.vy; p.vy += .035; p.vx *= .985; p.life -= p.d;
          var g = Math.max(0, p.life);
          ctx.fillStyle = 'rgba(' + p.c[0] + ',' + p.c[1] + ',' + p.c[2] + ',' + g + ')';
          ctx.beginPath(); ctx.arc(p.x, p.y, 1.4 + g * 1.9, 0, 6.28); ctx.fill();
          ctx.fillStyle = 'rgba(' + p.c[0] + ',' + p.c[1] + ',' + p.c[2] + ',' + (g * .3) + ')';
          ctx.beginPath(); ctx.arc(p.x, p.y, 6 * g + 2, 0, 6.28); ctx.fill();
        }});
        requestAnimationFrame(frame); return;
      }}
      stars.forEach(function (s) {{
        ctx.fillStyle = 'rgba(255,248,225,' + (.35 + .35 * Math.sin(t * s.sp + s.ph)) + ')';
        ctx.beginPath(); ctx.arc(s.x, s.y, s.r, 0, 6.28); ctx.fill();
      }});
      dots.forEach(function (d) {{
        d.a += (Math.random() - .5) * .12; d.x += Math.cos(d.a) * .28; d.y += Math.sin(d.a) * .22 - .02;
        if (d.x < -10) d.x = W + 10; if (d.x > W + 10) d.x = -10; if (d.y < -10) d.y = H + 10; if (d.y > H + 10) d.y = -10;
        var g = Math.max(0, Math.sin(t * d.sp + d.ph)), R = d.r * 7;
        var gr = ctx.createRadialGradient(d.x, d.y, 0, d.x, d.y, R);
        gr.addColorStop(0, 'rgba(255,244,160,' + (.95 * g) + ')'); gr.addColorStop(.3, 'rgba(247,215,122,' + (.4 * g) + ')'); gr.addColorStop(1, 'rgba(247,215,122,0)');
        ctx.fillStyle = gr; ctx.beginPath(); ctx.arc(d.x, d.y, R, 0, 6.28); ctx.fill();
      }});
      requestAnimationFrame(frame);
    }}
    size(); window.addEventListener('resize', size);
    if (reduce || !('IntersectionObserver' in window)) {{ if (!fire) {{ run = true; frame(1500); run = false; }} return; }}
    new IntersectionObserver(function (es) {{
      var v = es[0].isIntersecting;
      if (v && !run) {{ run = true; requestAnimationFrame(frame); }} else if (!v) run = false;
    }}).observe(cv);
  }});
}})();
/* ---------- personal invitations: ?to=Name shows "Dear Name" on the envelope and pre-fills the RSVP name ---------- */
(function () {{
  var raw = '';
  try {{ var q = new URLSearchParams(location.search); raw = q.get('to') || q.get('name') || ''; }} catch (e) {{}}
  raw = raw.replace(/[\\u0000-\\u001f\\u007f<>]/g, '').replace(/\\s+/g, ' ').trim().slice(0, 60);
  var el = document.getElementById('intro-to');
  if (raw && el) {{ el.textContent = 'Dear ' + raw; el.hidden = false; }}
  var g = document.getElementById('cover-guest'), gn = document.getElementById('cover-guest-name');
  if (raw && g && gn) {{
    gn.textContent = raw; g.style.display = 'inline';
    var w = gn.getComputedTextLength ? gn.getComputedTextLength() : 0;      /* long names shrink to fit the card */
    if (w > 620) gn.setAttribute('font-size', (58 * 620 / w).toFixed(1));
  }}
  var f = document.getElementById('rsvp-name');
  function restoreInviteName() {{ if (f && raw) f.value = raw; }}
  restoreInviteName();
  var form = document.getElementById('rsvp-form');
  if (form) window.addEventListener('pageshow', function () {{
    form.reset();
    restoreInviteName();
  }});
}})();
</script>
</body>
</html>
"""
out = f"{SITE}/index.html" if MODE == "site" else f"{SITE}/test.html"
LINKS_HTML = '<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">\n<title>Invitation links - Soumya &amp; Madhur</title><meta name="robots" content="noindex">\n<style>\nbody{font:16px/1.5 Georgia,serif;color:#784646;background:#fdf5ef;margin:0;padding:24px 16px 60px}\nmain{max-width:760px;margin:0 auto}h1{font-weight:400;color:#b85c1d;margin:0 0 4px}p.s{margin:0 0 20px;font-style:italic}\nlabel{display:block;font-weight:700;margin:18px 0 6px}input,textarea{width:100%;box-sizing:border-box;font:inherit;padding:10px 12px;border:1.4px solid #c9a99a;border-radius:10px;background:#fff;color:#4f2c2c}\ntextarea{min-height:130px}button{font:700 15px Georgia,serif;letter-spacing:.06em;padding:8px 16px;border-radius:999px;border:1.5px solid #784646;background:transparent;color:#784646;cursor:pointer}\nbutton:hover{background:rgba(120,70,70,.12)}.row{display:grid;grid-template-columns:1fr auto auto;gap:8px;align-items:center;margin:10px 0;padding:10px 12px;background:#fff;border:1px solid #ecd9cc;border-radius:12px}\n.row b{grid-column:1/-1}.row input{grid-column:1;font-size:14px}.bar{display:flex;gap:10px;margin:16px 0;flex-wrap:wrap}small{color:#9a7468}\n</style></head><body><main>\n<h1>Personal invitation links</h1><p class="s">Type each guest or family on its own line. Each link opens the invitation with &ldquo;Dear &hellip;&rdquo; on the envelope and their name already in the RSVP.</p>\n<label for="base">Website address</label><input id="base" value="https://soumyamadhurweddinginvitation.vercel.app/">\n<label for="names">Names (one per line)</label><textarea id="names" placeholder="Sharma Family&#10;Aunty Rekha&#10;Rahul &amp; Priya"></textarea>\n<label for="msg">WhatsApp message <small>({name} and {link} are filled in)</small></label>\n<textarea id="msg">Dear {name}, you are warmly invited to the wedding of Soumya &amp; Madhur. Please open your invitation here: {link}</textarea>\n<div class="bar"><button id="copyall" type="button">Copy all (name + link)</button></div><div id="out"></div>\n<script>\nvar $=function(i){return document.getElementById(i)};\ntry{var sv=localStorage.getItem(\'base\');if(sv)$(\'base\').value=sv}catch(e){}\nfunction link(n){var b=$(\'base\').value.trim();if(b&&b.slice(-1)!==\'/\'&&b.indexOf(\'?\')<0)b+=\'/\';return b+\'?to=\'+encodeURIComponent(n)}\nfunction render(){var out=$(\'out\');out.textContent=\'\';try{localStorage.setItem(\'base\',$(\'base\').value)}catch(e){}\n $(\'names\').value.split(/\\n/).map(function(x){return x.trim()}).filter(Boolean).forEach(function(n){\n  var u=link(n),r=document.createElement(\'div\');r.className=\'row\';\n  var t=document.createElement(\'b\');t.textContent=n;var i=document.createElement(\'input\');i.value=u;i.readOnly=true;\n  var c=document.createElement(\'button\');c.textContent=\'Copy\';c.onclick=function(){navigator.clipboard.writeText(u);c.textContent=\'Copied\'};\n  var w=document.createElement(\'button\');w.textContent=\'WhatsApp\';w.onclick=function(){\n   window.open(\'https://wa.me/?text=\'+encodeURIComponent($(\'msg\').value.split(\'{name}\').join(n).split(\'{link}\').join(u)),\'_blank\',\'noopener\')};\n  r.append(t,i,c,w);out.append(r)})}\n$(\'names\').oninput=$(\'base\').oninput=render;\n$(\'copyall\').onclick=function(){var l=$(\'names\').value.split(/\\n/).map(function(x){return x.trim()}).filter(Boolean).map(function(n){return n+\'\\t\'+link(n)}).join(\'\\n\');navigator.clipboard.writeText(l);$(\'copyall\').textContent=\'Copied\'};\nrender();\n</script></main></body></html>\n'
open(out, "w", encoding="utf-8", newline="\n").write(page)
if MODE == "site":
    open(f"{SITE}/links.html", "w", encoding="utf-8", newline="\n").write(LINKS_HTML)
json.dump(checklist, open(f"{S}/checklist.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", out, len(page) // 1024, "KB; glyphs", len(used_glyphs))
