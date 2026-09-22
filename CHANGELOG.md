# Changelog

Editions follow the blog-list lineage: the 2023 pentest list, the 2025 update, the 2026 dataset, and
now the wider cybersecurity directory. Corrections are listed because a directory's corrections are
its most useful output.

## 2026.1: the cybersecurity edition

The scope widens from penetration testing to cybersecurity and information security, and the headline
column changes from "how many pentesters" to "how many security staff, and has anyone actually
confirmed it".

**87 companies**, 81 with a Norwegian office, 79 with a confirmed Norwegian registration. The pentest
edition had 54.

### Added

- **In-house security staff as the headline column**, replacing in-house pentesters. It counts the
  consultants, testers, analysts and engineers on the company's own payroll whose job is security, and
  it is the number that answers whether a company can do the work itself.
- **A confirmed / estimated distinction made explicit.** "Confirmed" now means exactly two things: the
  company published the figure, or a named person vouched for it first-hand. Of the 29 rows with a
  figure, **28 are guarded estimates** and **1 is a crowdsourced researcher pool**; no row currently
  carries a first-hand attestation, and the remaining **58 rows show `??`**.
- **Guarded estimates, and the rule that keeps them honest.** Where a company is a security-only
  business, the headcount its legal entity filed with Enhetsregisteret is recorded as an *estimate* and
  a *floor*, labelled `estimated` everywhere, with a source whose note names the maintainer and says
  the company does not publish the figure. Nothing is inferred for companies that also do general IT,
  consulting or managed services: those rows stay `??`. `security_staff_scope: whole-company` makes it
  impossible to read the figure as a measured split between security and non-security staff.
- **A delivery column.** `in-house`, `mixed` (own staff plus subcontractors), `partner-sourced` (no
  real delivery team here, the work is resold) or unknown. Current data: **80 in-house, 1 mixed, 4
  partner-sourced, 2 not established.** The column exists because a provider and a reseller look
  identical on a services page, and one of them cannot answer the phone at 03:00. A delivery claim
  needs its own source, and the weaker claims need a note explaining how they were established.
- **Capability tags and a speciality line.** Every row now carries the tags the company itself
  publishes, from a vocabulary of 47 capabilities spanning offensive work, defensive operations, cloud
  and industrial security, and governance. **43 tags are in use** across the list. The speciality line
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
- **Twelve rows arrived from readers after the first publication.** O3C, reported as a local company
  missing from the list; AFRY and Viljr, both reported from the Advansia lineage, where AFRY carries the
  Norwegian entity behind Advansia and Viljr is the advisory house four former Advansia leaders founded
  in September 2025, which by February 2026 had recruited around 50 people from their former employer;
  and then Gritera Security, eProvider, blinQ, Storm IT Sikkerhet, Devtec Norway, Junglemap, Bsure,
  IndyKite and SoftwareOne from a reader's list of 41 names. Nine of those twelve carry a guarded
  estimate; Gritera (31), Junglemap (9), Bsure (13) and IndyKite (9) qualify because the registered
  entity is a security-only business.

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
- **Two capability tags were added on demand**: `ai-security`, after O3C's published practice turned out
  to cover AI security with no tag to describe it, and `crisis-management`, because preparedness
  (`beredskap`) is a distinct service line in the Norwegian market and tagging it as incident response
  would have been wrong.
- **The ordering now sorts on how well a figure is established**: confirmed counts first, then labelled
  estimates, then rows where nothing was found, and by size within each group.
- **Company identities were cleared against the registry**, which fixed several rows: Knowit's security
  business is Knowit Cybersecurity & Law AS (the pentest edition could not find an entity at all),
  Nixu's Norwegian work now sits in DNV AS, Teknograd is recorded as Upheads, EVRY as Tietoevry, and
  Banshie as Truesec.

### Findings worth recording

- **Still nobody publishes a count of their security staff.** Thirteen of 87 publish a whole-company
  headcount, and not one publishes a security staff figure: every number in that column is either a
  guarded estimate or a crowdsourced researcher pool. The column that motivated the dataset is still
  the emptiest one, and the list says so instead of guessing.
- **Resale is visible once you look for it.** Four rows are partner-sourced and one is mixed, and those
  are the ones where the delivery model was stated or self-evident. The number is a floor rather than a
  measurement: most companies simply do not say who does the work.
- **The registry headcount is a good floor for a pure-play security company and useless for anyone
  else.** That is what made the guarded estimate rule possible, and it is why the rule stops at
  security-only businesses.

### Reader submissions checked and not listed

A reader sent 41 company names to check. Each was looked up in Enhetsregisteret and, where a site
exists, read for a published cybersecurity offering. Sixteen were already in the directory under their
current names or a predecessor's, and those rows were left alone rather than duplicated: Sicra, O3
Cyber, Knowit Cybersecurity & Law, Telenor Cyberdefence, DNV Cyber, Atea, Promon, Secure Practice,
Secure-NOK, NORMA Cyber, Konfitech, Easywave, Xlent Cyber Security, Shift Security, FM Cybersecurity.
The rest were checked and not listed, for one of these reasons:

- **The same company under another name.** Watchcom Security Group is the business Telenor Cyberdefence
  was built from, and BDO Cybersecurity has no entity at all: BDO AS is listed, and Defendable was spun
  out of that practice.
- **Not a company selling work.** HelseCERT is a sector CERT inside Norsk Helsenett, an authority
  function rather than a supplier.
- **In bankruptcy.** Rogue Cybersecurity (konkurs registered in 2026) and Hugin Cybersecurity (konkurs
  2026, listed in the register as a cyber security SaaS platform).
- **No locatable business.** ITR Cybersecurity has a registered purpose covering IT security but no site,
  no registered employees and 2025 revenue of one krone; the 2026 Avinta Cyber Security and Avinta
  entities in Bergen are investment companies and avinta.no does not resolve; Painkiller, bitYoga and
  Orizon produced no matching entity and no reachable service; and Nordic Cyber Security Asghar and
  Henderson Cyber Security Consulting are sole proprietorships with no site or published service list.
- **Security is a feature, not the product.** Corporater (enterprise governance, performance, risk and
  compliance platform) and Dualog (maritime connectivity and software) both secure their own products,
  but neither sells a cybersecurity capability that stands on its own. The same test kept out Effortless365
  (an MSP selling Microsoft 365 and Cisco Meraki, with security blog posts rather than a service),
  ET Works and Favn Software (IT services and software houses where security is a category or a one-line
  bullet), and Visma Group Holding (a holding and software group whose security function serves Visma's
  own companies).

### Corrected

- **Experis: 4 attested pentesters became 40+ estimated security staff.** The pentest editions counted
  four penetration testers there, attested first-hand by the maintainer who works at the company. The
  wider edition is about all in-house security staff, and the maintainer's estimate of that figure is
  40 or more across the consultancy's security disciplines. It is recorded as a guarded estimate rather
  than an attestation, because a broader number is a judgement about a whole unit rather than a count
  of named testers, and it is labelled `estimated` everywhere.
- **DNV Cyber is listed without any DNV Cyber AS entity, because none exists.** The cyber business sits
  in DNV AS, and the row's links now point at DNV's own cyber pages instead of the retired nixu.com.
- **Crayon is now SoftwareOne.** Crayon Group was acquired in July 2025, the Norwegian company is
  SOFTWAREONE AS (registry history CRAYON NORGE AS, CRAYON AS) and its site still trades as Crayon, so
  the new row is named SoftwareOne with the rename recorded.

### Notes

- Each row's estimates are documented in `docs/methodology.md` and can be replaced by a published
  figure, a named attestation or a correction with a source. An issue is enough to overturn one.
