"""Optional (python make.py video): record the envelope opening to Previews/Envelope-opening.mp4.
Needs ffmpeg on the PATH. The recording comes from a browser without a graphics chip, so it looks
slightly less smooth than a real phone."""
import os, sys, glob, shutil, subprocess, tempfile
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
if not shutil.which("ffmpeg"):
    sys.exit("ffmpeg not found - install it (see SETUP.md) or skip this step")
tmp = tempfile.mkdtemp()
page_url = "file:///" + os.path.join(paths.WEBSITE, "index.html").replace("\\", "/").lstrip("/")
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 430, "height": 932}, record_video_dir=tmp, record_video_size={"width": 430, "height": 932})
    pg = ctx.new_page(); pg.goto(page_url); pg.wait_for_timeout(1200)
    pg.click("#seal", force=True); pg.wait_for_timeout(7000)
    ctx.close(); b.close()
src = glob.glob(os.path.join(tmp, "*.webm"))[0]
out = os.path.join(paths.PREVIEWS, "Envelope-opening.mp4")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-vf", "fps=30,scale=430:-2", "-c:v", "libx264",
                "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], check=True)
print("saved", out)
