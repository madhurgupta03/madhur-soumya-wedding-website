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
- [ ] Turn on **Build Command** override and leave the command empty to skip builds.
- [x] Leave **Install Command** empty.
- [x] Keep the **Output Directory** empty with its override off. With `Website` as the root and no `public/` folder, Vercel serves that directory's static files.
- [ ] Leave environment variables unset; this site has no server runtime or deployment secrets.

## 2. Deploy the first trial

- [x] Click **Deploy** to start the Vercel deployment.
- [x] Vercel reported a successful deployment.
- [x] Save the generated URL: https://madhur-soumya-wedding-website.vercel.app/
- [x] Confirm the project is under the Hobby team.
- [ ] If deployment fails, record the first error and try the correction before changing hosting providers.

## 3. Verify the deployed site

- [ ] Open the deployment URL and confirm the envelope opens and all invitation pages display.
- [ ] Check that images and fonts load, including later pages reached by scrolling.
- [ ] Check the venue directions, countdown, blessings, and RSVP form layout.
- [ ] Open the site on an iPhone/iOS browser and an Android browser.
- [ ] Open the site on a Windows or macOS desktop browser.
- [ ] Confirm the public URL uses HTTPS without a certificate warning.
- [ ] Confirm the Google Form is reachable and still accepts responses. Do not submit a test RSVP; it would become a real response.
- [ ] Check the social preview image. The current `og:image` in `Source/pipeline/build.py` points to `https://soumyamadhurweddinginvitation.vercel.app/og-cover.jpg`.
- [ ] If the chosen project URL differs and the preview should use the new host, update `og:image` in `Source/pipeline/build.py`, then run `python3 Source/make.py build` and `python3 Source/make.py check` before redeploying. Never hand-edit generated `Website/index.html`.

## 4. Optional custom domain

- [ ] Decide whether the Vercel-provided URL is enough or whether to buy a custom domain.
- [ ] If buying one, check the exact name, first-year price, tax, minimum term, and renewal price at checkout; domain registration is normally annual.
- [ ] Add the domain in Vercel **Settings → Domains** and apply Vercel's DNS instructions at the registrar.
- [ ] Wait for DNS verification and HTTPS to become active.
- [ ] Open the custom domain on mobile and desktop and confirm it serves the same deployment.
- [ ] Update `og:image` to the final public domain if needed, rebuild, check, and redeploy.
- [ ] Save the registrar and renewal date here: ______________________________

## 5. At the end of the two-month trial

- [ ] Decide whether to leave the Vercel site online or remove its deployment/project.
- [ ] If a domain was purchased, decide whether to keep it for another year.
- [ ] If dropping the domain, turn off auto-renew before the registrar's deadline.
- [ ] Keep any RSVP responses in the Google Form; removing the site does not delete those responses.

## 6. If Vercel does not work

- [ ] Save the Vercel error or note the configuration that blocked deployment.
- [ ] Use the Cloudflare Pages fallback described in [HOSTING-OPTIONS-AND-PLAN.md](HOSTING-OPTIONS-AND-PLAN.md).
- [ ] For Cloudflare direct upload, deploy the contents of `Website/`; exclude development-only files such as `Open website.bat` if they are present.
- [ ] Repeat the verification steps above on the Cloudflare Pages URL.

## 7. Set up automatic CI/CD for Vercel

**Intended flow:** pushes to GitHub `main` should create a Vercel production deployment. A local commit by itself does not reach GitHub or deploy; it must be pushed.

### Connect and configure Vercel

- [ ] In the Vercel project, confirm **Settings → Git** is connected to `madhurgupta03/madhur-soumya-wedding-website`.
- [ ] Set the Vercel **Production Branch** to `main`.
- [ ] Confirm automatic deployments are enabled for pushes to `main`; those deployments update the production URL above.
- [ ] Keep the project **Root Directory** as `Website`, **Framework Preset** as `Other`, and the Build, Install, and Output Directory overrides empty/off. This project is currently deployed as static files from `Website/` with no Vercel build step.

### Add CI validation in GitHub

- [ ] Add a GitHub Actions workflow for pull requests and pushes to `main` that installs the Python requirements needed by `Source/make.py`.
- [ ] Run `python3 Source/make.py build` in CI when source changes need to regenerate the site, then run `python3 Source/make.py check` and require it to pass before merging.
- [ ] Ensure the generated `Website/` output is included and up to date in the commit that reaches `main`. Vercel's current settings serve `Website/` directly and do not run the source build, so source-only changes will not appear on the live site.
- [ ] Require the CI check to pass in GitHub branch protection/rules for `main` before merge, if branch protection is available for this repository.
- [ ] Open a test pull request and confirm the CI check passes. Do not submit a test RSVP; it would create a real response.

### Verify production deploys and recovery

- [ ] Push a reviewed change to `main` and confirm Vercel starts a Production deployment automatically.
- [ ] Confirm Vercel reports the deployment as **Ready**, then open the production URL and verify the changed page and key assets.
- [ ] Confirm a failed CI check blocks the PR from merging and a failed Vercel deployment is visible in the project/GitHub status.
- [ ] Record the last known good Vercel deployment. If a production deployment breaks the site, use Vercel's deployment controls to promote/rollback to that known good deployment, then fix the source and repeat CI before pushing again.
- [ ] Mark this CI/CD section complete only after the Git connection, branch settings, CI workflow, and a successful production push have all been verified. CI/CD is not yet recorded as configured.
