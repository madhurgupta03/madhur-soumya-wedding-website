# SETUP — software needed to work on the wedding website

Everything a new computer (or a new Claude session) needs before running the pipeline.
Tested on Python 3.13 with the package versions in `Source/requirements.txt`.

## Required

| Software | Why it's needed | Check it's installed |
|---|---|---|
| **Python 3.10 or newer** | Runs the whole pipeline (`Source/make.py`) and the local preview server | `python --version` |
| **Python packages** (`Source/requirements.txt`): pymupdf, pillow, fonttools, brotli, svgpathtools, playwright | Read the PDF, build the page, run checks | `python -c "import pymupdf, PIL, fontTools, brotli, svgpathtools, playwright"` |
| **Chromium for Playwright** | Headless browser used by `check`, `og` and `video` | `python -m playwright install --dry-run chromium` |

## Optional

| Software | Needed for | Check |
|---|---|---|
| **ffmpeg** | `python Source/make.py video` (records the envelope opening to an MP4) | `ffmpeg -version` |
| **Node.js 18+ and the Vercel CLI** | Publishing from the command line (`vercel --prod`). Not needed if you upload the `Website` folder on vercel.com or deploy through GitHub | `node -v`, `vercel --version` |
| **Git** | Version history / deploying through GitHub | `git --version` |

Nothing else is needed: the fonts, PDFs and extracted artwork are all inside this folder.

## Install — Windows (this laptop)

Open **PowerShell** in the `Wedding_Stationary` folder (in File Explorer: click the address bar, type `powershell`, press Enter).

1. **Python.** Anaconda is already installed on this laptop. Use the *Anaconda Prompt* (Start menu) or make sure `python` works in PowerShell:
   ```powershell
   python --version
   ```
   If it isn't found, either open *Anaconda Prompt* instead, or install Python from https://www.python.org/downloads/ (tick **"Add python.exe to PATH"** during setup).
2. **Packages and the browser:**
   ```powershell
   python -m pip install -r Source\requirements.txt
   python -m playwright install chromium
   ```
3. **(Optional) ffmpeg:** `winget install Gyan.FFmpeg`, then open a new PowerShell window.
4. **(Optional) Vercel CLI:** install Node.js LTS from https://nodejs.org, then `npm install -g vercel` and `vercel login`.
5. **Test the setup:**
   ```powershell
   python Source\make.py all
   ```
   It should end with `ALL CHECKS PASSED` (about 1–2 minutes).

## Install — macOS / Linux

```bash
python3 -m pip install -r Source/requirements.txt      # add --break-system-packages on newer Debian/Ubuntu
python3 -m playwright install chromium                  # on Linux also: python3 -m playwright install-deps chromium
# optional: brew install ffmpeg   |   sudo apt install ffmpeg
python3 Source/make.py all
```

## Common problems

| Problem | Fix |
|---|---|
| `'python' is not recognized` | Use *Anaconda Prompt*, or `py` instead of `python`, or reinstall Python with "Add to PATH" ticked |
| `Executable doesn't exist ... chromium` | Run `python -m playwright install chromium` |
| `No module named brotli` when building | `python -m pip install brotli` |
| Windows blocks `Open website.bat` ("Windows protected your PC") | Click **More info → Run anyway** |
| Port 8000 already in use | Close the other preview window, or run `python -m http.server 8001` inside `Website` |
