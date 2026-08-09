# YNAB Bugcrowd programme brief - bounded operator extract

- Source: `https://bugcrowd.com/engagements/ynab`
- Capture mode: operator extract, paraphrased except for identifiers
- Retrieved: 2026-08-09T11:30:16Z
- Public page status: in progress, ongoing testing period
- Public page last updated: 2026-03-05T21:41:59Z

## Authority facts

- The rendered target tables contain three in-scope rows and five out-of-scope rows, saved separately in `ynab-target-groups.json`.
- The prose describes the staging web application/private API, staging public API, marketing site, two-factor-authentication issues, and YNAB-owned hosts as research areas.
- The prose also says testing is limited to targets listed in the in-scope section and treats unlisted properties and subdomains as out of scope.
- Production application environments, older desktop products, third-party support/learning sites, an internal development site, mobile applications, customer accounts, and real user data are excluded.
- The public API paragraph points researchers to the staging API but also mentions selecting the production API server. The target table lists only the staging API.

## Conduct and access facts

- Researchers must use accounts they control and must not access or alter real-user data.
- Denial of service, social engineering, phishing, physical attacks, and aggressive automated scanning are prohibited.
- Testing beyond explicitly authorized targets is prohibited.
- Test accounts use a Bugcrowd researcher alias; multiple controlled accounts may use plus-addressing.
- Public disclosure requires explicit permission through the programme's coordinated-disclosure process.

## Observed conflicts - no decision recorded

1. Broad YNAB-owned-host language conflicts with the later listed-target-only and unlisted-subdomain exclusion language.
2. The production API mention conflicts with the exclusion of production environments and the absence of that API from the in-scope target table.

These conflicts require human interpretation. This extract does not resolve them.
