# Contributing

Thank you for helping keep this list accurate. Corrections with a source are the most valuable
contribution there is, more valuable than additions.

- **Adding a company:** [open an issue](../../issues/new/choose) or add one JSON file by hand.
- **Fixing a fact:** same thing, and say what was wrong.
- **Adding a capability tag or a speciality line:** welcome, as long as it is what the company itself
  publishes.
- **Correcting your own company's row:** open an issue. You may correct your own facts; you may not
  delete or disparage a competitor.
- **Asking to be removed:** open an issue with the [removal form](../../issues/new?template=remove-company.yml).
  No reason is required and the removal is honoured.
- **Reporting a dead company or a rename:** open an issue with the new name and, if you have one, the
  link to the announcement.

## The rules

These are enforced by CI, not by politeness:

1. **Every company needs at least one source.** A row with no evidence will not be merged.
2. **Every number needs its own source.** A headcount with no URL behind it fails the build. This is
   the rule that keeps the dataset trustworthy.
3. **A registry headcount is never a security staff count.** `brreg_employees` covers the whole legal
   entity, including people who never touch security work. Putting it into `security_staff` fails the
   build.
4. **Every staff figure says what kind of claim it is.** `security_staff_basis` is one of
   `company-site` (the company publishes it), `attestation` (a named person vouches for it first-hand),
   `estimate` (a guarded estimate by the maintainer, documented in
   [docs/methodology.md](docs/methodology.md#guarded-estimates)) or `crowd-platform` (a researcher
   pool, not staff). Never convert a whole-company headcount into a security staff count.
5. **A delivery claim needs a source.** `delivery` may be `in-house`, `mixed`, `partner-network` or
   `unknown`; `mixed` and `partner-network` also need a note explaining how that was established. This
   is the column that separates a provider from a reseller, and guesses do not belong in it.
6. **Only tag capabilities the company publishes.** The tags are what buyers filter on, so a tag
   without a company page behind it is worse than no tag. If nothing is published, leave the list empty
   and say so in `notes`.
7. **`office_in_norway: false` means "no Norwegian entity was found"**, which is not the same as "no
   Norwegian staff". Use the registry to check, and put what you found in `notes`.
8. **No marketing language, no ranking, no "leading", no "best".** Describe services factually. The
   validator warns on marketing words in `specialty`.
9. **Declare your interest.** If you work for the company you are adding, say so in the pull request.
   That is fine: it just needs to be visible.
10. **Companies are listed, not endorsed.** Inclusion is not a recommendation, and CI does not check
    security claims. Any company can ask to be removed, and that is honoured without requiring a reason.
11. **Write plainly.** Factual English, no marketing, and plain punctuation: no em dashes, in the data,
    the docs or the issue templates. A colon, a comma or a full stop will almost always read better.
12. **CI checks links.** A source URL that 404s fails the build, so replace dead links rather than
    leaving them.

## Adding a company by hand

One file per company: `data/companies/<slug>.json`, where `<slug>` is a lowercase hyphenated id that
matches the `id` field (`river-security.json` → `"id": "river-security"`). Start from this template:

```json
{
  "id": "example-company",
  "name": "Example Company",
  "legal_name": "EXAMPLE COMPANY AS",
  "website": "https://example.no",
  "category": "norwegian",
  "org_nr": "999999999",
  "office_in_norway": true,
  "office_cities": ["Oslo"],
  "security_staff": null,
  "employees_total": null,
  "delivery": "in-house",
  "delivery_source": "https://example.no/om-oss",
  "specialty": "One factual line on what the company is known for, in plain language.",
  "capabilities": ["penetration-testing", "incident-response"],
  "verification": "partial",
  "last_verified": "2026-09-22",
  "verified_by": "@your-handle",
  "sources": [
    { "url": "https://example.no/om-oss", "type": "company-site", "checked": "2026-09-22" }
  ]
}
```

The full contract is in [`data/schema.json`](data/schema.json). The capability tags are listed in that
file and explained in [docs/methodology.md](docs/methodology.md#speciality-and-capabilities).

### Finding the Norwegian entity

Search the open Enhetsregisteret API for the organisasjonsnummer:

```
https://data.brreg.no/enhetsregisteret/api/enheter?navn=Example%20Company
```

Two warnings from experience:

- **The name search is fuzzy.** Searching for `NorSIS` returns a carpentry sole proprietorship in
  Sandefjord. Always confirm the match before pinning the number.
- **Check `historiskeNavn`.** It gives the real rename history, which is how this list can say
  "formerly Besec" as a verified fact instead of repeating a rumour.

Then let the tooling refresh the registry fields for you:

```bash
python3 scripts/enrich_brreg.py propose --id example-company   # ranked candidates, human decides
# put the confirmed number in the JSON as "org_nr"
python3 scripts/enrich_brreg.py refresh --all --write          # fill in registry-derived fields
```

### Counting in-house security staff

Almost nobody publishes this, and that is a finding, not a gap. Only set `security_staff` when the
company states a count of security staff or testers on its own page, or when a named person vouches for
a count first-hand. If the page publishes something adjacent, record it in `security_staff_note`
instead, for example:

```json
"security_staff_note": "Publishes 170+ employees and a Red Team service, but no staff count"
```

Watch for false friends: a "test specialist" in a consultancy usually means software QA, not security
testing, and a registry headcount says nothing about what anyone does. `scripts/fetch_signals.py` will
surface candidate sentences for you, but the judgement is yours:

```bash
python3 scripts/fetch_signals.py --id example-company
```

### Setting the delivery model

`delivery` answers a question the services list does not: who actually does the work.

- `in-house`: the company's own people deliver it. Point `delivery_source` at the page that shows the
  team, the service description or the careers page.
- `mixed`: mostly own staff with subcontractors for peaks or specialisms. Say how you know.
- `partner-network`: there is no real delivery team in Norway and the work goes to another provider.
  Say how you know; this is a strong claim and the note carries the weight.
- `unknown`, or omit the field: not established. That is a perfectly good answer.

## Before you open the pull request

```bash
python3 scripts/validate.py     # checks the dataset, must exit 0
python3 scripts/build.py        # regenerates README, site and exports
python3 scripts/linkcheck.py    # verifies every source URL
```

`scripts/build.py --check` fails if generated files are out of date, so run `build.py` and commit the
result. CI regenerates them on merge as a backstop, but keeping them in step keeps the diff honest.

## What reviewers will ask

- Where did this fact come from? (a URL, not a memory)
- Is this the right legal entity? (org.nr, or an explanation of why there is none)
- Is a rename or acquisition involved? (record it in `notes` and `former_names`)
- Does the delivery label match the evidence?
- Does `verification` match reality? `verified` means the stated facts were checked against a primary
  source, `partial` means something is still open, `unverified` means no verifiable presence was found.

## Adding a company you cannot verify

Add it anyway, with `"verification": "unverified"` and a note saying exactly what you could not find.
A clearly-labelled unknown is more useful than a confident guess, and it gives the next contributor
something concrete to chase. Rows in that state are visible in the site's "Unverified" filter.

## Removing a company

Any company can ask to be removed. Open an issue with the
[removal form](../../issues/new?template=remove-company.yml), or contact a maintainer privately if you
would rather not post in public. The row is deleted from the dataset and every generated file, and the
changelog records that a removal request was honoured without naming who asked. A company can also ask
for a single figure to be dropped while staying listed.

## Code of conduct

Be straightforward and be kind. Disagreements about facts are welcome; they are settled with sources.
See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
