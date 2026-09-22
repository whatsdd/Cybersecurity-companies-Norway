<!-- Thanks for contributing. Corrections with a source are the most valuable contribution there is. -->

## What does this change?

<!-- Adding a company, correcting a fact, adding a capability tag, fixing a dead source, or tooling. -->

## Checklist

- [ ] I edited `data/companies/` (the dataset) and did **not** hand-edit `README.md`, `site/index.html` or `export/`, which are generated.
- [ ] I ran `python3 scripts/validate.py` and it exits 0.
- [ ] I ran `python3 scripts/build.py` and committed the regenerated files.
- [ ] **Every number I added has a source URL** in that company's `sources`, and `employees_source` / `security_staff_source` are set where relevant.
- [ ] I did not guess. Where a company does not publish a figure, I left it out and said so in a note instead. I did **not** put a registry headcount into `security_staff`.
- [ ] Every `security_staff` figure carries a `security_staff_basis`, and any `estimate` or `attestation` names the person standing behind it.
- [ ] The `delivery` label matches the evidence, and `mixed` / `partner-network` have a `delivery_note` explaining how I know.
- [ ] Capability tags are only ones the company publishes, and I have left the list empty rather than padding it where nothing is published.
- [ ] If a rename or acquisition is involved, I recorded it in `legal_name`, `former_names` and `notes`, and the pinned `org_nr` is the entity that actually delivers the work today.
- [ ] `office_in_norway` reflects a **registered Norwegian entity or a published Norwegian address**, not my impression of whether they have Norwegian customers.
- [ ] I set `verification` and `last_verified` honestly (`verified` / `partial` / `unverified`).

## Sources

<!-- Paste the URLs you used, and say which claim each one supports. -->

## Conflict of interest

<!-- Do you work for, with or against any company affected by this change? "No" is a fine answer. -->

## Anything a reviewer should double-check?

<!-- Optional. Flag anything you were unsure about rather than quietly guessing. -->
