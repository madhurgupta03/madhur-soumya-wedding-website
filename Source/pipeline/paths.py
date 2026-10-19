"""Every folder the pipeline uses, relative to the project root (the Wedding_Stationary folder)."""
import os
PIPELINE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.dirname(PIPELINE)
ROOT = os.path.dirname(SOURCE)
PDF_ORIGINAL = os.path.join(SOURCE, "pdf", "1_ORIGINAL_approved_design.pdf")   # the approved design: copy this
PDF_REVIEWED = os.path.join(SOURCE, "pdf", "2_REVIEWED_with_comments.pdf")    # same design + review comments
DATA = os.path.join(SOURCE, "data")            # generated from the PDF: model.json, opacity.json, svgsrc/, pdf-fonts/
FONTS = os.path.join(SOURCE, "fonts")          # Crimson Text web fonts (OFL) used for new/restyled text
WEBSITE = os.path.join(ROOT, "Website")        # the finished site = the folder you deploy
PREVIEWS = os.path.join(ROOT, "Previews")      # screenshots / video made by the checks
CHECKS = os.path.join(SOURCE, "checks")        # scratch output of check.py (renders, diffs)
for d in (DATA, WEBSITE, PREVIEWS, CHECKS):
    os.makedirs(d, exist_ok=True)
