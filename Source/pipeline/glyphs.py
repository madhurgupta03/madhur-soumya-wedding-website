"""Step 2 of the pipeline (python make.py glyphs).
Exports each PDF page as SVG with text drawn as the PDF's own letter outlines (data/svgsrc/pN.svg),
and records the opacity of every image in paint order (data/opacity.json).
The build uses the letter outlines so unchanged text looks exactly like the PDF, even for the
Canva-only fonts (Alta, Amoresa) that can't be shipped as web fonts."""
import os, re, json, sys
import xml.etree.ElementTree as ET
import pymupdf as fitz
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths

out = os.path.join(paths.DATA, "svgsrc")
os.makedirs(out, exist_ok=True)
doc = fitz.open(paths.PDF_ORIGINAL)
XL = "{http://www.w3.org/1999/xlink}href"
opacity = {}
for i, page in enumerate(doc):
    n = i + 1
    svg = page.get_svg_image(text_as_path=True)
    svg = re.sub(r'xlink:href="data:[^"]+"', 'xlink:href=""', svg)      # drop embedded bitmaps; images come from Website/images
    path = os.path.join(out, f"p{n}.svg")
    open(path, "w", encoding="utf-8").write(svg)
    found = []
    def walk(el, op):
        tag = el.tag.split("}")[1]
        if tag in ("defs", "mask", "clipPath", "symbol"):
            return
        o = op * float(el.get("opacity", 1))
        if tag == "image" or (tag == "use" and el.get(XL, "").startswith("#image")):
            found.append(round(o, 3))
        for c in el:
            walk(c, o)
    walk(ET.parse(path).getroot(), 1)
    opacity[str(n)] = found
json.dump(opacity, open(os.path.join(paths.DATA, "opacity.json"), "w", encoding="utf-8"))
print("glyph SVGs + opacity written for", len(doc), "pages")
