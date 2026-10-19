# RSVP: connected to Google Forms

The website's RSVP form is connected to your Google Form **"💍 Madhur & Soumya | Wedding RSVP 🎉"**.
Every reply from the website appears in that form under **Responses**.

| Website field | Google Form question |
|---|---|
| Your name | Your name |
| Mobile number | Mobile number |
| Joyfully attending / Regretfully unable | 💌 Will you join us? (🎉 Joyfully attending / 💌 Regretfully unable) |
| Number of guests (1–20) | 👨‍👩‍👧‍👦 Number of guests, including you |
| Events (Tilak … Jaimala) | 🎊 Which events will you attend? (🌸 Tilak (24 Nov) … 💐 Jaimala (25 Nov)) |
| Message | 💌 A message for Soumya & Madhur |

## Keep it working
- **Don't rename or delete these questions or their options** in the Google Form. The website sends the exact option text, so if you change "🌸 Tilak (24 Nov)", Tilak answers stop being saved. If you need to edit the form, tell Claude and the website will be updated to match.
- Keep **"Limit to 1 response"** and **"Collect email addresses (verified)"** turned off. Either one makes guests sign in to Google, which blocks website replies.
- Keep **"Accepting responses"** turned on until the RSVP deadline.
- To see replies as a spreadsheet: in the form, open **Responses**, then **Link to Sheets**.

## Good to know
- Guests who choose "Regretfully unable" skip straight to the end in your Google Form, the same as on the website. Their message is sent too, but Google doesn't save it, because the message question is on the form's second page (confirmed with a test). To fix this, drag "💌 A message for Soumya & Madhur" above the "🥳 Hurray!" section break in the Google Form.
- Replies send from the real website (Vercel) and from the local preview at http://localhost:8000. The Claude preview page blocks outside connections, so sending doesn't work there.
- The mapping lives in `Source/pipeline/build.py` (search for `var GOOGLE_FORM`). `python Source/make.py check` confirms it without sending anything.
