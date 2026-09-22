#!/usr/bin/env python3
"""Validate the dataset. Standard library only, exits non-zero on any problem.

This script -- not data/schema.json -- is the authoritative enforcement of the
rules; the schema is the published contract for editors and tooling. The checks
that matter most are the honesty rules:

  * every row has at least one source
  * any number has its own source (no orphan figures)
  * `security_staff` is never a guess, and always says what kind of claim it is
  * a registry headcount is never passed off as a security staff count
  * a delivery model is never asserted without a source
  * an org.nr is never reused across two rows (which would mean a duplicate)

It also reports staleness, because a verified directory rots quietly.

Usage:
    python3 scripts/validate.py
    python3 scripts/validate.py --strict    # treat warnings as failures
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMPANY_DIR = ROOT / "data" / "companies"

CATEGORIES = {"norwegian", "nordic", "international"}
VERIFICATIONS = {"verified", "partial", "unverified"}
SOURCE_TYPES = {"registry", "company-site", "news", "seed-list", "attestation", "estimate", "other"}
STAFF_BASIS = {"company-site", "attestation", "estimate", "crowd-platform"}
STAFF_SCOPE = {"security-only", "security-and-it", "whole-company"}
DELIVERY = {"in-house", "mixed", "partner-network", "unknown"}
CAPABILITIES = {
    "penetration-testing", "red-teaming", "purple-teaming", "social-engineering",
    "vulnerability-assessment", "vulnerability-management", "automated-pentesting",
    "attack-surface-management", "bug-bounty-platform", "crowdsourced-testing",
    "physical-security", "crypto-blockchain-audit", "application-security", "api-security",
    "mobile-security", "code-review", "secure-development", "devsecops", "security-architecture",
    "soc", "incident-response", "threat-intelligence", "threat-hunting", "digital-forensics",
    "malware-analysis", "endpoint-security", "network-security", "email-security",
    "identity-access-management", "pki", "data-security", "backup-recovery", "cloud-security",
    "ot-ics-security", "iot-security", "container-security", "security-audit", "compliance",
    "risk-management", "privacy-gdpr", "nis2-dora", "vciso", "security-training",
    "awareness-training", "tabletop-exercises",
}
REQUIRED = {"id", "name", "category", "office_in_norway", "capabilities", "verification",
            "last_verified", "sources"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
ORG_RE = re.compile(r"^\d{9}$")

# Words that turn a factual directory row into an advertisement. The project's
# rule is no marketing language, so a specialty line containing these is
# flagged for a human to rewrite rather than merged silently.
MARKETING = (
    "leading", "world-class", "world class", "best-in-class", "best in class",
    "premier", "unrivalled", "unrivaled", "number one", "#1", "top-rated", "award-winning",
)

errors: list[str] = []
warnings: list[str] = []


def error(message: str) -> None:
    errors.append(message)


def warn(message: str) -> None:
    warnings.append(message)


def parse_date(value, where: str) -> date | None:
    if value is None:
        return None
    if not isinstance(value, str) or not DATE_RE.match(value):
        error(f"{where}: expected a YYYY-MM-DD date, got {value!r}")
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        error(f"{where}: invalid calendar date {value!r}")
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--strict", action="store_true", help="fail on warnings too")
    parser.add_argument("--today", help="override today's date (YYYY-MM-DD), for tests")
    args = parser.parse_args()
    today = date.fromisoformat(args.today) if args.today else date.today()

    paths = sorted(COMPANY_DIR.glob("*.json"))
    if not paths:
        error(f"no company files found in {COMPANY_DIR}")
        return 1

    org_numbers: dict[str, str] = {}
    domains: dict[str, list[str]] = {}
    ids: set[str] = set()
    records: list[dict] = []

    for path in paths:
        where = path.name
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            error(f"{where}: invalid JSON ({exc})")
            continue
        if not isinstance(record, dict):
            error(f"{where}: expected a JSON object")
            continue
        records.append(record)

        missing = REQUIRED - set(record)
        if missing:
            error(f"{where}: missing required field(s): {', '.join(sorted(missing))}")

        company_id = record.get("id")
        if not company_id:
            error(f"{where}: missing id")
        else:
            if not SLUG_RE.match(company_id):
                error(f"{where}: id {company_id!r} is not a lowercase slug")
            if path.stem != company_id:
                error(f"{where}: file name does not match id {company_id!r}")
            if company_id in ids:
                error(f"{where}: duplicate id {company_id!r}")
            ids.add(company_id)

        if record.get("category") not in CATEGORIES:
            error(f"{where}: category must be one of {sorted(CATEGORIES)}, got {record.get('category')!r}")
        if record.get("verification") not in VERIFICATIONS:
            error(f"{where}: verification must be one of {sorted(VERIFICATIONS)}, got {record.get('verification')!r}")

        office = record.get("office_in_norway")
        if not isinstance(office, bool):
            error(f"{where}: office_in_norway must be true or false, got {office!r}")
        elif office and not record.get("office_cities"):
            warn(f"{where}: office_in_norway is true but no office_cities recorded")
        # A registered Norwegian branch (NUF) or local subsidiary of a foreign
        # group is a real Norwegian office, so category and office can disagree
        # legitimately. What should never happen is claiming an office with no
        # registration and no entity behind it.
        if record.get("category") == "international" and office and not record.get("org_nr"):
            warn(f"{where}: international category, office_in_norway is true and no org_nr is recorded")

        org_nr = record.get("org_nr")
        if org_nr is not None:
            if not isinstance(org_nr, str) or not ORG_RE.match(org_nr):
                error(f"{where}: org_nr must be 9 digits as a string, got {org_nr!r}")
            elif org_nr in org_numbers:
                error(f"{where}: org_nr {org_nr} is already used by {org_numbers[org_nr]} (duplicate company?)")
            else:
                org_numbers[org_nr] = company_id

        website = record.get("website")
        if website is not None:
            if not isinstance(website, str) or not website.startswith(("http://", "https://")):
                error(f"{where}: website must start with http(s)://, got {website!r}")
            else:
                host = website.split("//", 1)[-1].split("/")[0].lower().removeprefix("www.")
                domains.setdefault(host, []).append(company_id)

        for field in ("employees_total", "brreg_employees", "security_staff"):
            value = record.get(field)
            if value is not None:
                if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                    error(f"{where}: {field} must be a non-negative integer, got {value!r}")

        # Numbers must never appear without provenance.
        if record.get("employees_total") is not None and not record.get("employees_source"):
            error(f"{where}: employees_total is set but employees_source is missing")
        if record.get("security_staff") is not None and not record.get("security_staff_source"):
            error(f"{where}: security_staff is set but security_staff_source is missing")
        if record.get("security_staff_source") and record.get("security_staff") is None:
            warn(f"{where}: security_staff_source present but no security_staff value")

        # A staff figure is only meaningful if the reader can tell what kind of
        # claim it is: published by the company, vouched for first-hand by a
        # person, estimated by the maintainer, or a crowdsourcing platform's
        # researcher pool. Everything except `company-site` is a weaker claim
        # than the reader might assume, and the schema keeps them apart.
        basis = record.get("security_staff_basis")
        if basis is not None and basis not in STAFF_BASIS:
            error(f"{where}: security_staff_basis must be one of {sorted(STAFF_BASIS)}, got {basis!r}")
        if record.get("security_staff") is not None and basis is None:
            error(f"{where}: security_staff is set but security_staff_basis is missing")
        own_sources = record.get("sources") if isinstance(record.get("sources"), list) else []
        if basis == "attestation":
            vouched = [s for s in own_sources if isinstance(s, dict) and s.get("type") == "attestation"]
            if not vouched:
                error(f"{where}: basis is attestation but no source of type 'attestation' explains who vouches for it")
            elif not any(s.get("note") for s in vouched):
                error(f"{where}: an attestation source must name who vouches for the figure")
        if basis == "estimate":
            estimated = [s for s in own_sources if isinstance(s, dict) and s.get("type") == "estimate"]
            if not estimated:
                error(f"{where}: basis is estimate but no source of type 'estimate' says who estimated it")
            elif not any(s.get("note") for s in estimated):
                error(f"{where}: an estimate source must say who is estimating and that it is not published")
        if basis == "estimate" and record.get("security_staff_is_minimum") is None:
            warn(f"{where}: an estimated staff count should say whether it is a floor (security_staff_is_minimum)")
        if record.get("security_staff_is_minimum") is not None and not isinstance(record.get("security_staff_is_minimum"), bool):
            error(f"{where}: security_staff_is_minimum must be true or false")
        if record.get("security_staff_is_minimum") and record.get("security_staff") is None:
            warn(f"{where}: security_staff_is_minimum set with no security_staff value")

        scope = record.get("security_staff_scope")
        if scope is not None and scope not in STAFF_SCOPE:
            error(f"{where}: security_staff_scope must be one of {sorted(STAFF_SCOPE)}, got {scope!r}")

        # The delivery model is the field that separates a provider from a
        # reseller, so it cannot be asserted without evidence either.
        delivery = record.get("delivery")
        if delivery is not None and delivery not in DELIVERY:
            error(f"{where}: delivery must be one of {sorted(DELIVERY)}, got {delivery!r}")
        if delivery is not None and not record.get("delivery_source"):
            error(f"{where}: delivery is set but delivery_source is missing")
        if delivery in {"mixed", "partner-network"} and not record.get("delivery_note"):
            error(f"{where}: delivery is {delivery} but delivery_note does not explain how that was established")

        specialty = record.get("specialty")
        if specialty is not None:
            if not isinstance(specialty, str) or not specialty.strip():
                error(f"{where}: specialty must be a non-empty string")
            else:
                if len(specialty) > 160:
                    error(f"{where}: specialty is longer than 160 characters ({len(specialty)})")
                lowered = specialty.lower()
                for word in MARKETING:
                    if word in lowered:
                        warn(f"{where}: specialty contains marketing language ({word!r}), please rewrite factually")
                if not specialty.rstrip().endswith((".", ")", "%")):
                    warn(f"{where}: specialty should read as a sentence (no full stop needed at the end is fine)")

        capabilities = record.get("capabilities")
        if not isinstance(capabilities, list) or not capabilities:
            error(f"{where}: capabilities must be a non-empty list")
        else:
            for capability in capabilities:
                if capability not in CAPABILITIES:
                    error(f"{where}: unknown capability {capability!r}")
            if len(capabilities) != len(set(capabilities)):
                error(f"{where}: duplicate entries in capabilities")

        for field in ("certifications", "former_names", "office_cities"):
            value = record.get(field)
            if value is not None and not isinstance(value, list):
                error(f"{where}: {field} must be a list")

        sources = record.get("sources")
        if not isinstance(sources, list) or not sources:
            error(f"{where}: at least one source is required")
        else:
            for index, source in enumerate(sources):
                label = f"{where}: sources[{index}]"
                if not isinstance(source, dict):
                    error(f"{label}: must be an object")
                    continue
                url = source.get("url")
                if not isinstance(url, str) or not url.startswith(("http://", "https://")):
                    error(f"{label}: url must start with http(s)://, got {url!r}")
                if source.get("type") not in SOURCE_TYPES:
                    error(f"{label}: type must be one of {sorted(SOURCE_TYPES)}, got {source.get('type')!r}")
                parse_date(source.get("checked"), f"{label}.checked")
            if not any(source.get("type") in {"registry", "company-site", "news"} for source in sources if isinstance(source, dict)):
                warn(f"{where}: only seed-list sources -- no primary source attached yet")

        verified_on = parse_date(record.get("last_verified"), f"{where}.last_verified")
        if verified_on:
            age = (today - verified_on).days
            if age > 730:
                error(f"{where}: last_verified is more than 24 months old ({record['last_verified']})")
            elif age > 365:
                warn(f"{where}: last_verified is more than 12 months old ({record['last_verified']})")
            elif age < 0:
                error(f"{where}: last_verified is in the future ({record['last_verified']})")

        if record.get("verification") == "unverified" and record.get("org_nr"):
            warn(f"{where}: marked unverified but has an org_nr")
        if record.get("verification") == "verified" and not record.get("legal_name") and record.get("org_nr"):
            warn(f"{where}: verified row with an org_nr but no legal_name from the registry")

    for host, company_ids in domains.items():
        if len(company_ids) > 1:
            warn(f"website {host} is shared by: {', '.join(sorted(company_ids))}")

    def count(predicate) -> int:
        return sum(1 for r in records if predicate(r))

    counts = {
        "companies": len(records),
        "with Norwegian office": count(lambda r: r.get("office_in_norway") is True),
        "with registry entity": len(org_numbers),
        "publishing a headcount": count(lambda r: r.get("employees_total") is not None),
        "with a staff count": count(lambda r: r.get("security_staff") is not None),
        "with a confirmed staff count": count(lambda r: r.get("security_staff_basis") in {"company-site", "attestation"}),
        "with an estimated staff count": count(lambda r: r.get("security_staff_basis") == "estimate"),
        "delivering in-house": count(lambda r: r.get("delivery") == "in-house"),
        "delivering through partners": count(lambda r: r.get("delivery") in {"mixed", "partner-network"}),
        "with capabilities tagged": count(lambda r: bool(r.get("capabilities"))),
        "capability tags used": len({c for r in records for c in (r.get("capabilities") or [])}),
    }

    for message in warnings:
        print(f"warning: {message}")
    for message in errors:
        print(f"ERROR:   {message}")

    print("\nsummary: " + ", ".join(f"{value} {key}" for key, value in counts.items()))
    print(f"result: {len(errors)} error(s), {len(warnings)} warning(s)")

    if errors or (args.strict and warnings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
