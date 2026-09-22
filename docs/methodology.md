# Methodology

This document explains what every column means, how each fact was established, and how the list stays
honest as it grows. It is the contract between the dataset and the people who rely on it.

## What this list is

A directory of companies that sell cybersecurity and information security work **to customers in
Norway**: penetration testing, red teaming and security assessment, 24/7 SOC and incident response,
cloud and OT security, identity and access management, forensics, governance and compliance, privacy
and security training.

It began as a blog list written by [Ahmad Abdur Rehman](https://ahmad.science/) in 2023 covering
penetration testing companies
([39 companies](https://ahmad.science/2023/02/24/33-pentest-firma-i-norge-sikkerhetstesting-inntrengingstesting/)),
was updated in
[2025](https://ahmad.science/2025/05/06/50-selskaper-som-tilbyr-sikkerhetstesting-pentest-i-norge-2025-utgaven/),
and is maintained here as an open dataset where every claim has a source. The 2026 edition widened the
scope from penetration testing to cybersecurity and information security, because three years of
maintaining the narrower list showed how much of the market it left out.

## What this list is not

- **Not a quality ranking.** Rows are ordered by *known numbers and how well they are established*,
  never by merit. There is no scoring and no "best". A company sorts higher because its in-house staff
  figure is confirmed or larger, not because it is better, and a missing number is never read as a
  weakness (see "How the list is ordered" below).
- **Not an endorsement.** Being listed says nothing about quality, and nothing here has been
  validated by testing the vendors' work.
- **Not paid placement.** No company can pay to be added, moved or removed. Being listed is not an
  accusation, and asking to be removed is not an admission of anything.
- **Not a security guarantee.** Inclusion is not evidence that a provider is competent, certified or
  insured.
- **Not a primary source.** Every figure here is an aggregation of published claims, registry filings,
  named attestations and labelled estimates. It is a starting point for your own diligence, not a
  substitute for it.
- **Not a product catalogue.** Companies whose Norwegian business is mainly selling licences and
  hardware are out of scope, as are public authorities and sector CERTs. This list is about who does
  the work.

### Aggregated data, and AI-assisted tooling

This has to be said plainly, because a clean table invites more trust than the data earns:

- **Some of these numbers are wrong.** They are aggregated from company pages, from the Norwegian
  register of legal entities and from people who know the market. Figures age, companies reorganise,
  and headcounts shrink as well as grow. Treat every number as a claim with a source, not as fact.
- **AI-assisted tooling was used for the data passes.** Scripts fetch pages, cross-check registry
  records, surface candidate sentences and draft entries for review. A human reviews the result before
  it lands in the dataset, and the validator refuses any figure with no source behind it. But
  extraction and drafting were machine-assisted, and errors can survive review.
- **The original 2023 list was plain manual research.** The author built the 2023 edition by hand, and
  the 2025 edition extended it the same way. The AI-assisted pass is a property of the later dataset
  editions, not of the list's origins.
- **Most staff counts are guarded estimates, and they say so.** They are labelled `estimated`
  wherever they appear and documented under "Guarded estimates" below.
- **Corrections are welcome and expected.** If a figure is wrong, an issue with a source fixes it;
  that is why corrections are tracked in [`CHANGELOG.md`](../CHANGELOG.md).

## Column definitions

### Company

The name readers know, kept as close as possible to the name used in the original pentest list so the
lineage stays traceable. Where a company has been renamed or acquired, the original name stays in the
`name` field when it is still the name buyers use, and the change is recorded in `legal_name`,
`former_names` and `notes`. A reader who has an old name in their procurement notes can therefore
still find today's provider.

### Office in Norway

`Yes` requires one of:

1. an entity registered in Enhetsregisteret with a Norwegian business address, or
2. a Norwegian address published by the company itself.

A registered Norwegian branch of a foreign group (a NUF) and a Norwegian subsidiary of a foreign
parent both qualify, with the ownership recorded in `notes`. `No` means **no Norwegian entity was
found**. It does not mean the company has no Norwegian staff, no Norwegian customers or no Norwegian
partners: plenty of foreign vendors serve Norway perfectly well remotely. The wording is deliberately
narrow so the column cannot be read as a stronger claim than the evidence supports.

### Employees (total)

The **whole company**, not the security staff. Two figures can appear:

| Marker | Meaning |
|---|---|
| `site` | The company states the figure itself. The `employees_source` URL and `employees_as_of` date are recorded. |
| `registry` | The headcount filed with Enhetsregisteret for that legal entity, with the registry's own registration date. |

Both can be shown, and they often differ: a group can have 170+ employees while the specific legal
entity reports 172, and a parent entity's registry count can include staff who have nothing to do with
security work. Showing both, with provenance, is more honest than picking one and hiding the other.

`employees_note` records qualifiers such as "stated as 250 specialists" or "group-wide across the
Nordics", so a soft figure is never presented as a precise one.

**A registry headcount is never used as a security staff count.** It covers the whole entity, including
people who never touch security work, so the two numbers are kept in separate fields and the validator
refuses to let one stand in for the other.

### In-house security staff

The number of cybersecurity staff on the company's own payroll: consultants, testers, analysts and
engineers whose job is security. This is the **primary signal** in the list: it is the number that
answers "can they do this work themselves", and it is the number most likely to be missing, because
almost nobody publishes it.

The column is populated from four bases, recorded in `security_staff_basis`, in descending order of
strength:

| Basis | Meaning | Confirmed? |
|---|---|---|
| `company-site` | The company states a count itself. Carries a `security_staff_source`. | Yes |
| `attestation` | A count vouched for first-hand by a named person who knows the company, typically someone who works there, rather than published by the company. The attester is named in the row. | Yes, but it is one person's word |
| `estimate` | A **guarded estimate** by the list maintainer, from market knowledge and the registry record, with no company statement and no first-hand count behind it. Labelled `estimated` everywhere it appears. | No |
| `crowd` | A crowdsourced platform's number of contracted researchers. A real published figure, but a crowd is not a payroll, so it does not count as in-house staff and does not lift a row in the order. | Not staff |

"Confirmed" therefore means exactly one of two things: the company said it, or a named person vouched
for it. Everything else is an estimate and is labelled as one.

Rules that hold for every value:

- a `+` (as in `391+`) means the count is a stated **minimum**, and `security_staff_is_minimum` is set;
- `security_staff_scope` records what the number actually counts when it is not a clean security-only
  figure: `security-only`, `security-and-it` (the team also does general IT), or `whole-company` (a
  company-wide figure that includes security staff);
- when a company publishes something adjacent but different, `security_staff_note` records what it
  actually says (for example: *"publishes 170+ employees and a Red Team service, but no staff count"*);
- a claim never masquerades as a stronger claim: the table says where the number came from, and any
  figure can be disputed like any other.

**`??` is not zero.** Where no count could be established, the site shows `??` with an *add it* button
that opens the update-company issue form. A blank would be read as "none"; `??` says "we did not find
this out", which is the truth. On the site, `??` sorts below every known number purely because nothing
was found, a fact about publishing rather than about skill.

### Guarded estimates

A lot of security work in Norway is sold by companies that do not deliver it themselves, and the
companies that do deliver it mostly do not publish how many people they employ to do it. Leaving every
one of those rows as `??` would make the primary column useless exactly where a buyer most needs it,
so a **guarded estimate** is used, under strict conditions:

- **It is only used for security-only businesses**, where the company's registered headcount is a
  close proxy for its security staff because everyone on the payroll works on security. Nothing is
  inferred for companies that also do general IT, consulting or managed services: those rows stay `??`.
- **The estimate is the registry headcount, set as a floor**, with `security_staff_is_minimum` and
  `security_staff_scope: whole-company` so nobody can read it as a measured split between security and
  non-security staff.
- **It says where it came from.** The row carries a source of type `estimate` whose note names the
  maintainer, says the figure is not published by the company, and explains the derivation.
- **It is the weakest basis above unknown**, and it is replaced the moment anything better arrives: a
  published figure, a named attestation, or a correction with a source.

`security_staff_basis: estimate` is the label that makes this safe to publish. An estimate sorted and
labelled like a number is useful; an estimate dressed up as a published figure is not.

### Delivery

How the Norwegian work is actually done, because a provider and a reseller look identical on a services
page:

| Value | Meaning |
|---|---|
| `in-house` | The company's own employees deliver the work. |
| `mixed` | Mostly own staff, with subcontractors for peaks or specialisms. |
| `partner-network` | There is no real delivery team in Norway: the work is resold or subcontracted to another provider. |
| `unknown` | Not established. Shown as `?`. |

**A delivery model cannot be asserted without a source** (`delivery_source`), and the weaker claims
(`mixed`, `partner-network`) must carry a `delivery_note` explaining how that was established. A
partner network is a legitimate way to buy; it is simply a different thing to buy, and it should not be
a surprise after the contract is signed.

### Speciality and capabilities

- **`specialty`** is one factual line, in plain language, on what the company is actually known for.
  No marketing: the validator warns on words like "leading" or "best-in-class".
- **`capabilities`** are the tags the company itself publishes: penetration testing, red teaming,
  purple teaming, social engineering, vulnerability assessment and management, automated pentesting,
  attack surface management, bug bounty and crowdsourced testing, physical security, crypto audits,
  application, API, mobile and cloud security, secure development and DevSecOps, code review, security
  architecture, SOC/MDR, incident response, threat intelligence and hunting, forensics, malware
  analysis, endpoint, network and email security, identity and access management, PKI, data protection,
  backup and recovery, OT/ICS, IoT and container security, security audit, compliance, risk management,
  privacy/GDPR, NIS2/DORA readiness, virtual CISO, security and awareness training, and tabletop
  exercises.

Only tags the company publishes are attached. A row with no established capability list keeps its
speciality and an empty tag list rather than a plausible-looking guess.

### Org. no.

The nine-digit Norwegian organisasjonsnummer for the entity that delivers the Norwegian work, the
reliable way to tell providers apart after renames and acquisitions. Where a group sells through several
entities, the one pinned is the one whose people do the work, and `notes` says so when it is ambiguous.
Where no Norwegian entity exists, the field is `null` rather than borrowed from a parent company abroad.

### Verification and last updated

| Value | Meaning |
|---|---|
| `verified` | The stated facts were checked against a primary source: the registry, the company's own page, or a named attestation. |
| `partial` | Something in the row is still open, and `notes` says what. |
| `unverified` | No verifiable presence was found. The row is kept and labelled rather than quietly deleted. |

`last_verified` is the date a human last checked the row. The site shows green within 6 months, amber to
12 months and red beyond, and CI warns past 12 months and fails past 24.

## How the list is ordered

1. **Tier first.** Companies with a physical office in Norway are listed first, because that is what most
   Norwegian buyers need. Companies without one are in a separate, lower-priority section.
2. **How well the staff figure is established**: confirmed counts (published or attested) first, then
   labelled estimates, then rows where no count could be established.
3. **How many staff**, most first, within those groups.
4. **Employees, the secondary signal**, where staff counts tie or are equal.
5. **Name**, alphabetically, as the last resort.

A crowdsourced researcher pool is not a payroll, so those rows sort below every company with staff
testers while keeping their `crowd` label. Fifteen security staff at a specialist boutique and fifteen
inside a 4,000-person consultancy are very different propositions, and the ordering is not a ranking:
use the columns, not the position.

## Maintenance, corrections and removal

### Adding and correcting

- **Adding a company:** open an issue with the add-company form, or add one JSON file by hand. See
  [`CONTRIBUTING.md`](../CONTRIBUTING.md).
- **Correcting a row:** an issue or pull request with a URL. Corrections with sources are merged
  quickly; corrections without one are still read, and the row is marked as disputed instead of changed
  silently.
- **Correcting your own company:** you may correct facts about your own company, and you do not need to
  justify yourself. You may not correct or remove a competitor's row.
- **Disputing a figure:** the dispute form takes precedence over the general update form. If a public
  source and the company disagree and neither side is clearly wrong, both versions are recorded in the
  notes rather than one being deleted.

### Removing a company

Any company can ask to be removed from the list, for any reason or none:

1. Open an issue with the [removal form](../.github/ISSUE_TEMPLATE/remove-company.yml), or write to the
   maintainer if you would rather not post publicly.
2. The row is deleted from the dataset and from every generated file on merge, and
   [`CHANGELOG.md`](../CHANGELOG.md) records that a removal request was honoured, without dwelling on
   who asked or why.
3. It stays public in the git history, because that is how the repository works and pretending
   otherwise would be dishonest. Nothing stops a future contributor from re-adding a company by hand,
   but a maintainer who sees a removal note will not.
4. A company can also ask for **one figure to be dropped** while staying listed, for example if it does
   not want its staff count published. Say which figure, and it goes.

This is a listing of companies that sell security work, not an investigation of them. Removal requests
are honoured because the list has no right to anyone's participation.

## Neutrality and money

- No company pays to be listed, moved, ranked or removed.
- No advertising, sponsorship or affiliate links anywhere in the dataset, the README, the site or the
  exports.
- Anyone with a commercial interest in a row must disclose it when contributing, and the disclosure
  stays in the pull request, which is public.
- Maintainers do not accept an estimate as a payment in kind: if someone asks for a favourable figure,
  the answer is the same as for everyone else, namely a source or an estimate labelled as one.

## How the tooling enforces this

- `scripts/validate.py` is the authoritative check, and it is what CI runs. It refuses a number with no
  source, a `security_staff` figure with no basis, an estimate with no named estimator, an attestation
  with no named attester, a delivery model with no source, a `mixed` or `partner-network` claim with no
  explanation, an unknown capability tag, a duplicate org.nr, and a row whose `last_verified` is in the
  future or more than two years old.
- `scripts/build.py` generates the README, the site and the CSV/JSON/YAML exports from the same files,
  so they cannot disagree, and `--check` fails when a contributor edits data without regenerating.
- `scripts/enrich_brreg.py` refreshes registry facts for rows whose org.nr a human has confirmed. It
  never invents a link between a name and a number: the registry's name search is fuzzy, so a person
  confirms each match once.
- `scripts/fetch_signals.py` fetches company pages and surfaces candidate sentences for a human to
  judge. It deliberately writes nothing into the dataset.
- `scripts/linkcheck.py` verifies every source URL and fails on a dead link.
