# Soumya & Madhur e-invite — change checklist

Source: `Soumya_Madhur_invite_original_pdf.pdf` (approved design). Changes taken from `Madhur_Soumy_wedding_invite.pdf` (review comments).
Everything not listed below is copied from the original PDF unchanged.

## Changes made

| # | Page | Change requested | What was done | Where in the site |
|---|------|------------------|---------------|-------------------|
| 1 | 2 | Replace lorem-ipsum parent names | "Daughter of Mrs. Rashmi Gupta & / Mr. Umakant Gupta" and "Son of Mrs. Bhavna Gupta & / Mr. Santosh Gupta". Same font (Crimson semibold), 28 pt, colour #b85c1d, letter spacing, two-line break after "&", same baselines, centred on the original lines | `#page-2`, the two `<text>` pairs |
| 2 | 2 | Slightly less letter spacing in "Soumya Gupta" / "Madhur Gupta" | Spacing between letters reduced so each name is 5% narrower; still centred where it was | `#page-2`, script name glyphs |
| 3 | 2 | Slightly less letter spacing in "॥ श्री गणेशाय नमः ॥" | The 0.86 pt extra spacing between characters removed (line about 6% narrower); still centred | `#page-2`, Hindi line |
| 4 | 3–7 | Venue address: remove bold, slightly smaller | Crimson semibold italic 34.5 pt → Crimson regular italic 31 pt on Tilak, Engagement & Sangeet, Haldi & Mehendi, Baraat and Jaimala. Colour, line breaks, centring and the top of the text kept | `#page-3` to `#page-7`, venue `<text>` lines |
| 5 | 3–7 | One identical gap between event title and date | Every event page now uses the gap that Engagement and Baraat already had: 50.1 pt from the bottom of the title letters to the top of the date (before: Tilak 59.2, Engagement 49.7, Haldi 46.0, Baraat 50.5, Jaimala 31.4). The date, time, ornament and venue did not move; only the titles moved | `#page-3` to `#page-7`, title glyphs |
| 6 | 4 | Title "ENGAGEMENT / small & / SANGEET", remove "CEREMONY" | Done, three lines, "&" at half the title size, same title font (Alta), white, centred | `#page-4` |
| 7 | 5 | Title "HALDI / small & / MEHENDI" | Done, three lines, "&" at half the title size, same title font and colour, centred | `#page-5` |
| 8 | 1 | Add "Soumya & Madhur" below the monogram (requested after first preview) | Added in the same lettering as the names on page 2: script font in #784646 with the italic "&" in #b85c1d, at 70% of the page 2 size (44 pt names, 27 pt "&"). Centred just below the monogram (14 pt gap) | `#page-1` |

## Decisions

| Item | Decision |
|------|----------|
| Page 1: add "Soumya & Madhur" | Added (see change 8) |
| Page 1: add dates | Left as is |
| Page 7: Jaimala title font | **Kept in the original script font.** The title font (Alta) is only partly embedded in the PDF and has no letter "J", so "Jaimala" cannot be set in it without the full font file |
| Page 8: logo | Left as is (no logo file was attached) |
| Page 8 text | Unchanged |
| Tilak time | 4:30 PM onwards, as in the PDF |
| Page 7 colours | Kept exactly as in the PDF (date #04112a, venue #000000) |

## Website features (added after the card was approved)

| Feature | Details |
|---------|---------|
| Always starts from the envelope | Every visit and every reload opens at the closed envelope, never part-way down the page |
| Envelope opening | Guests first see a closed envelope with a rust wax seal. One tap plays a smooth sequence (about 5 seconds): the seal pops with gold sparkles, the flap swings open, the card slides all the way out of the envelope, the empty envelope fades away, the card settles with its SM logo over the spot where the cover's logo sits, and then the card and the cover crossfade (the card fades out as the cover fades in). A "Skip" link is always available |
| Gentle reveals | Text on each page and section rises softly into view the first time it is scrolled to. The artwork itself never moves |
| Falling flowers | Pink rose petals, small marigolds and a few green leaves drift and tumble down, the way leaves fall, on every page and section (lighter on the venue, RSVP and blessings sections). They never block taps, and pause when off-screen to save battery |
| Sparkle | A shower of gold sparkles bursts from the wax seal when the envelope opens, and a few soft gold stars twinkle on and off across every page and section |
| Countdown | Live days / hours / minutes / seconds until the Tilak (24 Nov 2026, 4:30 PM IST) at the top of "Where we celebrate" |
| Reduced motion | Phones set to "reduce motion" get no petals and no movement; everything shows straight away |
| Tap to open | "Tap to open" under the names on the cover scrolls to the invitation |
| Directions on the cards | A "Get directions" button under the venue on all five event pages: Tilak and Engagement & Sangeet (Havana Restro), Haldi & Mehendi, Baraat and Jaimala (Royal Resort). On Jaimala the button sits slightly right of centre, in the clear sky beside the peacock, so it doesn't cover its neck |
| Where we celebrate | New section after the event cards: Day 1 at Havana Restro (Tilak 4:30 PM, Engagement & Sangeet 7:00 PM) and Day 2 at The Royal Resort Orchha (Haldi & Mehendi 11:30 AM, Baraat 7:00 PM, Jaimala 9:00 PM), each with directions |
| RSVP form | After the venues section: name, mobile, attending (yes/no), number of guests and which events (shown only if attending), and an optional message. Replies go straight into your Google Form once it is connected (see RSVP-SETUP.md) |
| With Blessings Of | Two pages: the bride's side, with the "Lovingly invited by Umakant Gupta & Santosh Gupta" box on top, then the groom's side on its own page. Names taken from the old website |
| WhatsApp / link preview | `og-cover.jpg` (cover monogram and names) shows when the link is shared. It points to soumyamadhurweddinginvitation.vercel.app, so deploy to that address or update the `og:image` line |
| Style | Each website section is a framed card: cream paper with a double gold border and the card's ornament in each corner, on a coloured background from the artwork (night blue for the venues and the groom's side, rose for RSVP, marigold for the bride's side). Day, side and family headings sit in coloured bands, events and relations in tinted rows and tags. Text is the same reading size as the card pages (about 16–23 px on a phone) |

## How it was built

- **Artwork:** all 16 images extracted from the PDF at their native pixel size, saved as lossless PNG with their original colour profile, and placed with the PDF's own position, rotation and opacity. They were not cropped, resized, recompressed or recoloured. The 40% opacity on the page 2 and page 8 skies comes from the PDF.
- **Colours:** every text and ornament colour is the exact value from the PDF.
- **Text:** unchanged text is drawn with the PDF's own letter shapes at the exact PDF positions. New or restyled text (parent names, venue) uses Crimson Text, the free version of the same Crimson font, included in `fonts/`.
- **Pages:** each page is one 9:16 section. On phones it fills the width and you scroll page by page. On wider screens it is centred, with the page's paper colour (#fdf5ef) at the sides.
- **Checked:** each page was rendered in Chrome and compared with the PDF. Apart from the listed changes, the pages match except for normal image-smoothing differences.

## Source code

Everything is rebuilt from the PDF by `python Source/make.py all`. See `CLAUDE.md` for the workflow.

## Files

- `index.html` — the whole site
- `images/` — extracted artwork (about 22 MB)
- `fonts/` — Crimson Text (SIL Open Font License)

To publish: upload this folder to Vercel (or any static host) as is.
