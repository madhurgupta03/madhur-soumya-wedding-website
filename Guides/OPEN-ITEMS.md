# Open items

Use this list for work that is still pending. Check an item only after the change or follow-up is complete.

## RSVP

**Deferred/open:** Google Forms integration work and verification are deferred. Do not treat the form integration as successful or verified; the following integration issues and audit remain open.

- [ ] Fix RSVP mobile-number validation: during the owner's manual check, the mobile-number field accepted letters.
- [ ] Review RSVP submission-error placement: the owner reports the error message appears near the submit button instead of immediately after the dialog box. The submit button has not been clicked, so this error state has not been reproduced or verified.
- [ ] Investigate the reported Google Forms integration behavior: only the “Regretfully unable to come” response works; the attending choice and number-of-attendees/guest-count values reportedly do not work. This report has not been independently verified.
- [ ] Audit the current Google Form against the website integration for questions, fields, and options that were added, removed, or renamed; update the website mapping as needed. Keep this integration open until the comparison is complete and RSVP responses work.
- [x] Reset RSVP answers on every visit or reload. Keep the intentional defaults (Joyfully attending, 1 guest, all events selected), leave other answers blank, and preserve personalized invite-name prefill.
- [ ] (Deferred) Verify the Google Forms endpoint accepts the RSVP data. The form opened and the fields were inspected, but no response was submitted; do not submit a real RSVP as a test.
- [ ] Ask Soumya to move the optional message question into section 1 of the Google Form so guests who decline can have their message saved.

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
