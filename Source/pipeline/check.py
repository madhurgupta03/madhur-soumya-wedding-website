"""Step 5 (python make.py check): automatic checks of the built website. Run after every change.

  1. Card pages vs the approved PDF: each page is rendered and compared with the PDF page.
     Only the agreed changes should differ (see Guides/CHECKLIST.md). A side-by-side sheet is saved
     to Source/checks/compare-pN.png so you can look at any page.
  2. Behaviour: envelope opens and ends on the cover; reload starts at the envelope; no sideways
     scrolling on a phone; web fonts load; no JavaScript errors.
  3. RSVP: fills the form and checks exactly what would be sent to the Google Form (nothing is sent:
     the request is intercepted).
  4. Saves Previews/Full-invite-overview.png (every section in order, phone size).
Exit code 0 = all good, 1 = something failed (details printed)."""
import os, sys, json
from urllib.parse import parse_qsl
import pymupdf as fitz
from PIL import Image, ImageChops, ImageFilter, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths

def url(name): return "file:///" + os.path.join(paths.WEBSITE, name).replace("\\", "/").lstrip("/")
fails = []
def check(ok, msg):
    print(("  PASS " if ok else "  FAIL ") + msg)
    if not ok: fails.append(msg)

# reference renders of the approved PDF (810 x 1440 px = 1 px per PDF point)
ref = os.path.join(paths.CHECKS, "ref"); os.makedirs(ref, exist_ok=True)
doc = fitz.open(paths.PDF_ORIGINAL)
for i, pg in enumerate(doc):
    f = os.path.join(ref, f"p{i+1}.png")
    if not os.path.exists(f): pg.get_pixmap(dpi=72).save(f)

CHANGED = {1: "names added under the monogram", 2: "parent names + tighter name/Hindi spacing",
           3: "venue font, title gap, directions button", 4: "title split, venue font, directions",
           5: "title split, venue font, directions", 6: "venue font, title gap, directions",
           7: "venue font, title gap, directions", 8: "no changes"}
errors = []
with sync_playwright() as p:
    b = p.chromium.launch()
    print("1. Card pages compared with the approved PDF")
    pg = b.new_page(viewport={"width": 810, "height": 1440})
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.add_init_script("document.addEventListener('DOMContentLoaded',()=>{document.documentElement.classList.remove('js','locked')})")
    pg.add_init_script("Object.defineProperty(window,'matchMedia',{value:q=>({matches:q.includes('reduce'),addListener(){},removeListener(){}})})")
    pg.goto(url("test.html") if os.path.exists(os.path.join(paths.WEBSITE, "test.html")) else url("index.html"))
    pg.wait_for_timeout(1500)
    for n in range(1, 9):
        out = os.path.join(paths.CHECKS, f"web-p{n}.png")
        el = pg.locator(f"#page-{n} svg"); el.scroll_into_view_if_needed(); pg.wait_for_timeout(300)
        el.screenshot(path=out)
        a = Image.open(os.path.join(ref, f"p{n}.png")).convert("RGB")
        w = Image.open(out).convert("RGB").resize(a.size)
        d = ImageChops.difference(a.filter(ImageFilter.GaussianBlur(2)), w.filter(ImageFilter.GaussianBlur(2))).convert("L")
        h = d.histogram(); pct = sum(h[21:]) / (a.width * a.height) * 100
        sheet = Image.new("RGB", (a.width * 2 + 20, a.height), "white"); sheet.paste(a, (0, 0)); sheet.paste(w, (a.width + 20, 0))
        sheet.save(os.path.join(paths.CHECKS, f"compare-p{n}.png"))
        check(pct < (1.0 if n == 8 else 3.0 if n == 1 else 8.0), f"page {n}: {pct:.2f}% of the page differs from the PDF ({CHANGED[n]})")
    pg.close()

    print("2. Behaviour on a phone")
    pg = b.new_page(viewport={"width": 390, "height": 844})
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto(url("index.html")); pg.wait_for_timeout(900)
    check(pg.is_visible("#intro"), "page opens on the envelope")
    pg.click("#seal", force=True); pg.wait_for_timeout(7500)
    check(pg.locator("#intro").count() == 0 and pg.evaluate("scrollY") == 0, "envelope animation ends on the cover")
    check(pg.evaluate("document.documentElement.scrollWidth") <= 390, "no sideways scrolling at phone width")
    fonts = pg.evaluate("[...document.fonts].filter(f=>f.status==='loaded').length")
    check(fonts >= 3, f"web fonts loaded ({fonts})")
    pg.evaluate("document.getElementById('rsvp').scrollIntoView()"); pg.wait_for_timeout(300)
    pg.reload(); pg.wait_for_timeout(1200)
    check(pg.evaluate("scrollY") == 0 and pg.is_visible("#intro"), "reload starts again from the envelope")
    order = pg.evaluate("[...document.querySelectorAll('body > section')].map(s=>s.id)")
    print("     section order:", " > ".join(order))

    print("3. RSVP form (request intercepted, nothing is sent)")
    sent = []
    pg.route("**/formResponse", lambda r, q: (sent.append(q.post_data), r.fulfill(status=200, body="ok")))
    pg.click("#intro-skip"); pg.wait_for_timeout(900)
    pg.evaluate("document.getElementById('rsvp').scrollIntoView()"); pg.wait_for_timeout(400)
    pg.click("#rsvp-send"); pg.wait_for_timeout(200)
    check(pg.is_visible("#rsvp-err") and not sent, "empty form is stopped with a message")
    pg.fill("#rsvp-name", "Check Test"); pg.fill("#rsvp-phone", "98765 43210"); pg.check("#rsvp-yes")
    pg.select_option("#rsvp-guests", "3"); pg.click("label[for=ev-tilak]"); pg.fill("#rsvp-msg", "hello")
    pg.click("#rsvp-send"); pg.wait_for_timeout(700)
    got = dict()
    for k, v in parse_qsl(sent[0] if sent else ""): got.setdefault(k, []).append(v)
    want = {"entry.127160018": ["Check Test"], "entry.1746679459": ["98765 43210"], "entry.55150948": ["🎉 Joyfully attending"],
            "entry.798723131": ["3"], "entry.1689328520": ["hello"], "pageHistory": ["0,1"],
            "entry.142255648": ["💃 Engagement & Sangeet (24 Nov)", "🌼 Haldi & Mehendi (25 Nov)", "🥁 Baraat (25 Nov)", "💐 Jaimala (25 Nov)"]}
    check(got == want, "attending reply maps to the Google Form exactly" + ("" if got == want else f"\n       sent {got}"))
    check(pg.is_visible("#rsvp-done"), "thank-you message shows")
    pg.close()

    print("4. Overview picture")
    pg = b.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=1.5)
    pg.goto(url("index.html")); pg.wait_for_timeout(700); pg.click("#intro-skip"); pg.wait_for_timeout(900)
    shots = []
    for sid in order:
        el = pg.locator("#" + sid); el.scroll_into_view_if_needed(); pg.wait_for_timeout(1100)
        f = os.path.join(paths.CHECKS, f"ov-{sid}.png"); el.screenshot(path=f); shots.append((f, sid))
    pg.close(); b.close()
W, pad = 280, 20
ims = [(Image.open(f).convert("RGB"), l) for f, l in shots]
ims = [(im.resize((W, int(im.height * W / im.width))), l) for im, l in ims]
rows = [ims[:7], ims[7:]]
hs = [max(i.height for i, _ in r) + 40 for r in rows if r]
sheet = Image.new("RGB", (7 * (W + pad) + pad, sum(hs) + pad * 3), (240, 234, 228)); d = ImageDraw.Draw(sheet)
y = pad
for r, h in zip(rows, hs):
    x = pad
    for im, l in r:
        d.text((x, y), l, fill=(120, 70, 70)); sheet.paste(im, (x, y + 20)); x += W + pad
    y += h + pad
sheet.save(os.path.join(paths.PREVIEWS, "Full-invite-overview.png"))
print("  saved Previews/Full-invite-overview.png")

check(not errors, "no JavaScript errors" + ("" if not errors else f": {errors}"))
print("\nALL CHECKS PASSED" if not fails else f"\n{len(fails)} CHECK(S) FAILED")
sys.exit(1 if fails else 0)
