# Changelog

Editions follow the blog-list lineage: the 2023 pentest list, the 2025 update, the 2026 dataset, and
now the wider cybersecurity directory. Corrections are listed because a directory's corrections are
its most useful output.

## 2026.1: the cybersecurity edition

The scope widens from penetration testing to cybersecurity and information security, and the headline
column changes from "how many pentesters" to "how many security staff, and has anyone actually
confirmed it".

**75 companies**, 69 with a Norwegian office, 67 with a confirmed Norwegian registration. The pentest
edition had 54.

### Added

- **In-house security staff as the headline column**, replacing in-house pentesters. It counts the
  consultants, testers, analysts and engineers on the company's own payroll whose job is security, and
  it is the number that answers whether a company can do the work itself.
- **A confirmed / estimated distinction made explicit.** "Confirmed" now means exactly two things: the
  company published the figure, or a named person vouched for it first-hand. Of the 24 rows with a
  figure, **1 is confirmed** (the Experis attestation from the pentest edition), **22 are guarded
  estimates**, and **1 is a crowdsourced researcher pool**. The remaining **51 rows show `??`**.
- **Guarded estimates, and the rule that keeps them honest.** Where a company is a security-only
  business, the headcount its legal entity filed with Enhetsregisteret is recorded as an *estimate* and
  a *floor*, labelled `estimated` everywhere, with a source whose note names the maintainer and says
  the company does not publish the figure. Nothing is inferred for companies that also do general IT,
  consulting or managed services: those rows stay `??`. `security_staff_scope: whole-company` makes it
  impossible to read the figure as a measured split between security and non-security staff.
- **A delivery column.** `in-house`, `mixed` (own staff plus subcontractors), `partner-sourced` (no
  real delivery team here, the work is resold) or unknown. Current data: **68 in-house, 1 mixed, 4
  partner-sourced, 2 not established.** The column exists because a provider and a reseller look
  identical on a services page, and one of them cannot answer the phone at 03:00. A delivery claim
  needs its own source, and the weaker claims need a note explaining how they were established.
- **Capability tags and a speciality line.** Every row now carries the tags the company itself
  publishes, from a vocabulary of 45 capabilities spanning offensive work, defensive operations, cloud
  and industrial security, and governance. **40 tags are in use** across the list. The speciality line
  is one factual sentence, and the validator warns on marketing language.
- **A removal policy.** Any company can ask to be removed, no reason required, through a
  [removal form](.github/ISSUE_TEMPLATE/remove-company.yml). The row is deleted from the dataset and
  from every generated file, and the changelog records that a removal request was honoured without
  saying who asked. A company can also ask for a single figure to be dropped while staying listed.
  Being listed is not an accusation and leaving is not an admission of anything.
- **32 new companies**, including Ikomm, Move, Conscia Norge, nLogic, Sicra, Cyberon Security, Shift
  Security, Xlent Cyber Security, FM Cyber Security, Ivolv, Sun Security, Triple-S, NorthGRC,
  Proactima, Intility, Deloitte, Bouvet, Computas, Advania, Kyndryl, DXC, Devoteam, GlobalConnect,
  Miles, Forvis Mazars, Easywave, iTeam Braathe, Racom, SPADE Consulting, Norconsult Digital, Arctic
  Wolf and NCC Group.

### Changed

- **NorSIS is no longer listed.** It became part of the Norwegian National Security Authority in 2024,
  and authorities and sector CERTs are out of scope for a directory of companies selling work.
- **Product vendors are out of scope.** Companies whose Norwegian business is mainly selling licences
  and hardware, and their distributors, are not listed. This list is about who does the work.
- **Nine pentest-edition rows were not carried over**: NorSIS (above), plus DataGardens, Motit,
  ShieldTech and NextLink Labs (no locatable business, no Norwegian entity, or an unrelated US company
  behind the name), Greenberg Traurig (US law firm), Horangi (Bitdefender-owned, no Norwegian entity),
  and Intruder, Pentera and DeepStrike (products rather than service providers). The rest of the
  pentest list is here.
- **Eleven companies whose security practice could not be confirmed were researched and left out**,
  rather than listed on a guess: candidate IT houses were fetched and read, and where their own pages
  showed general IT or product work and no security service, they were dropped.
- **`services` became `capabilities`, and `security_testers` became `security_staff`**, with the
  existing four bases kept and given clearer meanings.
- **The ordering now sorts on how well a figure is established**: confirmed counts first, then labelled
  estimates, then rows where nothing was found, and by size within each group.
- **Company identities were cleared against the registry**, which fixed several rows: Knowit's security
  business is Knowit Cybersecurity & Law AS (the pentest edition could not find an entity at all),
  Nixu's Norwegian work now sits in DNV AS, Teknograd is recorded as Upheads, EVRY as Tietoevry, and
  Banshie as Truesec.

### Findings worth recording

- **Still nobody publishes a count of their security staff.** Thirteen of 75 publish a whole-company
  headcount, and exactly one row in the dataset has a confirmed security staff figure, which is an
  attestation rather than a publication. The column that motivated the dataset is still the emptiest
  one, and the list says so instead of guessing.
- **Resale is visible once you look for it.** Four rows are partner-sourced and one is mixed, and those
  are the ones where the delivery model was stated or self-evident. The number is a floor rather than a
  measurement: most companies simply do not say who does the work.
- **The registry headcount is a good floor for a pure-play security company and useless for anyone
  else.** That is what made the guarded estimate rule possible, and it is why the rule stops at
  security-only businesses.

### Notes

- Each row's estimates are documented in `docs/methodology.md` and can be replaced by a published
  figure, a named attestation or a correction with a source. An issue is enough to overturn one.
