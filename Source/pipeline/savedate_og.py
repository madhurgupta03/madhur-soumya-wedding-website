"""Link-preview picture shown when the invitation link is sent: two photos of Soumya and Madhur in arches, with the names and dates.
WhatsApp and other apps show it when the link is sent. Called from build.py; writes Website/save-the-date-og.jpg (1200 x 630)."""
import glob, io, os, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from fontTools.ttLib import TTFont

W, H = 1200, 630
BROWN, NAVY, GOLD, CREAM = (120, 70, 70), (29, 47, 92), (224, 160, 28), (251, 243, 233)
TXT, SOFTGOLD = (253, 245, 239), (247, 215, 122)      # light text on the dark blue


def _font(fonts_dir, name, size):
    f = TTFont(os.path.join(fonts_dir, name)); f.flavor = None      # woff2 -> plain TrueType in memory
    buf = io.BytesIO(); f.save(buf); buf.seek(0)
    return ImageFont.truetype(buf, size)


def _spaced(d, xy, text, font, fill, gap, anchor_center=True):
    widths = [d.textlength(c, font=font) for c in text]
    total = sum(widths) + gap * (len(text) - 1)
    x = xy[0] - total / 2 if anchor_center else xy[0]
    for c, w in zip(text, widths):
        d.text((x, xy[1]), c, font=font, fill=fill); x += w + gap


def _arch(photo, w, h, angle):
    photo = photo.convert("RGB"); r = photo.width / photo.height
    photo = (photo.crop((0, 0, photo.width, int(photo.width / (w / h)))) if r < w / h else photo.crop(((photo.width - int(photo.height * w / h)) // 2, 0, (photo.width + int(photo.height * w / h)) // 2, photo.height)))
    photo = photo.resize((w, h), Image.LANCZOS)
    pad = 8
    mask = Image.new("L", (w + 2 * pad, h + 2 * pad), 0); md = ImageDraw.Draw(mask)
    md.rounded_rectangle((0, 0, w + 2 * pad, h + 2 * pad), radius=14, fill=255)
    md.rectangle((0, 0, w + 2 * pad, (w + 2 * pad) // 2), fill=0); md.pieslice((0, 0, w + 2 * pad, w + 2 * pad), 180, 360, fill=255)
    card = Image.new("RGBA", mask.size, CREAM + (255,))
    inner = Image.new("L", (w, h), 0); idr = ImageDraw.Draw(inner)
    idr.rounded_rectangle((0, 0, w, h), radius=8, fill=255); idr.rectangle((0, 0, w, w // 2), fill=0); idr.pieslice((0, 0, w, w), 180, 360, fill=255)
    card.paste(photo, (pad, pad), inner)
    out = Image.new("RGBA", mask.size, (0, 0, 0, 0)); out.paste(card, (0, 0), mask)
    ring = Image.new("RGBA", mask.size, (0, 0, 0, 0)); ImageDraw.Draw(ring).rounded_rectangle((0, 0, mask.width - 1, mask.height - 1), radius=14, outline=GOLD + (255,), width=3)
    ring_mask = mask.copy(); ring.putalpha(Image.composite(ring.getchannel("A"), Image.new("L", mask.size, 0), ring_mask))
    out = Image.alpha_composite(out, ring)
    return out.rotate(angle, resample=Image.BICUBIC, expand=True)


def _load(images_dir, prefix):
    return Image.open(glob.glob(os.path.join(images_dir, prefix + "*.png"))[0]).convert("RGBA")


def _piece(img, longest, angle):
    k = longest / max(img.size)
    return img.resize((max(1, int(img.width * k)), max(1, int(img.height * k))), Image.LANCZOS).rotate(angle, resample=Image.BICUBIC, expand=True)


def _petal(color, w, h, angle):
    im = Image.new("RGBA", (w * 3, h * 3), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((w * 3 * 0.16, h * 3 * 0.02, w * 3 * 0.84, h * 3 * 0.98), fill=color + (235,))
    light = tuple(min(255, int(c + (255 - c) * .45)) for c in color)
    d.ellipse((w * 3 * 0.30, h * 3 * 0.10, w * 3 * 0.62, h * 3 * 0.52), fill=light + (210,))
    return im.resize((w, h), Image.LANCZOS).rotate(angle, resample=Image.BICUBIC, expand=True)


def _scatter(bg, images_dir):
    """Small colourful petals drifting down over the card."""
    rnd = random.Random(5)
    items = []
    cols = [(240, 98, 146), (255, 138, 101), (249, 168, 37), (186, 104, 200), (236, 64, 122), (255, 112, 67), (255, 183, 77)]
    text_zone = (690, 100, 1125, 540)
    n = 0
    while n < 26:
        x, y = rnd.randint(40, W - 40), rnd.randint(40, H - 40)
        if text_zone[0] < x < text_zone[2] and text_zone[1] < y < text_zone[3]:
            continue
        w = rnd.randint(11, 20); items.append((_petal(rnd.choice(cols), w, int(w * 1.6), rnd.randint(0, 359)), x, y)); n += 1
    base = bg.convert("RGBA")
    for img, x, y in items:
        base.alpha_composite(img, (max(0, min(W - img.width, int(x - img.width / 2))), max(0, min(H - img.height, int(y - img.height / 2)))))
    bg.paste(base.convert("RGB"))


def make(site_dir, assets_dir, fonts_dir):
    bg = Image.new("RGB", (W, H)); px = bg.load()
    for y in range(H):
        t = y / H
        c = tuple(int(a + (b - a) * t) for a, b in zip((12, 24, 60), (4, 9, 28)))
        for x in range(W): px[x, y] = c
    d = ImageDraw.Draw(bg)
    d.rectangle((16, 16, W - 17, H - 17), outline=GOLD, width=2); d.rectangle((26, 26, W - 27, H - 27), outline=GOLD, width=1)
    _scatter(bg, os.path.join(site_dir, "images"))

    # one picture: the two of them standing in front of the stairs (slideshow photo-12)
    shows = os.path.join(site_dir, "images", "slideshow")
    stairs = Image.open(os.path.join(shows, "photo-12.jpg")).convert("RGB").crop((0, 450, 1350, 2250))
    for img, x, y, a in ((_arch(stairs, 336, 448, 0), 150, 78, 0),):
        shadow = Image.new("RGBA", bg.size, (0, 0, 0, 0)); shadow.paste((60, 30, 20, 90), (x + 6, y + 14), img.getchannel("A"))
        bg.paste(Image.alpha_composite(bg.convert("RGBA"), shadow.filter(ImageFilter.GaussianBlur(12))).convert("RGB"))
        bg.paste(img, (x, y), img)
    d = ImageDraw.Draw(bg)

    cx = 905
    semi = _font(fonts_dir, "crimson-text-latin-600-normal.woff2", 30)
    ital = _font(fonts_dir, "crimson-text-latin-400-italic.woff2", 104)
    ital_s = _font(fonts_dir, "crimson-text-latin-400-italic.woff2", 36)
    _spaced(d, (cx, 128), "SAVE THE DATE", semi, SOFTGOLD, 7)
    d.text((cx, 232), "Soumya", font=ital, fill=TXT, anchor="mm")
    d.text((cx, 336), "& Madhur", font=ital, fill=TXT, anchor="mm")
    d.line((cx - 120, 402, cx + 120, 402), fill=GOLD, width=2)
    _spaced(d, (cx, 430), "24 & 25 NOVEMBER 2026", semi, SOFTGOLD, 3)
    d.text((cx, 500), "Jhansi · Orchha", font=ital_s, fill=TXT, anchor="mm")
    bg.save(os.path.join(site_dir, "save-the-date-og.jpg"), quality=88, optimize=True, progressive=True)
