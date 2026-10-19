# Hosting options and two-month launch plan

**Research date:** 2026-10-19  
**Scope:** Publicly host the finished Soumya & Madhur wedding invitation for about two months, reachable by guests on phones and computers, with an optional memorable custom domain.

## Recommendation

**Trial choice: create a new Vercel project from the imported Git repository.** This repository already documents Vercel deployment, and `Website/.vercelignore` excludes the Windows helper and test page from publication. Use the free Hobby plan for this personal, non-commercial wedding invitation. Set the project root to `Website/`; choose the `Other` framework preset and skip the build command so Vercel serves the already-built files. A custom domain is a separate annual purchase. If the trial deploy does not work, Cloudflare Pages Free remains the best static-host alternative.

**Trial status:** Vercel's success screen confirms a successful project deployment to the Hobby team. The generated site URL is [madhur-soumya-wedding-website.vercel.app](https://madhur-soumya-wedding-website.vercel.app/). Device-by-device and RSVP verification are still pending; use [HOSTING-CHECKLIST.md](HOSTING-CHECKLIST.md) to track them.

**Project readiness:** the site is already suitable for Vercel; no application-code change is needed to host it. The import configuration is the important part: Vercel project root `Website`, framework `Other`, and an empty overridden build command. The existing `og:image` points to the currently planned Vercel hostname; update it in `Source/pipeline/build.py` only if the final hostname should serve the social preview from a different address, then rebuild and check.

For the lowest cost, use the host-provided address (such as the existing `*.vercel.app` target, if it is still available) and spend **₹0**. To use a chosen `.in` or `.com` domain, budget about **₹899 or ₹1,499 for the first year**, respectively, at the current displayed Hostinger list prices. Thus the two-month hosting charge is still ₹0; the one-year domain registration is the paid part. A domain is not rented month-by-month.

## What this project needs

- The finished site is a generated static website in `Website/`: `index.html`, local image and font assets, and the link-preview image. There is no application server or server-side build requirement after the output is built.
- The current `Website/` folder occupies about **23 MB**. Artwork is about 22 MB and loads by page, with only the first two pages loaded up front. Cloudflare Pages' current Free limits include 20,000 files and 25 MiB per individual asset; this site is comfortably below both based on the current files.
- RSVP runs in the visitor's browser and submits to Google Forms; there is no separate RSVP server to host. Keep the Google Form accepting responses and preserve its question/option text. See [RSVP setup](RSVP-SETUP.md). Do not submit a live test RSVP without the owner's approval; project checks can validate the mapping without sending a response.
- The HTML includes a mobile viewport declaration, 9:16 page sizing rules, reduced-motion handling, and lazy loading. A public HTTPS URL works in ordinary browsers on iPhone/iPad, Android, Windows, and macOS; the host does not require a platform-specific app. Actual screen layout and form usability still need a post-launch review on representative devices.
- The generated HTML currently sets `og:image` to `https://soumyamadhurweddinginvitation.vercel.app/og-cover.jpg` in `Source/pipeline/build.py`. If the final hostname changes, update that absolute URL in the source, rebuild, and redeploy so WhatsApp and other social previews fetch the image from the live host. Never hand-edit generated `Website/index.html`.
- The `.vercel.app` address is a Vercel-provided subdomain, not proof that a separately purchased custom domain is already owned. Verify access to the existing Vercel project and hostname before relying on it.

## Hosting comparison

Costs below are hosting fees for two months, with domain registration shown separately. USD conversions use the European Central Bank's 2026-10-16 reference rates: EUR 1 = USD 1.1253 and EUR 1 = INR 106.864, giving **USD 1 ≈ ₹94.9649** by division. The conversions are estimates before card FX spreads, GST, or other checkout taxes.

| Host | Static hosting, 2 months | Custom domain support | Fit and important limits |
|---|---:|---|---|
| **Vercel Hobby** | **₹0** | Yes; connect a domain bought from Vercel or another registrar; automatic SSL | Best low-friction fit because the project already documents Vercel and includes `.vercelignore`. Hobby must remain personal/non-commercial. Free plan details: [Hobby](https://vercel.com/docs/plans/hobby); custom domains: [Add a domain](https://vercel.com/docs/domains/working-with-domains/add-a-domain); [pricing](https://vercel.com/pricing). |
| **Cloudflare Pages Free** | **₹0** | Yes; custom apex domain requires its zone/nameservers on Cloudflare; subdomain can use a CNAME | Strong static alternative: 500 builds/month, 100 custom domains/project, 20,000 files, 25 MiB per file; static asset requests/bandwidth are free/unlimited. Use direct upload for prebuilt files. [Limits](https://developers.cloudflare.com/pages/platform/limits/), [static request pricing](https://developers.cloudflare.com/pages/functions/pricing/), [custom domains](https://developers.cloudflare.com/pages/configuration/custom-domains/), [direct upload](https://developers.cloudflare.com/pages/get-started/direct-upload/). |
| **GitHub Pages / GitHub Free** | **₹0** | Yes | Requires a public repository on GitHub Free. Soft 100 GB/month bandwidth and published site max 1 GB. Pages is not intended for sites primarily facilitating commercial transactions; this personal invite is a simple static site. [Free plan](https://github.com/pricing), [custom domains](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site), [usage limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits). |
| **Netlify Free** | **₹0** | Yes, with SSL | 300 credits/month, hard cap and no automatic recharge on Free; a project may pause if it reaches the limit. Ample for normal static usage, but the cap is less predictable than Cloudflare's static-asset pricing. [Pricing](https://www.netlify.com/pricing/), [credit plan details](https://docs.netlify.com/manage/accounts-and-billing/billing/billing-for-credit-based-plans/credit-based-pricing-plans/). |
| **Netlify Personal** | **$18 ≈ ₹1,709** | Yes | Optional paid tier at $9/month; not needed for this site. Pricing can change and USD card conversion/taxes can add cost. [Pricing](https://www.netlify.com/pricing/). |
| **Vercel Pro** | **$40 ≈ ₹3,799** | Yes | Optional paid tier at $20/month; not needed for personal wedding site. [Pricing](https://vercel.com/pricing). |
| **Hostinger shared hosting** | No useful two-month total advertised on the cited page | Yes; eligible longer-term plans include a domain for a year | The India page advertises discounted prices averaged across a 48-month prepaid term, not month-to-month billing: Single ₹3,312 upfront for 48 months (shown as ₹69/mo; renews ₹289/mo); Premium ₹6,672 upfront (shown as ₹139/mo; renews ₹449/mo). It is a poor two-month fit when a static host is free. [India web hosting pricing](https://www.hostinger.com/in/web-hosting). |

**Hosting cost in two months:** ₹0 on each of the listed free plans, subject to the stated fair-use and usage rules. Paid optional plan totals are shown only for comparison; none is needed here.

## Domain budget (separate from hosting)

Most domain registrations are sold in annual terms, so even a two-month publication means paying for at least the first year. Hostinger's [India domain search](https://www.hostinger.com/in/domain-name-search?lang=en) currently displays list prices of ₹899 for `.in` and ₹1,499 for `.com`, alongside ₹1 first-year promotions. Its [domain page](https://www.hostinger.com/in/domains) says the `.com` ₹1 offer requires a three-year term and standard renewal applies after the first year. The promotional display should therefore not be treated as the cost of a two-month domain rental; confirm the actual name, term, tax, and checkout total before purchase. The domain search FAQ states the minimum registration period is one year.

| Domain choice | Budget for year one | Hosting for two months | Estimated combined spend |
|---|---:|---:|---:|
| `.in` at displayed list price | ₹899 | ₹0 | **₹899** |
| `.com` at displayed list price | ₹1,499 | ₹0 | **₹1,499** |
| Existing domain already owned and paid through its renewal date | ₹0 incremental | ₹0 | **₹0 incremental** |
| Vercel `*.vercel.app` / Cloudflare `*.pages.dev` host address | ₹0 | ₹0 | **₹0**, but it is a provider subdomain rather than a purchased custom domain |

If registering with Cloudflare Registrar instead, it sells supported TLDs at registry/ICANN cost with no markup ([registrar overview](https://developers.cloudflare.com/registrar/about/)). Its API documentation's example gives `.com` USD 8.57 registration/renewal, approximately ₹814 using the stated FX rate, but that is an example, not a live quote; check the chosen available domain immediately before checkout ([pricing/availability API guide](https://developers.cloudflare.com/registrar/registrar-api/)). A Cloudflare-registered domain uses Cloudflare nameservers ([register a domain](https://developers.cloudflare.com/registrar/get-started/register-domain/)).

### India-focused wedding-site services (not comparable to static hosting)

These are vendor-reported wedding-builder/service prices, not first-party commodity hosting rates. The linked product pages describe publishing inside each vendor's builder; I found no documented static-file upload path for this repository's `Website/` files. Treat them as replacements for the approved custom site, not hosts for its current static build, unless a vendor confirms otherwise. Confirm plan duration, custom-domain ownership, RSVP export/data handling, and taxes with each provider before choosing.

| Service | Publicly displayed offer | Custom domain / duration notes | Practical caveat |
|---|---|---|---|
| [Vowframes](https://www.vowframes.com/pricing) | Silver ₹2,999 one-time, 3 months; Gold ₹5,999, 6 months; Platinum ₹9,999, 12 months | Silver lists custom-domain setup as ₹499 plus registrar cost; Gold/Platinum list a custom domain as included | Closest duration-based package option, but still costs more than a year's basic domain plus free hosting, and would mean moving to its builder. Price/features are reported by the vendor. |
| [Varumo](https://varumo.com/) | From ₹799 (page also shows ₹1,598) | Site link shown under `varumo.com/<name>`; custom domain may be added at checkout, but exact add-on price/term was not clear on the public page | Confirm custom-domain price and exact live term before treating this as a custom-domain quote. Its template/RSVP model would replace the existing site. |
| [TyingKnot](https://www.tyingknot.in/) | ₹1,575 | Advertises a custom subdomain and 3- or 6-month term; the public custom-domain FAQ did not state a clear answer/price | Its short term suits an event microsite, but custom-domain availability/price is unresolved and the current design/Google Forms RSVP behavior would need to be recreated. |
| [ShaadiPath bespoke](https://www.shaadipath.com/custom) | From ₹19,999 one-time | Advertises an included custom `.in` domain, RSVP, custom design and 2 revision rounds | Bespoke done-for-you service; far outside the low-cost hosting target, but includes design labour rather than just hosting. |
| [Riwaaz](https://www.riwaaz.in/invitations/website) | Basic package currently shown as ₹9,999 launch offer (₹12,999 list) | Promotes multi-event per-ceremony RSVP; custom-domain registration charges depend on the chosen domain | Indian multi-event feature fit; vendor says premium package adds its own domain setup. This is a new hosted wedding page rather than deployment of the current generated files. |
| [SaveOurDate](https://saveourdate.in/) | ₹299–₹1,499 one-time, depending on template | Vendor subdomain; vendor says link stays live through the wedding and one month after | Short event term and RSVP dashboard/CSV export; no documented static upload or custom-domain purchase on the public pricing information. It would replace this design. |
| [Weddinsite](https://www.weddinsite.com/) | Build/preview free; site says ₹999 one-time to publish (final price at checkout) | Publish plan lists a vendor vanity URL, RSVP tracker and guest features; exact term/expiry is not stated publicly | Low advertised price, but no documented static upload. Confirm final checkout price, post-event availability, and RSVP export/privacy requirements. |
| [WeaveCards](https://weavecards.com/pricing) | ₹1,999–₹3,999 once | Vendor subdomain; publish lasts one year, then website and guest replies are erased | RSVP export and WhatsApp-oriented sharing are included per vendor page; no documented static upload or external custom-domain option on the pricing page. |
| [Wedence](https://wedence.in/pricing) | Free tier (two designs free; other designs ₹999–₹1,499 each); Pro ₹3,999 once; Signature ₹7,999 once; Concierge ₹19,999 once | Custom domain listed with Concierge; lower tiers use platform pages. Free tier reports RSVP counts only; higher tiers offer detailed guest operations. | Strong multi-event/guest-management product, but no documented static upload; it is a wedding invitation/operations platform, not a host for this repository's files. |

## Brainstorming and dependency-ordered plan

Planning is complete for this hosting decision. The brainstorming pass established the goal (share the existing invite reliably across devices for about two months), constraints (preserve the approved design, static `Website/` artifact, browser-based Google Forms RSVP, low cost, optional owned domain), and alternatives (reuse Vercel, compare free static hosts, or replace the site with a wedding-specific builder). The writing-plans pass sequenced the work by dependency:

1. **Completed — inspect the project and identify its hosting shape.** Confirmed static `Website/` output, approximately 23 MB total, client-side RSVP, Vercel instructions and ignores, mobile viewport, lazy loading, and current social preview hostname.
2. **Completed — compare hosting and domain costs.** Checked current vendor-published plans and terms; separated recurring hosting from annual domain registration; recorded the USD conversion basis and limitations above.
3. **Completed — select the trial host.** Vercel Hobby is the chosen first attempt; if the Git import or deploy fails, switch to Cloudflare Pages Free. Either costs ₹0 for two months of static hosting.
4. **Completed — import the repository.** The owner has imported the wedding website repository into Vercel's new-project flow.
5. **In progress — configure the imported repository.** Choose `Website/` as the project root, select `Other`, leave the install command empty, and override the build command with an empty value to skip building. Let the output directory default to the project root.
6. **Pending deployment — publish the generated artifact.** Keep source edits in `Source/pipeline/build.py`; rebuild and run the project's check after any metadata update; deploy `Website/` as static files.
7. **Pending owner action — choose a hostname.** First test the Vercel-provided URL. Decide later whether to register an available `.in`/`.com` name for one year; check final price, tax, and renewal settings at checkout.
8. **In progress — verify the deployment.** Vercel reports successful deployment to `https://madhur-soumya-wedding-website.vercel.app/`. Open it and check HTTPS, pages/assets and RSVP layout on phone and desktop browsers, and verify the link preview. Do not create a live RSVP test response without approval.
9. **Pending later decision — keep or retire after the two-month window.** Hosting may remain on the free tier; remove the deployment only if it should go offline. Keep or disable domain auto-renew based on whether the address should remain owned for next year.

No hosting account, domain, DNS, or deployment has been changed as part of this research/documentation.

## Deployment steps

### Option A: Vercel Hobby (selected trial)

1. In Vercel's new-project form, select the imported Git repository. Use the Vercel-provided hostname for the first trial; adding a custom domain is optional and costs separately.
2. Set **Root Directory** to `Website`, **Framework Preset** to `Other`, enable **Build Command → Override** and leave the command blank, and leave the install command blank. Keep the output directory at its default project root; with this configuration Vercel serves the static files in `Website/` directly. Vercel's [build configuration documentation](https://vercel.com/docs/builds/configure-a-build) describes the no-build setup.
3. Click **Deploy**. `Website/.vercelignore` excludes `test.html` and `Open website.bat`.
4. If changing the hostname and the preview image should use the new host, edit the `og:image` absolute URL in `Source/pipeline/build.py`, then run `python3 Source/make.py build` and `python3 Source/make.py check` before redeploying. Never hand-edit generated `Website/index.html`.
5. For an optional custom domain, use **Settings → Domains**, apply Vercel's displayed DNS instructions at the registrar, then wait for DNS verification and SSL activation.

For a new project imported from Git, set **Root Directory** to `Website`, **Framework Preset** to `Other`, and enable the **Build Command** override with the command field left empty. Leave the install command empty. Since `Website/` has no `public/` directory, Vercel serves the root of that project directory as static output. Vercel documents this no-build configuration in [Configure a Build](https://vercel.com/docs/builds/configure-a-build). Do not set the root to the repository root or point the output directory back to `Website` after selecting that root.

### Option B: Cloudflare Pages Free

1. Build/check the site as above; create a Pages project using **Direct Upload** and upload the prebuilt files from `Website/` (dashboard accepts a folder or ZIP; Wrangler accepts a folder). It will receive a `*.pages.dev` address.
2. If using a custom apex domain, add the domain as a Cloudflare zone and point its nameservers to Cloudflare. Add the domain under **Workers & Pages → project → Custom domains**; for a subdomain on external DNS, add the instructed CNAME after associating it in Pages. Follow the dashboard instructions and wait for activation/SSL.
3. Note: `.vercelignore` is Vercel-specific. Before uploading to another platform, inspect the upload contents and exclude any development-only artifacts if present. The current folder listing contains `Open website.bat`; it is not required by visitors.

## Post-launch checks

Use the separate tickable [hosting and verification checklist](HOSTING-CHECKLIST.md) to track import, deployment, post-launch checks, optional custom-domain setup, and the two-month decision.

- Open the public HTTPS URL on one iPhone/iOS browser and one Android browser, plus a Windows or macOS desktop browser. Confirm envelope opening, all card pages, venues/maps, countdown, blessings and RSVP layout.
- Confirm there are no missing images/fonts and that scrolling continues to load later sections; the artwork is intentionally lazy-loaded and roughly 23 MB of site assets are not all loaded at once.
- Confirm the public URL, host, and final custom domain all resolve to the same site, and HTTPS works on apex/`www` variants that are configured.
- Inspect the rendered HTML/metadata from a fresh deployment and check that `og:image` resolves at the selected host. Paste the public address into the intended sharing app and confirm the preview; cached previews may take time to refresh.
- Check the Google Form still accepts answers and the live RSVP fields/options remain as documented. Do not send a test submission unless separately approved because it becomes a real response.

## After the two months

- Free Vercel/Cloudflare/GitHub/Netlify hosting has no two-month paid subscription to cancel. If the site should stay online, leave the project deployed; if it should go offline, remove the project/deployment deliberately.
- A registered domain remains an annual registration even if the deployment is removed. If keeping the domain, leave renewal on and budget the registrar's renewal price. If dropping it, disable auto-renew in advance; Cloudflare says its auto-renew attempt begins about 30 days before expiry, and Hostinger provides renewal controls/reminders. Confirm the chosen registrar's deadlines and renewal price in its dashboard.
- If the hostname changes or the domain expires, update/remove the old social-preview reference in `Source/pipeline/build.py` through the normal build, check, and redeploy workflow.

## Price assumptions and source notes

- Vendor plan and domain prices were checked on **2026-10-19**. Promotional prices and domain availability change; the domain name itself has not been searched/reserved, so the figures are planning estimates rather than a checkout quote.
- The ECB's 2026-10-16 reference observations were EUR 1 = INR 106.864 and EUR 1 = USD 1.1253, implying USD 1 ≈ INR 94.9649. See the official [ECB INR series](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/eurofxref-graph-inr.en.html) and [ECB USD series](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/eurofxref-graph-usd.en.html). Payment-card FX spreads and any applicable taxes can change the final INR charge.
- Prices in the wedding-builder table are those publicly displayed by the service vendors, not independently quoted by a registrar or static-host vendor. Their exact domain ownership/renewal and response-export terms should be confirmed before purchase. Public pages reviewed do not document deployment of an existing static site bundle; assume a builder migration unless the vendor confirms otherwise.
- This is a comparison of suitable mainstream and wedding-specific options, not an exhaustive survey of every hosting provider.
