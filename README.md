# taxmap resources

A community-maintained catalog of reusable official jurisdiction resources for
[taxmap](https://github.com/Cocoa-County/tax-map).

Store **where to start**, not the documents collected for a particular project:

| Include | Keep in an individual taxmap project instead |
|---|---|
| County tax-bill URL templates and lookup portals | Individual parcel bill URLs, bills, payments or owner information |
| Parcel, assessment and boundary GIS services | Downloaded GIS datasets and project-specific parcel selections |
| City/county websites and open-data portals | Specific reports, resolutions and rate schedules |
| Agenda/minute calendars and archives | Individual meetings, attachments, minutes and recordings |

## Use the catalog

Start with [catalog.json](catalog.json), then read the relevant files under
[jurisdictions/](jurisdictions/). Match country, region, county and city;
city projects can use their parent county's resources, not an unrelated city's
resources. Each entry records its official authority, verification method/date,
limitations and, where applicable, APN format and tax-year behavior.

The taxmap plugin's `find-jurisdiction-resources` skill checks this catalog before
starting discovery. It records the catalog revision and rechecks candidate
endpoints for the project. Direct browsing does not require GitHub authentication.
If the catalog is unavailable or has no match, continue official-source research
and report that limitation. This catalog is not a prerequisite for a useful app.

**Catalog verification is not tax authority or project evidence.** `verified`
means the recorded endpoint check succeeded, only to the extent described.
An HTTP response does not prove that a bill belongs to a parcel, that its fiscal
year matches a project, or that a document was adopted. `access_limited` preserves
an explicit access failure without claiming the site is unavailable to everyone.
`unverified` entries are leads. No entry authorizes publication or execution.

For a tax-bill template, verify the APN formatting and check the returned parcel
and year before using it in `site.parcel_links`. Current-year endpoints may change
years independently of the map. Never initiate payments or store a concrete bill
URL in this catalog.

## Contribute

Anyone with a GitHub account can propose an addition or correction through a
fork and pull request. With taxmap installed, ask:

> Propose a taxmap resource catalog update for this official county GIS service.

The `contribute-jurisdiction-resources` skill prepares a minimal change, validates
it and, after approval to publish, opens a pull request using your authorized
GitHub tools. It never approves or merges its own contribution. Reading the
catalog does not grant permission to submit information.

Maintainers review and merge contributions. See [CONTRIBUTING.md](CONTRIBUTING.md).
The repository has no automatic merge or deployment of submitted resources.

## Validate locally

Requires Python 3.10+:

```text
python -m pip install -r requirements.txt
python scripts/validate_catalog.py
python -m unittest discover -s tests -v
```

After adding/removing a jurisdiction or changing resource kinds, regenerate the
small discovery index with `python scripts/validate_catalog.py --write-index`.
Commit the index with the YAML changes. CI validates the schema, catalog scope,
unique identities and index consistency. It does not contact external sites;
contributors and maintainers must inspect authority and verification claims.

This repository's code and original metadata use the [MIT license](LICENSE).
Underlying websites, data and documents retain their own terms and rights.
