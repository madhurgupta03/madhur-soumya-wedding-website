import sys, os
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops, ImageDraw
S = os.path.dirname(os.path.abspath(__file__))
html = sys.argv[1] if len(sys.argv) > 1 else f"{S}/site/test.html"
os.makedirs(f"{S}/out", exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 810, "height": 1440})
    pg.goto("file://" + html)
    pg.wait_for_timeout(1500)
    pg.evaluate("document.fonts.ready")
    for n in range(1, 9):
        el = pg.locator(f"#page-{n} svg")
        el.scroll_into_view_if_needed()
        pg.wait_for_timeout(400)
        el.screenshot(path=f"{S}/out/web-{n}.png")
    # phone check
    pg2 = b.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2)
    pg2.goto("file://" + html); pg2.wait_for_timeout(1500)
    pg2.screenshot(path=f"{S}/out/phone-1.png")
    pg2.evaluate("document.getElementById('page-3').scrollIntoView()"); pg2.wait_for_timeout(800)
    pg2.screenshot(path=f"{S}/out/phone-3.png")
    sw = pg2.evaluate("document.documentElement.scrollWidth")
    print("phone scrollWidth", sw)
    b.close()

for n in range(1, 9):
    a = Image.open(f"{S}/ref/p-{n}.png").convert("RGB")
    w = Image.open(f"{S}/out/web-{n}.png").convert("RGB").resize(a.size)
    diff = ImageChops.difference(a, w).convert("L")
    hist = diff.histogram()
    big = sum(hist[24:]) / (a.size[0] * a.size[1])
    print(f"page {n}: pixels differing >24/255: {big*100:.2f}%  bbox {diff.point(lambda v: 255 if v > 24 else 0).getbbox()}")
    sheet = Image.new("RGB", (a.size[0] * 2 + 20, a.size[1]), "white")
    sheet.paste(a, (0, 0)); sheet.paste(w, (a.size[0] + 20, 0))
    sheet.save(f"{S}/out/cmp-{n}.png")
