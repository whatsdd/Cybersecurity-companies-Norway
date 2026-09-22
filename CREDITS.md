# Credits

## Author and originator

**Ahmad Abdur Rehman** ([ahmad.science](https://ahmad.science/), [LinkedIn](https://www.linkedin.com/in/ahmadscience/))

The list was started in 2023 and maintained by the author through three editions:

| Edition | Date | Scope |
|---|---|---|
| [39 pentest firms in Norway](https://ahmad.science/2023/02/24/33-pentest-firma-i-norge-sikkerhetstesting-inntrengingstesting/) | February 2023 | The original list, 39 companies, with a short description of each. |
| [50+ security testing companies in Norway](https://ahmad.science/2025/05/06/50-selskaper-som-tilbyr-sikkerhetstesting-pentest-i-norge-2025-utgaven/) | May 2025 | Expanded past 50 companies, split into Norwegian and international providers. |
| [Pentest-companies-Norway](https://github.com/whatsdd/Pentest-companies-Norway) | 2026 | The 2025 list turned into an open, verifiable dataset with a source behind every claim. |
| This repository | 2026 | The dataset widened from penetration testing to cybersecurity and information security, with capability tags, delivery models and confirmed in-house staff counts. |

The importance of that lineage is simple: the hard part was knowing which companies to look at.
Verifying them is comparatively mechanical, and that is what this repository adds.

### What the maintainer vouches for

Two kinds of claim in this dataset come from a person rather than from a company page, and they are
kept apart on purpose:

- **Attestations.** A figure vouched for **first-hand** by somebody who works at the company or has run
  the work themselves. Rows like this carry `security_staff_basis: attestation`, name the person in the
  row, and point at this file or a public statement. Exactly one such figure is in the current data:
  the four security staff at Experis, attested by the author, who works there.
- **Guarded estimates.** Figures the maintainer **estimated from market knowledge and the registry
  record**, with no company statement and no first-hand count behind them. Rows like this carry
  `security_staff_basis: estimate`, show an `estimated` label everywhere the number appears, and are
  documented in [`docs/methodology.md`](docs/methodology.md#guarded-estimates). They are only used where
  the registered entity is a security-only business, so the registry headcount is a usable floor.

Estimates are the weakest basis in the dataset. Any company statement, named attestation or correction
with a source replaces one, and an issue is enough to overturn it.

If you reuse this dataset, the licence requires that you credit the author and link back here:

> Started in 2023 by Ahmad Abdur Rehman (https://ahmad.science/) as a list of penetration testing
> companies in Norway, widened in 2026 to cybersecurity and information security companies.
> Source: https://github.com/whatsdd/Cybersecurity-companies-Norway

## Hiring or connecting

The author is on [LinkedIn](https://www.linkedin.com/in/ahmadscience/) and writes at
[ahmad.science](https://ahmad.science/). Hiring security people, or scoping security work of your own,
is the usual reason people get in touch.

## Contributors

Thank you to everyone who adds a company, corrects a figure or reports a dead link. Corrections with
sources are the most valuable contribution there is.

<!-- New contributors are added here as their pull requests are merged. -->

- Ahmad Abdur Rehman ([@whatsdd](https://github.com/whatsdd)): dataset, verification, tooling

## Data sources

This project stands on open data and on companies publishing facts about themselves:

- **[Enhetsregisteret](https://data.brreg.no/enhetsregisteret/api/docs/index.html)**: the Norwegian
  Central Coordinating Register for Legal Entities, operated by the Brønnøysund Register Centre.
  Company registrations, headcounts, addresses and rename histories come from here. Open, free, no
  API key. It never tells us what anyone does, so it is never used as a security staff count.
- **Company websites**: headcounts, services, capability claims and certifications that companies
  publish themselves.
- **News coverage**: used to date acquisitions and name changes, and cited per row.
- **People who know the market**: attestations, named per row, and always weaker on paper than a
  published figure.

## Licensing

- Dataset: [CC BY 4.0](LICENSE), reuse freely, including commercially, with attribution.
- Code: [MIT](LICENSE-CODE).
