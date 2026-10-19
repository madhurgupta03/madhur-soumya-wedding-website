"""One command for everything.  Run from the Wedding_Stationary folder:

    python Source/make.py all        extract + glyphs + build + og + check   (full rebuild from the PDF)
    python Source/make.py build      rebuild Website/index.html after editing Source/pipeline/build.py
    python Source/make.py check      run the automatic checks (always do this after a change)
    python Source/make.py serve      open the site at http://localhost:8000
    python Source/make.py video      record the envelope opening (needs ffmpeg)
    python Source/make.py extract | glyphs | og     single steps
"""
import os, sys, subprocess, webbrowser, http.server, functools
HERE = os.path.dirname(os.path.abspath(__file__))
PIPE = os.path.join(HERE, "pipeline")
ROOT = os.path.dirname(HERE)
PY = sys.executable

def run(script, *args):
    print(f"\n=== {script} {' '.join(args)}".rstrip())
    r = subprocess.run([PY, os.path.join(PIPE, script), *args], cwd=ROOT)
    if r.returncode: sys.exit(r.returncode)

def serve(port=8000):
    site = os.path.join(ROOT, "Website")
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=site)
    print(f"Serving {site}\n  -> http://localhost:{port}   (Ctrl+C to stop)")
    webbrowser.open(f"http://localhost:{port}")
    http.server.ThreadingHTTPServer(("127.0.0.1", port), handler).serve_forever()

steps = {
    "extract": lambda: run("extract.py"),
    "glyphs": lambda: run("glyphs.py"),
    "build": lambda: (run("build.py", "test"), run("build.py")),
    "og": lambda: run("og.py"),
    "check": lambda: run("check.py"),
    "video": lambda: run("record.py"),
    "serve": serve,
}
cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
if cmd == "all":
    for s in ("extract", "glyphs", "build", "og", "check"): steps[s]()
elif cmd in steps:
    steps[cmd]()
else:
    print(__doc__)
