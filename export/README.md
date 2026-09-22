# Exports

Generated from [`data/companies/`](../data/companies) by `scripts/build.py`. Do not edit by hand.

| File | Contents |
| --- | --- |
| `companies.csv` | One row per company, lists joined with `; `. |
| `companies.json` | Same records, plus metadata. |
| `companies.yaml` | Same as JSON, in YAML. |

**Attribution (required by the licence):** this dataset was started in 2023 by
[Ahmad Abdur Rehman](https://ahmad.science/) ([LinkedIn](https://www.linkedin.com/in/ahmadscience/))
as a list of penetration testing companies in Norway, and is published under [CC BY 4.0](../LICENSE).
If you reuse it, credit the author and link to <https://github.com/whatsdd/Cybersecurity-companies-Norway>.

Field notes: `security_staff` is `null` when no in-house count has been established, null means
"not stated" and never zero; whenever it is set, `security_staff_basis` says whether the figure is
`company-site` (published), `attestation` (vouched for first-hand), `estimate` (the maintainer's
guarded estimate) or `crowd-platform` (a researcher pool, not staff). Registry headcounts live in
`brreg_employees` and are never presented as security staff. `delivery` is `in-house`, `mixed`,
`partner-network` or `unknown`. `capabilities` are the company's own tags and `specialty` is a
plain-language summary. `office_in_norway` is `false` only when no Norwegian entity was found.

Dataset version: 2026-09-22.
