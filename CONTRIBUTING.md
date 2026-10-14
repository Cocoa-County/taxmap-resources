# Contributing

Use a fork, a focused branch and a pull request targeting
`Cocoa-County/taxmap-resources:main`. Do not push a contribution directly to
upstream main, enable auto-merge, approve your own PR, or merge it. Maintainers
decide whether to accept it. Contributions are public.

1. Read README.md, AGENTS.md, schema/resource.schema.json and a nearby
   jurisdiction file. Reuse an existing jurisdiction/resource identity when
   correcting it. Include only official reusable entry points.
2. Verify official ownership, resource scope and endpoint behavior. Respect
   access restrictions and rate limits. Record what was actually checked and
   the date; never turn an HTTP 403 into a successful verification.
3. Edit or add a YAML file below jurisdictions/. Use canonical country/region
   codes, the actual county/city names and a stable lowercase ID. Do not put
   city-only services in a county entry or duplicate county templates in cities.
4. Record bill APN formatting and year behavior. A placeholder template is
   allowed; concrete parcel bill URLs, sample APNs, addresses, owner/payment
   details and downloaded bills are not. Explain the test method without
   publishing the sample parcel or its financial information.
5. Keep specific reports, resolutions, meetings and attachments in project
   evidence, never in URLs, verification references, notes or the PR body.
   Use the parent official calendar, archive, service or agency website.
6. Run the validator, regenerate catalog.json if needed, and run the tests as
   documented in README.md. Review the full diff for private information.
7. Explain the jurisdiction, reusable purpose, official ownership evidence,
   verification date/method, APN/year caveats and validation results in the PR.
   Ownership references must themselves be reusable official entry points.

Use `verified`, `access_limited` or `unverified` honestly. Checks describe an
endpoint, not adoption of its documents or applicability to every parcel.
CI's URL filters catch common mistakes but cannot prove official ownership or
detect every document URL or personal detail; human review remains required.

GitHub credentials belong to the contributor's host tools. Never add tokens,
cookies, browser profiles, machine paths or authentication helpers here. If
authentication or fork/PR creation is unavailable, provide the proposed patch
and manual GitHub instructions instead of claiming a PR was submitted.
