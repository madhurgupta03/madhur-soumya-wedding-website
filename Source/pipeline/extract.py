"""Step 1 of the pipeline (python make.py extract).
Extract every page of the original invite into a JSON model + lossless image files.
Images keep native pixel size and their embedded ICC profile; nothing is resampled."""
import sys, os, json, hashlib, statistics
import pymupdf as fitz
from fontTools.ttLib import TTFont
from PIL import Image
import io

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
SRC = paths.PDF_ORIGINAL
IMG = os.path.join(paths.WEBSITE, "images")
FNT = os.path.join(paths.DATA, "pdf-fonts")
os.makedirs(IMG, exist_ok=True)
os.makedirs(FNT, exist_ok=True)
doc = fitz.open(SRC)

def hexcol(c):
    if isinstance(c, int):
        return "#%06x" % c
    return "#%02x%02x%02x" % tuple(round(v * 255) for v in c[:3])

img_by_hash, img_files = {}, {}
def export_image(xref):
    if xref in img_files:
        return img_files[xref]
    info = doc.extract_image(xref)
    pix = fitz.Pixmap(doc, xref)
    if info.get("smask"):
        mask = fitz.Pixmap(doc, info["smask"])
        pix = fitz.Pixmap(pix, mask)
    # ICC profile of the image's colour space, embedded unchanged in the PNG
    icc = None
    cs = doc.xref_get_key(xref, "ColorSpace")
    if cs[0] == "array" and "ICCBased" in cs[1]:
        icc_xref = int(cs[1].split()[1])
        icc = doc.xref_stream(icc_xref)
    mode = "RGBA" if pix.alpha else "RGB"
    im = Image.frombytes(mode, (pix.width, pix.height), pix.samples)
    h = hashlib.sha1(pix.samples).hexdigest()[:10]
    if h in img_by_hash:
        img_files[xref] = img_by_hash[h]
        return img_files[xref]
    name = f"img-{len(img_by_hash)+1:02d}-{pix.width}x{pix.height}.png"
    im.save(f"{IMG}/{name}", optimize=False, compress_level=6, icc_profile=icc)
    img_by_hash[h] = {"file": name, "w": pix.width, "h": pix.height, "icc": bool(icc)}
    img_files[xref] = img_by_hash[h]
    return img_files[xref]

font_files = {}
def export_font(xref, name):
    if xref in font_files:
        return font_files[xref]
    n, ext, typ, buf = doc.extract_font(xref)
    if not buf:
        font_files[xref] = None
        return None
    fn = f"{name.split('+')[-1]}-{xref}.{ext}"
    open(f"{FNT}/{fn}", "wb").write(buf)
    tt = TTFont(io.BytesIO(buf))
    font_files[xref] = {"file": fn, "upm": tt["head"].unitsPerEm,
                        "cmap": tt.getBestCmap() or {}, "hmtx": tt["hmtx"].metrics}
    return font_files[xref]

pages = []
for pn, page in enumerate(doc):
    P = {"n": pn + 1, "images": [], "drawings": [], "lines": []}
    # images in paint order
    for inf in page.get_image_info(xrefs=True):
        meta = export_image(inf["xref"])
        P["images"].append({"file": meta["file"], "w": meta["w"], "h": meta["h"],
                            "m": [round(v, 4) for v in inf["transform"]]})
    # vector drawings (skip the full-page white/paper fills, recorded separately)
    for g in page.get_drawings():
        r = g["rect"]
        if r.width >= 809 and r.height >= 1439:
            P.setdefault("fills", []).append(hexcol(g["fill"]))
            continue
        d = []
        for it in g["items"]:
            if it[0] == "l":
                d.append(f"M{it[1].x:.3f} {it[1].y:.3f}L{it[2].x:.3f} {it[2].y:.3f}")
            elif it[0] == "c":
                d.append(f"M{it[1].x:.3f} {it[1].y:.3f}C{it[2].x:.3f} {it[2].y:.3f} {it[3].x:.3f} {it[3].y:.3f} {it[4].x:.3f} {it[4].y:.3f}")
            elif it[0] == "re":
                q = it[1]; d.append(f"M{q.x0:.3f} {q.y0:.3f}H{q.x1:.3f}V{q.y1:.3f}H{q.x0:.3f}Z")
            elif it[0] == "qu":
                q = it[1]; d.append(f"M{q.ul.x:.3f} {q.ul.y:.3f}L{q.ur.x:.3f} {q.ur.y:.3f}L{q.lr.x:.3f} {q.lr.y:.3f}L{q.ll.x:.3f} {q.ll.y:.3f}Z")
        # join sub-paths so continuous outlines stay one contour
        path = "".join(d)
        P["drawings"].append({"d": path, "fill": hexcol(g["fill"]) if g.get("fill") else None,
                              "evenodd": bool(g.get("even_odd")), "op": g.get("fill_opacity", 1)})
    # fonts on page
    fmap = {}
    for f in page.get_fonts():
        base = f[3].split("+")[-1]
        fmap[base] = (f[0], f[3])
    # text
    raw = page.get_text("rawdict")
    for b in raw["blocks"]:
        for l in b.get("lines", []):
            for s in l["spans"]:
                chars = s["chars"]
                text = "".join(c["c"] for c in chars)
                if not text.strip():
                    continue
                fname = s["font"]
                key = next((k for k in fmap if k.startswith(fname[:20])), None)
                if key is None:
                    key, fmeta = fname, None
                else:
                    fx, full = fmap[key]
                    fmeta = export_font(fx, full)
                size = s["size"]
                track = None
                if fmeta and len(chars) > 1:
                    diffs = []
                    for a, c2 in zip(chars, chars[1:]):
                        gid = fmeta["cmap"].get(ord(a["c"]))
                        if gid is None:
                            continue
                        adv = fmeta["hmtx"][gid][0] * size / fmeta["upm"]
                        diffs.append(c2["origin"][0] - a["origin"][0] - adv)
                    if diffs:
                        track = round(statistics.median(diffs), 3)
                P["lines"].append({
                    "text": text, "font": key, "file": fmeta["file"] if fmeta else None,
                    "size": round(size, 3), "color": hexcol(s["color"]),
                    "x": round(chars[0]["origin"][0], 3), "y": round(chars[0]["origin"][1], 3),
                    "x_end": round(chars[-1]["bbox"][2], 3),
                    "bbox": [round(v, 2) for v in s["bbox"]], "track": track,
                    "char_x": [round(c["origin"][0], 2) for c in chars]})
    pages.append(P)

json.dump(pages, open(os.path.join(paths.DATA, "model.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("images:", len(img_by_hash), sum(os.path.getsize(f"{IMG}/{v['file']}") for v in img_by_hash.values()) // 1024, "KB")
for P in pages:
    print("page", P["n"], "imgs", len(P["images"]), "draw", len(P["drawings"]), "fills", P.get("fills"))
    for L in P["lines"]:
        print("   ", L["font"], L["size"], L["color"], L["x"], L["y"], "track", L["track"], repr(L["text"]))
