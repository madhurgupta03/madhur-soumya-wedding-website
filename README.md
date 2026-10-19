# Soumya & Madhur — wedding e-invite website

**To look at the site:** open `Website` and double-click **Open website.bat**. It opens http://localhost:8000 and starts at the envelope.

**Dev server with hot reload:** `python3 serve.py` (or `./open.sh` to also open the browser).

**AI assistants:** When ChatGPT or Codex is connected to this repository (for example, through Codex or a ChatGPT project with repository access), project context is automatic: the assistant reads `AGENTS.md`, which points to `CLAUDE.md`. Claude reads `CLAUDE.md` directly. A standalone ChatGPT chat cannot read files from your computer; open this repository in a connected workspace to give it automatic access.

**Hosting status:** The site is deployed on Vercel Hobby from the `main` branch of `madhurgupta03/madhur-soumya-wedding-website`. The project root is `Website`, with the `Other` preset and no build, install, or output-directory overrides or environment variables. Vercel Hobby has no two-month expiry or billing cycle for personal, non-commercial use; usage limits apply. The owner is happy with the Vercel-provided project URL and does not require separate Python build/check automation or a recovery note. The site is static; RSVP submissions go to Google Forms.

- **Live site:** [madhur-soumya-wedding-website.vercel.app](https://madhur-soumya-wedding-website.vercel.app/)
- **Google Forms RSVP:** [Open the RSVP form](https://tinyurl.com/madhur-soumya-wedding-rsvp)
- **Deployment status:** Vercel is working, and pushes to `main` automatically create Ready production deployments. The owner has decided not to perform any further manual deployment checks; unchecked visual checks are waived, not verified. Outstanding functional work, including deferred Google Forms issues, is tracked in [Guides/OPEN-ITEMS.md](Guides/OPEN-ITEMS.md).
- **Hosting research and launch plan:** [Guides/HOSTING-OPTIONS-AND-PLAN.md](Guides/HOSTING-OPTIONS-AND-PLAN.md)
- **Tickable deployment checklist:** [Guides/HOSTING-CHECKLIST.md](Guides/HOSTING-CHECKLIST.md)

The existing project setup is documented under "Deploying" in `CLAUDE.md`.

**To change something:** ask your assistant in a session linked to this folder to make the change. It should follow `AGENTS.md` and `CLAUDE.md` automatically. The project context is here:

- `CLAUDE.md`: how the project works, the rules, every decision, the RSVP wiring.
- `SETUP.md`: software to install, step by step (Python, a few packages, a headless browser).
- `Source/`: the approved PDF, the review PDF, and the code that builds the site from them.
- `Guides/PROJECT-HISTORY.md`: your original brief word for word and every later request.
- `Guides/CHECKLIST.md`: every change made to the PDF design and every website feature.
- `Guides/OPEN-ITEMS.md`: pending follow-ups and items waiting on supplied assets.
- `Archive/`: earlier versions and drafts (for reference).
- `Guides/RSVP-SETUP.md`: how replies reach the Google Form, and how to keep that working.
- `Previews/`: pictures and a video of the current site.

**One-command rebuild and check:** `python Source/make.py all` (or `build` then `check` after a small edit).
