# Hosting and verification checklist

**Selected trial host:** Vercel Hobby (free for personal use)  
**Project:** Soumya & Madhur wedding invitation  
**Deployable folder:** `Website/`  

Tick each box as the step is completed. The hosting research, provider comparisons, pricing, and full plan are in [HOSTING-OPTIONS-AND-PLAN.md](HOSTING-OPTIONS-AND-PLAN.md).

## 1. Configure the Vercel project

- [x] Import the wedding website Git repository into a new Vercel project.
- [x] Use the Vercel project name `madhur-soumya-wedding-website`.
- [x] Set **Root Directory** to `Website`.
- [x] Set **Framework Preset** to `Other`.
- [x] Leave **Build Command** empty/off; Vercel serves the static files directly.
- [x] Leave **Install Command** empty.
- [x] Keep the **Output Directory** empty with its override off. With `Website` as the root and no `public/` folder, Vercel serves that directory's static files.
- [x] Leave environment variables unset; this site has no server runtime or deployment secrets.

## 2. Deploy the first trial

- [x] Click **Deploy** to start the Vercel deployment.
- [x] Vercel reported a successful deployment.
- [x] Save the generated URL: https://madhur-soumya-wedding-website.vercel.app/
- [x] Confirm the project is under the Hobby team.
- [ ] If deployment fails, record the first error and try the correction before changing hosting providers.

## 3. Verify the deployed site

- [x] Open the deployment URL and confirm the envelope opens and all invitation pages display.
- [x] Check that images and fonts load, including later pages reached by scrolling.
- [x] Confirm the venue directions buttons open the expected locations (owner-confirmed).
- [x] Open the site on an iPhone/iOS browser and an Android browser.
- [x] Open the site on a Windows or macOS desktop browser.
- [x] Confirm the public URL uses HTTPS without a certificate warning.
- **Owner decision (19 October 2026):** Vercel is working, and the owner does not plan to perform any further manual deployment checks. Remaining visual/manual checks are intentionally waived, not confirmed successful. Functional fixes and deferred Google Forms work remain in [OPEN-ITEMS.md](OPEN-ITEMS.md).
- **Waived, not verified:** countdown reaching and staying at zero; blessings and RSVP layout review; social preview image. The owner accepts sharing the link with an attached image/video instead of relying on WhatsApp's automatic preview.
- **Google Forms deferred:** Endpoint reachability and response acceptance have not been verified. See [RSVP open items](OPEN-ITEMS.md#rsvp); do not submit a real RSVP as a test.

## 4. Ongoing Vercel hosting

- **Custom domain:** Not needed. The owner is happy with `madhur-soumya-wedding-website.vercel.app`.
- **Plan:** Vercel Hobby is free for personal, non-commercial use and has no fixed two-month expiry or billing cycle. Usage limits apply; if a limit is exceeded, Vercel may pause the Hobby deployment or affected feature until usage resets. See [Vercel Hobby plan](https://vercel.com/docs/plans/hobby).
- **No action due:** Reconsider only if Vercel changes its terms or the project reaches a usage limit.

## 5. Two-month trial wrap-up — complete

- [x] Confirmed: no cancellation or renewal action is due after two months on Vercel Hobby. Keep the site on its Vercel-provided address; ongoing hosting remains subject to the plan's personal-use terms and usage limits.

## 6. If Vercel does not work

- [ ] Save the Vercel error or note the configuration that blocked deployment.
- [ ] Use the Cloudflare Pages fallback described in [HOSTING-OPTIONS-AND-PLAN.md](HOSTING-OPTIONS-AND-PLAN.md).
- [ ] For Cloudflare direct upload, deploy the contents of `Website/`; exclude development-only files such as `Open website.bat` if they are present.
- [ ] Repeat the verification steps above on the Cloudflare Pages URL.

## 7. Automatic deployments from GitHub

**Status:** Vercel is connected to `madhurgupta03/madhur-soumya-wedding-website`; pushes/merges to `main` have been confirmed to create Ready production deployments. No pull request previews are requested. No separate Python build/check automation or rollback note is required by the owner.

Vercel deploys the committed static files in `Website/` directly. If a source change needs regeneration, run the project build and check locally and include the updated `Website/` output in the commit; Vercel does not run the Python generator.
