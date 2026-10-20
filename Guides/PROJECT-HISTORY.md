# Project history — every instruction from Soumya, in order

This is the full record of what was asked and what was decided, so a new session can continue without the original conversation.
The current state of the site is described in `CLAUDE.md` and `Guides/CHECKLIST.md`. Where this history and those files disagree, **the later instruction wins**.

## 0. Background

- An earlier e-invite already existed at https://soumyamadhurweddinginvitation.vercel.app/ (built by someone else; its code isn't available).
- That old site wrongly said both days were at The Royal Resort Orchha. **Correct:** Tilak, Engagement and Sangeet are at **Havana Restro, Jhansi**. Haldi & Mehendi, Baraat and Jaimala are at **The Royal Resort Orchha**. "Havana Resort" and "Havana Restro" are the same place; the site uses the Google Maps name, **Havana Restro**.
- Soumya asked for a new invite "which doesn't feel so AI/Claude generated". A first red-and-gold draft (`Archive/first-draft-site/`) was replaced by the PDF-based build below.

## 1. The main brief (verbatim, as given with the two PDFs)

> Attached are two PDFs of Soumya & Madhur's wedding e-invite (8 pages each, 810 × 1440 pt):
> 1. ORIGINAL.pdf: the approved design.
> 2. REVIEWED.pdf: the same design with review comments.
>
> TASK
> Build a single-page, vertically scrolling e-invite website. Each PDF page becomes one full-screen section, in the same order and with the same 9:16 proportions. Copy ORIGINAL.pdf exactly. Change only what is listed under CHANGES below.
>
> NON-NEGOTIABLE
> - Colours: Use the exact colour values from the PDF for every background, text, ornament and divider. No substitute shades and no contrast changes.
> - Artwork: Extract each background illustration from the PDF at its original resolution. Never screenshot, compress, crop, stretch or recolour it. Every background was approved as it is.
> - Layout: Same positions, alignment, margins and spacing. Do not add, remove or reorder anything unless CHANGES lists it.
> - Text: Copy every word exactly, including the Hindi line "॥ श्री गणेशाय नमः ॥".
> - Fonts: Same fonts as the PDF, unless CHANGES says otherwise.
> - No placeholders, no simplifications and no design ideas of your own.
>
> CHANGES (apply these and nothing else)
> Page 2 (Families)
> - Replace the lorem-ipsum parent names with:
>   Soumya: "Daughter of Mrs. [MOTHER'S NAME] & Mr. [FATHER'S NAME]"
>   Madhur: "Son of Mrs. [MOTHER'S NAME] & Mr. [FATHER'S NAME]"
> - Slightly reduce the letter spacing in the script names "Soumya Gupta" and "Madhur Gupta" and in the "॥ श्री गणेशाय नमः ॥" line.
>
> Pages 3 to 7 (events: Tilak, Engagement & Sangeet, Haldi & Mehendi, Baraat, Jaimala)
> - Venue address text: remove the bold and make it slightly smaller. Apply the same style to every event page.
> - Use one identical vertical gap between the event title and the date line on every event page.
>
> Page 4: Change the title to "ENGAGEMENT", then a small "&", then "SANGEET", on three lines. Remove the word "CEREMONY".
>
> Page 5: Change the title to "HALDI", then a small "&", then "MEHENDI", on three lines.
>
> Page 7: [DECIDE: keep the "Jaimala" script font / change it to the same title font as the other event pages]
>
> Page 1 (Cover): No change, except:
> - [DECIDE: add "Soumya & Madhur" below the monogram / leave as is]
> - [DECIDE: add the dates below that / leave as is]
>
> Page 8 (Closing): Keep the text unchanged.
> - [DECIDE: add a small logo in the centre, below the text, using the attached file / leave as is]
>
> OUTPUT
> 1. The complete website code: one HTML file, with the extracted images saved alongside it.
> 2. A checklist mapping each change above to where you made it.
> If anything is unclear, ask before you change it. Do not guess.

### How the open items were settled
| Item | Decision |
|---|---|
| Parent names | Mrs. Rashmi Gupta & Mr. Umakant Gupta (Soumya), Mrs. Bhawana Gupta & Mr. Santosh Gupta (Madhur); confirmed by Soumya |
| Tilak time | 4:30 PM, as in the PDF (the old site said 3:00 PM) |
| "Slightly" values | venue 34.5 → 31 pt regular italic; names 5% narrower; Hindi line extra spacing removed; title-to-date gap 50.1 pt on all event pages |
| Jaimala font | Kept as script. The title font (Alta) has no "J" in the PDF, so it can't be switched without the font file |
| Page 1 names | Added later at Soumya's request: just below the monogram, smaller (70% of the page-2 names) |
| Page 1 dates | Not added |
| Page 8 logo | Not added: no logo file supplied |
| Page 7 colours | Kept exactly as in the PDF |
| Fonts | Unchanged text uses the PDF's own letter shapes; new or restyled text uses Crimson Text (free version of the PDF's Crimson) |

## 2. Later requests, in order (all implemented)

1. Recheck every review comment end to end. A full check showed 10 comments done; Jaimala font and page-8 logo still open; page-1 dates optional. See `Previews/Review-vs-website.png`.
2. Turn the card into a proper website: directions buttons, a "Where we celebrate" section with both venues, the family blessings list from the old site, and a link-preview picture.
3. Add an RSVP form inside the website, with fields for name, mobile, attending, number of guests, which events, and a message.
4. Show all RSVP fields straight away. Guest count and events only hide when "Regretfully unable" is chosen.
5. Connect the RSVP directly to Google Forms. Soumya created the form herself; the site posts into it. Two test replies were sent (with permission) and arrived. A decliner's message isn't saved because the message question is in the form's 2nd section; Soumya was told how to fix this in the form.
6. Animations: envelope opening, gentle reveals, countdown to the Tilak.
7. Add a directions button to the Jaimala page as well (placed beside the peacock).
8. Falling flowers, "like leaves fall", on all pages: petals, marigolds and a few leaves.
9. Add sparkle: a gold burst when the seal opens, plus twinkling stars.
10. The website sections' text was "way too small": make it the same reading size as the cards, and add borders, colours and structure (framed panels, coloured bands).
11. Split the bride's side and the groom's side into separate pages.
12. A reload must always start from the beginning (the envelope).
13. Envelope opening was choppy. First rework: the logo glided and scaled onto the cover logo. Then refined to a zoom in place.
14. **Reverted** the glide/zoom (Soumya: not fading out properly; the card didn't come fully out of the envelope; the envelope vanished choppily; the final alignment was choppy). **Current version:** the card slides fully out, the envelope fades, then a crossfade between the card and the cover. Earlier versions are in `Archive/earlier-build-versions/`.
15. Set up this folder as a complete, self-contained project with instructions for a new Claude session.
16. Added a high-resolution transparent illustration of a faceless bride in a powder-pink lehenga placing a varmala on the groom in a white sherwani to the Jaimaala page. The bride already wears her own varmala; her proportions are only slightly fuller than the first draft. The original page artwork, text, fonts, and textures are preserved, and the Get Directions button is omitted from this page. The change is part of the local main build; it has not been deployed.

## 3. Places outside this folder

| What | Where |
|---|---|
| Old live site (to be replaced) | https://soumyamadhurweddinginvitation.vercel.app/ |
| Google Form editor (Soumya's account) | https://docs.google.com/forms/d/1KIkRrLeCScyQz9D6GxDSO4pL7pF5aaTd7-_FSHoLAsk/edit |
| Google Form public link | https://docs.google.com/forms/d/e/1FAIpQLSfnBOj2V0I5WwqbaIJzzUCkaqaY4ZEuZ3dqVqI0_m0bwpd1yA/viewform |
| Havana Restro on Google Maps | https://maps.app.goo.gl/NSd9deR3CCMiEXvz9 |
| Private Claude preview of the site (Soumya's account only) | https://claude.ai/artifact/Hz5YpD2swDs8G8k58yJzVa |
