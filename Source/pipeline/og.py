"""Step 4 (python make.py og): make Website/og-cover.jpg, the picture WhatsApp/Facebook show when the link is shared.
It is a 1200x630 crop of the cover (monogram + names), rendered from the built site."""
import os, sys
from PIL import Image
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths

page_url = "file:///" + os.path.join(paths.WEBSITE, "index.html").replace("\\", "/").lstrip("/")
tmp = os.path.join(paths.CHECKS, "og-full.png")
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1200, "height": 2134})
    pg.goto(page_url); pg.wait_for_timeout(800)
    pg.click("#intro-skip"); pg.wait_for_timeout(900)          # skip the envelope
    pg.locator("#page-1 svg").screenshot(path=tmp)
    b.close()
im = Image.open(tmp).convert("RGB"); k = im.width / 810          # page units are PDF points (810 x 1440)
crop = im.crop((0, int(352 * k), im.width, int(884 * k)))
crop = crop.resize((int(crop.width * 630 / crop.height), 630), Image.LANCZOS)
og = Image.new("RGB", (1200, 630), (0xfd, 0xf5, 0xef)); og.paste(crop, ((1200 - crop.width) // 2, 0))
og.save(os.path.join(paths.WEBSITE, "og-cover.jpg"), quality=88)
print("og-cover.jpg written")
