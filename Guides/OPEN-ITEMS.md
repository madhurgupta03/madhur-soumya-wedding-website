# Open items

Use this list for work that is still pending. Check an item only after the change or follow-up is complete.

## RSVP

**No open RSVP items.** The following work is complete:

- [x] Match mobile-number validation to the form's digits-only prompt; local checks reject spaces and symbols.
- [x] Show field validation beside its field. The owner confirmed the error placement works.
- [x] Attending choice and guest-count submission work; the owner confirmed this.
- [x] Compare the website mapping with the current Google Form fields and options; local checks cover the mapped payloads.
- [x] Reset RSVP answers on every visit or reload. Keep the intentional defaults (Joyfully attending, 1 guest, all events selected), leave other answers blank, and preserve personalized invite-name prefill.
- [x] Confirm the deployed Google Form accepts RSVP replies; the owner confirmed successful submissions. The website still cannot read Google's response because it uses `no-cors`.
- [x] Declined guests' wishes are saved through the form's third section; the owner confirmed this works.

## Site navigation

- [ ] Add small, fixed, translucent navigation controls at the lower-right of the website to move to the previous/above page and next/below page, styled to match the wedding invitation theme.
- [ ] Move the RSVP section/page to second-to-last in the site order, keeping the card's greeting/closing page as the final page.

## Launch verification and countdown

**Owner decision (19 October 2026):** Vercel hosting is working. The owner does not plan further manual deployment checks; any remaining visual checks are waived, not confirmed successful. The already confirmed checks (cross-device display, HTTPS, pages/assets, and venue directions) are recorded in [HOSTING-CHECKLIST.md](HOSTING-CHECKLIST.md).

- [ ] Update the countdown so that after the target event time passes, it clamps/freezes at zero and never displays negative values. This remains a functional change request; no further manual verification is planned by the owner.

## Sharing

The owner accepts WhatsApp not automatically generating a link preview. When sharing, they plan to attach a small logo, photo, or video with the link; no preview fix or deployment follow-up is requested.

## Build and deployment

- [ ] Decide whether to automate the Python build and check pipeline. Vercel's Git integration already auto-deploys pushes to `main`, but it deploys the committed `Website/` files and does not run the project's Python generator/checks. Until automation is added, regenerate and check `Website/` before pushing source changes so the deployed files are current.

## Design assets (waiting on supplied files)

- [ ] Add the page-8 logo if Soumya supplies the approved logo file.
- [ ] Revisit the Jaimala title font only if the full Alta font file is supplied and its licence permits web use.
- [ ] Add background music only if Soumya supplies a song; it must be started by a tap because browsers block autoplay.
