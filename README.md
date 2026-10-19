# Soumya & Madhur — wedding e-invite website

**To look at the site:** open `Website` and double-click **Open website.bat**. It opens http://localhost:8000 and starts at the envelope.

**To publish it:** upload the `Website` folder to Vercel (see "Deploying" in `CLAUDE.md`).

**To change something:** ask Claude in a session linked to this folder, e.g. *"Read CLAUDE.md in my Wedding_Stationary folder, then change …"*. It has everything it needs here:

- `CLAUDE.md`: how the project works, the rules, every decision, the RSVP wiring.
- `SETUP.md`: software to install, step by step (Python, a few packages, a headless browser).
- `Source/`: the approved PDF, the review PDF, and the code that builds the site from them.
- `Guides/PROJECT-HISTORY.md`: your original brief word for word and every later request.
- `Guides/CHECKLIST.md`: every change made to the PDF design and every website feature.
- `Archive/`: earlier versions and drafts (for reference).
- `Guides/RSVP-SETUP.md`: how replies reach the Google Form, and how to keep that working.
- `Previews/`: pictures and a video of the current site.

**One-command rebuild and check:** `python Source/make.py all` (or `build` then `check` after a small edit).
