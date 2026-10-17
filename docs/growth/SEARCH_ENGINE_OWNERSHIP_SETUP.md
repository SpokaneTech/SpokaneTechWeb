# Search engine ownership setup for SpokaneTech.org

Last reviewed: October 17, 2026.

The domain owner manages DNS through Namecheap. This guide covers manual setup
of Google Search Console and Bing Webmaster Tools. It documents the procedure;
it does not confirm that either service has been configured or verified.

Owner update: Google verification is in progress and is considered complete for
planning purposes. The repository SEO implementation is ready; follow the
[rollout guide](SEO_IMPLEMENTATION_AND_ROLLOUT.md) for production settings,
sitemap submission, and verification-dependent checks. DNS propagation does not
block preparing or deploying the application changes.

## Why this is being done

SpokaneTech.org aims to help local people discover technology events and groups.
Search engine tools help us understand whether people can find those pages and
what prevents useful content from appearing in search results.

- **Google Search Console** reports Google search impressions, clicks, search
  queries, indexing status, and crawl/indexing problems. It provides URL
  inspection and sitemap submission tools.
- **Bing Webmaster Tools** provides similar visibility into Bing search and
  tools for inspecting URLs and submitting sitemaps.
- **Google Analytics**, already used by the website, measures activity after
  visitors arrive. It does not replace search-engine indexing reports.

Ownership verification proves control of the website before these services give
an account access to its reports and management tools. It does not transfer domain
ownership, change the website's hosting, or guarantee search rankings.

The [SEO and organic traffic plan](SEO_AND_ORGANIC_TRAFFIC_PLAN.md) identifies a
deployed `noindex, nofollow` directive, missing sitemap, and duplicate hostname
variants in its October 17 audit. Verification gives us tools to diagnose and
monitor those issues. **Verification itself does not remove `noindex` or make
pages automatically eligible for indexing.** Those application/deployment fixes
are separate work under the plan.

## Recommended approach

Create a Google Search Console **Domain property** for `spokanetech.org` and
verify it with a DNS TXT record. A Domain property covers HTTP/HTTPS and subdomains,
including both `www.spokanetech.org` and `spokanetech.org`.

DNS verification fits this deployment because it requires no Django template
changes, uploaded verification files, Docker rebuilds, or server restarts. Leave
the verification record in DNS after setup so verification remains valid.

After Google verification succeeds, import the verified site into Bing Webmaster
Tools. Bing also supports independent verification if import is unsuitable.

## Before starting

Have access to:

- A Google account controlled by a long-term project maintainer.
- The Namecheap account that can edit DNS records for `spokanetech.org`.
- An account accepted by Bing Webmaster Tools for its sign-in process.

Check whether a Search Console property already exists in the intended Google
account before creating another one. If another maintainer owns an existing
property, ask that owner to grant access or complete your own verification.

In Namecheap, confirm that the domain's nameservers use its BasicDNS, PremiumDNS,
or FreeDNS service. If **Advanced DNS → Host Records** is unavailable, DNS may
actually be hosted elsewhere or managed through a hosting control panel. Use that
authoritative DNS service instead. Do not change nameservers just to complete
verification.

## Step 1: Add the Google Search Console property

1. Open [Google Search Console](https://search.google.com/search-console/) and
   sign in with the intended project-maintainer Google account.
2. Use the property selector to choose **Add property**.
3. Choose **Domain**, rather than URL prefix.
4. Enter exactly:

   ```text
   spokanetech.org
   ```

   Do not include `https://`, `www`, a path, or a trailing slash.
5. Continue to the ownership verification instructions and select the TXT record
   option if prompted.
6. Copy the complete value supplied by Google. It will resemble:

   ```text
   google-site-verification=YOUR_UNIQUE_VERIFICATION_VALUE
   ```

   The example is a placeholder; use the actual value from your verification
   screen. Keep that screen available while editing DNS.

See [Google's ownership verification instructions](https://support.google.com/webmasters/answer/9008080).

## Step 2: Add the TXT record in Namecheap

1. Sign into Namecheap.
2. Open **Domain List**.
3. Find `spokanetech.org` and click **Manage**.
4. Open **Advanced DNS**.
5. In **Host Records**, click **Add New Record**.
6. Configure the record:

   | Field | Value |
   | --- | --- |
   | Type | `TXT Record` |
   | Host | `@` |
   | Value | The complete `google-site-verification=...` value copied from Google |
   | TTL | `Automatic` |

7. Save the record using the checkmark or save control shown by Namecheap.

`@` represents the root domain, `spokanetech.org`. Add a separate TXT record;
retain existing website, mail, SPF, DKIM, DMARC, and other verification records.
The new record is for Google's verification, not a replacement for those records.

See [Namecheap's host-record instructions](https://www.namecheap.com/support/knowledgebase/article.aspx/434/2237/how-do-i-set-up-host-records-for-a-domain/).

## Step 3: Verify with Google

1. Return to the Search Console verification screen.
2. Click **Verify**.
3. If verification succeeds, open the property and confirm that it is the Domain
   property for `spokanetech.org`.
4. If Google cannot yet find the record, allow time for DNS propagation and retry.
   Propagation can take minutes or longer; Google's instructions allow for delays
   of a few days. An initial failure does not necessarily mean the record is wrong.
5. Leave the TXT record in Namecheap after verification. Google periodically
   checks that the verification method remains valid.

If verification continues to fail, check:

- The record was saved at the authoritative DNS provider.
- Type is TXT and Host is `@`, rather than `www`.
- The complete value matches Google's current verification screen exactly.
- There are no accidental leading/trailing spaces or added characters.
- You are verifying the property in the Google account that supplied the value.

Optionally, inspect public DNS from a machine with `dig` installed:

```shell
dig TXT spokanetech.org +short
```

Look for the matching `google-site-verification=...` entry. This checks record
visibility from that resolver; it does not itself complete Google's verification.

## Step 4: Add the site to Bing Webmaster Tools

1. Open [Bing Webmaster Tools](https://www.bing.com/webmasters/) and sign in.
2. Choose the option to import sites from **Google Search Console**.
3. Sign into the Google account that has access to the verified property.
4. Review the permissions Bing requests, then authorize the connection if you
   agree to them.
5. Select the SpokaneTech property when offered and complete the import.
6. Confirm that Bing lists the correct site and reports successful verification.
   Follow the wizard's instructions if it asks for a public site URL. Use the
   preferred HTTPS hostname agreed in the SEO plan; the current recommendation
   is `https://www.spokanetech.org/`.

If import is unavailable or unsuitable, choose **Add a site** and follow Bing's
independent verification instructions. It supports DNS and website-based methods.
For a DNS method, add the exact record Bing supplies as an additional record;
Google's verification value is not a substitute for Bing's token.

See [Microsoft's Bing setup guide](https://blogs.bing.com/webmaster/2025/6/Start-Using-Bing-Webmaster-Tools-to-Improve-Your-Site-Visibility/).

## Step 5: Maintain access and record the result

Keep verified ownership with a long-term project maintainer. Grant contributors
individual access appropriate to their work instead of sharing the owner's
password. Search Console supports owner, full-user, and restricted-user roles.
Review access when responsibilities change, and retain required verification
records during future DNS migrations.

Record the following in the project's private operational notes:

- The responsible maintainer and recovery/contact arrangements.
- The Search Console property and Bing site URL.
- Verification method, date completed, and where the DNS record is managed.
- Which maintainers have access and when access was last reviewed.

Do not put passwords, recovery codes, or access tokens in the repository.
See [Google's permission guidance](https://support.google.com/webmasters/answer/7687615).

## After verification

1. Review Search Console's indexing and performance reports and Bing's equivalent
   reports. New properties may need time to accumulate data.
2. Inspect the homepage and representative event/group URLs to establish a
   baseline. Record indexing exclusions and any canonical or crawl problems.
3. Deploy the implemented indexability, metadata, and canonical URL changes using
   the rollout guide, with production indexing explicitly enabled.
4. Once `/sitemap.xml` actually exists and serves a valid sitemap, submit its
   preferred-host URL in both tools. The October 17 pre-implementation audit found
   a 404 there; the new route becomes available after deployment, and includes
   public URLs only when production indexing is enabled.
5. After deployment, inspect representative pages again, request indexing for
   appropriate important URLs, and monitor subsequent reports. Submission and
   verification do not guarantee indexing or a particular ranking.

## Completion checklist

- [ ] Google Domain property for `spokanetech.org` is verified.
- [ ] The required DNS TXT record remains in place at Namecheap.
- [ ] Bing lists the intended site and confirms verification.
- [ ] Responsible maintainers and account access are recorded privately.
- [ ] Initial search/indexing reports have been reviewed, or their pending status recorded.
- [ ] Indexability and sitemap implementation remain tracked separately in the SEO plan.
