# RSVP: connected to Google Forms

The website's RSVP form posts to your Google Form **"💍 Madhur & Soumya | Wedding RSVP 🎉"**.
Guest replies can be viewed in that form under **Responses**.

| Website field | Google Form question |
|---|---|
| Your name | Your name |
| Mobile number | Mobile number |
| Joyfully attending / Regretfully unable | 💌 Will you join us? (🎉 Joyfully attending / 💌 Regretfully unable) |
| Number of guests (1–10) | 👨‍👩‍👧‍👦 Number of guests, including you |
| Events (Tilak … Jaimala) | 🎊 Which events will you attend? |
| Arrival and departure details (optional) | 🚆✈️ Tell us about your arrival & departure |
| Message | 💌 A message for Soumya & Madhur |

## Keep it working
- **Don't rename or delete these questions or their options** in the Google Form. The website sends the exact option text, so if an option changes, that answer may stop being saved. If you edit the form, update the mapping in `Source/pipeline/build.py`.
- Keep **"Limit to 1 response"** and **"Collect email addresses (verified)"** turned off. Either one makes guests sign in to Google, which blocks website replies.
- Keep **"Accepting responses"** turned on until the RSVP deadline.
- To see replies as a spreadsheet: in the form, open **Responses**, then **Link to Sheets**.

## Good to know
- The RSVP resets to its intentional defaults on each visit or reload: "Joyfully attending," one guest and all events selected. Previously entered answers are not restored; the arrival/departure and message fields start blank. Personalized invitation links still pre-fill the guest's name.
- Guests who choose "Regretfully unable" skip the attendee details in section 2 and go to the wishes section 3. Their message is sent through that section; arrival/departure details are only sent for attendees.
- The browser submits with `no-cors`, so it cannot read Google's response. The thank-you screen means the browser request did not fail at the network level; it cannot confirm that Google saved the reply. `python Source/make.py check` intercepts the request locally and verifies its fields without sending a real reply.
- Replies send from the real website (Vercel) and from the local preview at http://localhost:8000. The Claude preview page blocks outside connections, so sending doesn't work there.
- The mapping lives in `Source/pipeline/build.py` (search for `var GOOGLE_FORM`). `python Source/make.py check` confirms it without sending anything.
