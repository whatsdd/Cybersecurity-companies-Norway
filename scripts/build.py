#!/usr/bin/env python3
"""Generate every published artefact from the dataset. Standard library only.

    data/companies/*.json  ->  README.md
                            ->  site/index.html   (self-contained: CSS and JS inlined)
                            ->  export/companies.{csv,json,yaml}

Because the README, the website and the exports all come from the same files,
they cannot drift apart. CI regenerates them on merge, and `--check` fails the
build if a contributor edited a company file but did not regenerate.

Usage:
    python3 scripts/build.py
    python3 scripts/build.py --check     # exit 1 if the output is stale
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
import urllib.parse
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMPANY_DIR = ROOT / "data" / "companies"
TEMPLATE_DIR = ROOT / "templates"
SITE_DIR = ROOT / "site"
EXPORT_DIR = ROOT / "export"

REPO = "whatsdd/Cybersecurity-companies-Norway"
SITE_URL = "https://whatsdd.github.io/Cybersecurity-companies-Norway/"

CAPABILITY_LABELS = {
    "penetration-testing": "Penetration testing",
    "red-teaming": "Red teaming",
    "purple-teaming": "Purple teaming",
    "social-engineering": "Social engineering",
    "vulnerability-assessment": "Vulnerability assessment",
    "vulnerability-management": "Vulnerability management",
    "automated-pentesting": "Automated pentesting / BAS",
    "attack-surface-management": "Attack surface management",
    "bug-bounty-platform": "Bug bounty platform",
    "crowdsourced-testing": "Crowdsourced testing",
    "physical-security": "Physical security",
    "crypto-blockchain-audit": "Crypto / blockchain audit",
    "application-security": "Application security",
    "api-security": "API security",
    "mobile-security": "Mobile security",
    "code-review": "Secure code review",
    "secure-development": "Secure development",
    "devsecops": "DevSecOps",
    "security-architecture": "Security architecture",
    "soc": "SOC / MDR",
    "incident-response": "Incident response",
    "threat-intelligence": "Threat intelligence",
    "threat-hunting": "Threat hunting",
    "digital-forensics": "Digital forensics",
    "malware-analysis": "Malware analysis",
    "endpoint-security": "Endpoint security",
    "network-security": "Network security",
    "email-security": "Email security",
    "identity-access-management": "Identity and access management",
    "pki": "PKI / certificate services",
    "data-security": "Data protection / DLP",
    "backup-recovery": "Backup and recovery",
    "cloud-security": "Cloud security",
    "ot-ics-security": "OT / ICS security",
    "iot-security": "IoT security",
    "container-security": "Container / Kubernetes security",
    "security-audit": "Security audit",
    "compliance": "Compliance",
    "risk-management": "Risk management",
    "privacy-gdpr": "Privacy / GDPR",
    "nis2-dora": "NIS2 / DORA readiness",
    "vciso": "Virtual CISO",
    "security-training": "Security training",
    "awareness-training": "Awareness training",
    "tabletop-exercises": "Tabletop exercises",
}

CATEGORY_LABELS = {
    "norwegian": "Norwegian",
    "nordic": "Nordic",
    "international": "International",
}

# The chip that says what kind of claim the in-house staff figure is. `published`
# and `attested` are both confirmed by somebody who can be held to it; `estimate`
# is the maintainer's guarded guess and reads as one; `crowd` is a real published
# number that is not a payroll.
STAFF_BASIS_CHIP = {
    "company-site": ("chip-site", "published",
                     "The company publishes this figure itself"),
    "attestation": ("chip-attested", "attested",
                    "A named person vouches for this figure first-hand rather than the company publishing it. See the sources"),
    "estimate": ("chip-estimated", "estimated",
                 "A guarded estimate by the list maintainer from market knowledge, not published by the company and not vouched for first-hand. The weakest basis above unknown, so treat it as a starting point"),
    "crowd-platform": ("chip-crowd", "crowd",
                       "A crowdsourcing platform's contracted researcher pool, not employees"),
}

STAFF_SCOPE_LABEL = {
    "security-only": "security staff only",
    "security-and-it": "security and IT staff together",
    "whole-company": "a company-wide figure",
}

DELIVERY_CHIP = {
    "in-house": ("chip-inhouse", "in-house",
                 "The company's own employees deliver the Norwegian work"),
    "mixed": ("chip-mixed", "mixed",
              "Mostly the company's own staff, with subcontractors for peaks or specialisms"),
    "partner-network": ("chip-partner", "partner-sourced",
                        "No real delivery team in Norway: work is resold or subcontracted to another provider"),
    "unknown": ("chip-registry", "unknown",
                "How the work is delivered has not been established"),
}

# Legal suffixes stay uppercase when we tidy a registry name for display.
UPPERCASE_TOKENS = {"AS", "ASA", "ANS", "DA", "ENK", "NUF", "SA", "STI", "IKS", "AVD", "FLI", "BA", "KF"}


def pretty_legal(name: str) -> str:
    """Registry names are shouty; make them readable without mangling AS/ASA."""
    if not name or not name.isupper():
        return name
    words = []
    for word in name.replace("&", "& ").split():
        stripped = word.strip(".,&")
        # Short all-caps tokens are acronyms (IT, EDB, DNV, NFH, WM) and stay as
        # they are; AS/ASA and friends are legal forms and always stay uppercase.
        is_acronym = stripped.isalpha() and stripped.isupper() and len(stripped) <= 4
        if stripped in UPPERCASE_TOKENS or is_acronym or not stripped.isalpha():
            words.append(word)
        else:
            words.append(word[:1] + word[1:].lower())
    text = " ".join(words).replace("& ", "& ")
    return text.replace("&", "&").strip()


def headcount(record: dict):
    """The employee figure to order by: the company's own, else the registry's."""
    return record.get("employees_total") or record.get("brreg_employees") or 0


def rank_key(record: dict):
    """Ordering: office in Norway first, then in-house security staff, then headcount.

    This is an ordering of known numbers, not a quality rating. A company with no
    staff count sorts last, which reflects what it publishes rather than how good
    it is, and the column says so.

    Only in-house counts boost the rank. A crowdsourcing platform's researcher
    pool is a real number but it is not a payroll, so it sorts below every
    company with staff while keeping its own label.
    """
    staff = record.get("security_staff")
    basis = record.get("security_staff_basis")
    # 0 = confirmed by the company or a named person, 1 = labelled estimate,
    # 2 = no in-house figure at all.
    if staff is not None and basis in {"company-site", "attestation"}:
        basis_group = 0
    elif staff is not None and basis == "estimate":
        basis_group = 1
    else:
        basis_group = 2
    in_house = staff is not None and basis in {"company-site", "attestation", "estimate"}
    return (
        0 if record.get("office_in_norway") else 1,
        0 if in_house else 1,
        basis_group,
        -(staff or 0),
        -headcount(record),
        record["name"].lower(),
    )


def load_companies() -> list[dict]:
    records = []
    for path in sorted(COMPANY_DIR.glob("*.json")):
        records.append(json.loads(path.read_text(encoding="utf-8")))
    records.sort(key=rank_key)
    return records


def staff_issue_url(name: str) -> str:
    """A prefilled issue so a reader can fill in a missing in-house staff count."""
    query = urllib.parse.urlencode(
        {"template": "update-company.yml", "title": f"In-house security staff for {name}"}
    )
    return f"https://github.com/{REPO}/issues/new?{query}"


def days_since(value: str | None, today: date) -> int | None:
    if not value:
        return None
    try:
        return (today - date.fromisoformat(value)).days
    except ValueError:
        return None


def staleness(days: int | None) -> str:
    if days is None:
        return "stale"
    if days <= 182:
        return "fresh"
    if days <= 365:
        return "aging"
    return "stale"


def employees_cell(record: dict, for_html: bool) -> str:
    total = record.get("employees_total")
    brreg = record.get("brreg_employees")
    as_of = record.get("employees_as_of")
    brreg_as_of = record.get("brreg_employees_as_of")
    not_stated = '<span class="muted">Not stated</span>' if for_html else "Not stated"

    if total is None and brreg is None:
        return not_stated

    if total is not None:
        chip = '<span class="chip chip-site" title="Stated by the company">site</span>' if for_html else " (site)"
        value = f'<span class="num-strong">{total:,}</span> {chip}' if for_html else f"{total:,}{chip}"
        if brreg is not None and brreg != total:
            registry = (
                f'<span class="as-of">registry: {brreg:,}'
                + (f" ({brreg_as_of})" if brreg_as_of else "")
                + "</span>"
            ) if for_html else f"<br><sub>registry: {brreg:,}</sub>"
            value += registry
        elif for_html and as_of:
            value += f'<span class="as-of">as of {as_of}</span>'
        elif not for_html and as_of:
            value += f"<br><sub>site, {as_of}</sub>"
        return value

    chip = '<span class="chip chip-registry" title="Headcount reported to Enhetsregisteret for this legal entity">registry</span>' if for_html else " (registry)"
    value = f'<span class="num-strong">{brreg:,}</span> {chip}' if for_html else f"{brreg:,}{chip}"
    if for_html and brreg_as_of:
        value += f'<span class="as-of">as of {brreg_as_of}</span>'
    elif not for_html:
        value += "<br><sub>registry</sub>"
    return value


def staff_cell(record: dict, for_html: bool) -> str:
    """The headline column: in-house security staff, or an explicit unknown.

    When the number is unknown the row says ?? and offers a prefilled issue
    instead of a plausible-looking blank, because a blank reads as zero.
    """
    staff = record.get("security_staff")
    if staff is None:
        if for_html:
            url = staff_issue_url(record["name"])
            return (
                '<span class="unknown" title="No in-house security staff count has been established for this company">??</span>'
                f' <a class="fill" href="{url}" rel="noopener" '
                'title="We could not find this number - send it in and it gets added">add it</a>'
            )
        return "??"

    label = f"{staff:,}" + ("+" if record.get("security_staff_is_minimum") else "")
    basis = record.get("security_staff_basis")
    css, text, title = STAFF_BASIS_CHIP.get(basis, ("chip-registry", basis or "unknown", "Basis not recorded"))
    if record.get("security_staff_scope") and record["security_staff_scope"] != "security-only":
        title += f". This figure counts {STAFF_SCOPE_LABEL.get(record['security_staff_scope'], record['security_staff_scope'])}"
    if for_html:
        return (f'<span class="num-strong num-tester">{label}</span> '
                f'<span class="chip {css}" title="{title}">{text}</span>')
    return f"**{label}** <sub>{text}</sub>"


def delivery_cell(record: dict, for_html: bool) -> str:
    delivery = record.get("delivery")
    if delivery is None:
        return '<span class="unknown" title="How the work is delivered has not been established">?</span>' if for_html else "?"
    css, text, title = DELIVERY_CHIP.get(delivery, ("chip-registry", delivery, ""))
    if for_html:
        return f'<span class="chip {css}" title="{title}">{text}</span>'
    return text


def capabilities_cell(record: dict, for_html: bool, limit: int = 4) -> str:
    specialty = record.get("specialty")
    capabilities = record.get("capabilities") or []
    if for_html:
        out = f'<p class="specialty">{specialty}</p>' if specialty else ""
        if capabilities:
            labels = [CAPABILITY_LABELS.get(c, c) for c in capabilities]
            shown, rest = labels[:limit], len(labels) - limit
            tags = "".join(f'<span class="service-tag">{label}</span>' for label in shown)
            if rest:
                tags += f'<span class="service-more">+{rest} more</span>'
            out += f'<div class="services">{tags}</div>'
        else:
            out += '<span class="muted">Not stated</span>'
        return out
    if not capabilities and not specialty:
        return "Not stated"
    labels = [CAPABILITY_LABELS.get(c, c) for c in capabilities]
    shown, rest = labels[:3], max(0, len(labels) - 3)
    tags = " · ".join(shown) + (f' <sub>+{rest}</sub>' if rest else "")
    return f"{specialty}<br><sub>{tags}</sub>" if specialty else tags


def office_cell(record: dict, for_html: bool) -> str:
    cities = ", ".join(record.get("office_cities") or [])
    if record.get("office_in_norway"):
        mark = '<span class="yes">Yes</span>' if for_html else "Yes"
        if cities:
            mark += f'<span class="cities">{cities}</span>' if for_html else f" ({cities})"
        else:
            mark += '<span class="cities">address not recorded</span>' if for_html else ""
        return mark
    mark = '<span class="no">No</span>' if for_html else "No"
    note = "no Norwegian entity" if record.get("org_nr") is None else "not recorded"
    return mark + (f'<span class="cities">{note}</span>' if for_html else f" ({note})")


def company_cell(record: dict, for_html: bool) -> str:
    name = record["name"]
    website = record.get("website")
    legal = record.get("legal_name")
    former = record.get("former_names") or []
    bits = []
    if legal and legal.upper().replace(" ", "") != name.upper().replace(" ", ""):
        bits.append(pretty_legal(legal))
    if former:
        shown = ", ".join(pretty_legal(f) for f in former[:2])
        if len(former) > 2:
            shown += f" and {len(former) - 2} more"
        bits.append("formerly " + shown)
    flagged = record.get("verification") == "unverified"
    if for_html:
        button = (f'<button type="button" class="expand" aria-expanded="false" '
                  f'aria-controls="detail-{record["id"]}">{name}</button>')
        out = button
        if flagged:
            out += ' <span class="chip chip-flag" title="See the notes">unverified</span>'
        if bits:
            out += f'<span class="company-meta">{" · ".join(bits)}</span>'
        if website:
            out += f'<a class="company-site" href="{website}" rel="noopener">{website.replace("https://", "").rstrip("/")}</a>'
        return out
    out = f"**{name}**"
    if flagged:
        out += " ⚠️"
    if bits:
        out += f"<br><sub>{' · '.join(bits)}</sub>"
    if website:
        out += f"<br>[{website.replace('https://', '').rstrip('/')}]({website})"
    return out


def org_cell(record: dict, for_html: bool) -> str:
    org_nr = record.get("org_nr")
    founded = record.get("founded")
    year = founded[:4] if founded else None
    if for_html:
        out = f'<code>{org_nr}</code>' if org_nr else '<span class="muted">n/a</span>'
        if year:
            out += f'<span class="as-of">founded {year}</span>'
        return out
    out = org_nr or "n/a"
    if year:
        out += f"<br><sub>founded {year}</sub>"
    return out


def verified_cell(record: dict, for_html: bool, today: date) -> str:
    value = record.get("last_verified")
    days = days_since(value, today)
    state = staleness(days)
    ages = {"fresh": "within 6 months", "aging": "6-12 months", "stale": "over 12 months"}
    if for_html:
        return (f'<span class="dot dot-{state}" title="Verified {ages[state]} ago"></span> '
                f'<span class="as-of">{value or "unknown"}</span>')
    return f"{value or 'unknown'}"


README_COLUMNS = [
    "Company",
    "In-house security staff",
    "Employees",
    "Office in Norway",
    "Delivery",
    "Speciality and capabilities",
    "Org. no.",
    "Last updated",
]


def readme_table(records: list[dict], today: date) -> str:
    lines = ["| " + " | ".join(README_COLUMNS) + " |", "| " + " | ".join("---" for _ in README_COLUMNS) + " |"]
    for record in records:
        lines.append("| " + " | ".join([
            company_cell(record, False),
            staff_cell(record, False),
            employees_cell(record, False),
            office_cell(record, False),
            delivery_cell(record, False),
            capabilities_cell(record, False),
            org_cell(record, False),
            verified_cell(record, False, today),
        ]) + " |")
    return "\n".join(lines)


def search_blob(record: dict) -> str:
    parts = [
        record["name"],
        record.get("legal_name") or "",
        " ".join(record.get("former_names") or []),
        " ".join(record.get("office_cities") or []),
        " ".join(record.get("capabilities") or []),
        " ".join(CAPABILITY_LABELS.get(c, c) for c in record.get("capabilities") or []),
        record.get("specialty") or "",
        record.get("org_nr") or "",
        record.get("delivery") or "",
        record.get("notes") or "",
    ]
    return " ".join(parts).lower().replace('"', "")


def site_rows(records: list[dict], today: date, ranks: dict[str, int]) -> str:
    out = []
    for record in records:
        days = days_since(record.get("last_verified"), today)
        state = staleness(days)
        attrs = {
            "data-name": record["name"].lower(),
            "data-rank": ranks.get(record["id"], 0),
            "data-category": record["category"],
            "data-category-label": CATEGORY_LABELS.get(record["category"], record["category"]),
            "data-office": "true" if record.get("office_in_norway") else "false",
            "data-employees": record.get("employees_total") or record.get("brreg_employees") or "",
            "data-staff": record.get("security_staff") or "",
            "data-staff-basis": record.get("security_staff_basis") or "",
            "data-delivery": record.get("delivery") or "",
            "data-has-employees": "true" if (record.get("employees_total") is not None or record.get("brreg_employees") is not None) else "false",
            "data-has-staff": "true" if record.get("security_staff") is not None else "false",
            "data-org": record.get("org_nr") or "",
            "data-capabilities": " ".join(record.get("capabilities") or []),
            "data-capability-count": str(len(record.get("capabilities") or [])),
            "data-verification": record.get("verification", ""),
            "data-verified": record.get("last_verified") or "",
            "data-detail-id": f"detail-{record['id']}",
            "data-search": search_blob(record),
            "data-verified-state": state,
        }
        attr_text = " ".join(f'{key}="{value}"' for key, value in attrs.items())
        out.append(f'          <tr class="data-row" {attr_text}>')
        out.append(f'            <td class="cell-company" data-label="Company">{company_cell(record, True)}</td>')
        out.append(f'            <td class="num" data-label="In-house security staff">{staff_cell(record, True)}</td>')
        out.append(f'            <td class="num" data-label="Employees">{employees_cell(record, True)}</td>')
        out.append(f'            <td data-label="Office in Norway">{office_cell(record, True)}</td>')
        out.append(f'            <td data-label="Delivery">{delivery_cell(record, True)}</td>')
        out.append(f'            <td data-label="Speciality and capabilities">{capabilities_cell(record, True)}</td>')
        out.append(f'            <td data-label="Org. no. / founded">{org_cell(record, True)}</td>')
        out.append(f'            <td class="num" data-label="Last updated">{verified_cell(record, True, today)}</td>')
        out.append("          </tr>")

        # Detail row: everything a reader needs to audit the row.
        blocks = []
        if record.get("notes"):
            blocks.append(f'<div class="detail-block"><h4>Notes</h4><p>{record["notes"]}</p></div>')
        facts = []
        if record.get("legal_name"):
            facts.append(f'Legal name: <code>{record["legal_name"]}</code>')
        if record.get("org_nr"):
            facts.append(f'Org. no.: <code>{record["org_nr"]}</code>')
        if record.get("founded"):
            facts.append(f"Registered: {record['founded']}")
        if record.get("former_names"):
            facts.append("Former names: " + ", ".join(record["former_names"]))
        if record.get("certifications"):
            facts.append("Certifications: " + ", ".join(record["certifications"]))
        if record.get("employees_note"):
            facts.append("Headcount note: " + record["employees_note"])
        if record.get("security_staff_note"):
            facts.append("Staff note: " + record["security_staff_note"])
        if record.get("security_staff_basis"):
            basis_line = "Staff basis: " + record["security_staff_basis"]
            if record.get("security_staff_scope"):
                basis_line += f" ({STAFF_SCOPE_LABEL.get(record['security_staff_scope'], record['security_staff_scope'])})"
            facts.append(basis_line)
        if record.get("delivery_note"):
            facts.append("Delivery: " + record["delivery_note"])
        if record.get("capabilities"):
            facts.append("Capabilities: " + ", ".join(CAPABILITY_LABELS.get(c, c) for c in record["capabilities"]))
        facts.append(f"Verification: {record.get('verification', 'unknown')}"
                     + (f" by {record['verified_by']}" if record.get("verified_by") else ""))
        blocks.append('<div class="detail-block"><h4>Record</h4><ul>'
                      + "".join(f"<li>{fact}</li>" for fact in facts) + "</ul></div>")
        sources = record.get("sources") or []
        source_items = "".join(
            f'<li><a href="{s["url"]}" rel="noopener">{s["url"]}</a> '
            f'<span class="src-type">{s.get("type")} · checked {s.get("checked")}</span>'
            + (f'<br><span class="src-type">{s["note"]}</span>' if s.get("note") else "")
            + "</li>"
            for s in sources
        )
        blocks.append(f'<div class="detail-block"><h4>Sources</h4><ul>{source_items}</ul></div>')
        out.append(f'          <tr class="detail-row is-hidden" id="detail-{record["id"]}">'
                   f'<td colspan="8"><div class="detail-grid">{"".join(blocks)}</div></td></tr>')
    return "\n".join(out)


def stat_tile(value, label: str, muted: bool = False) -> str:
    css = "stat-value is-muted" if muted else "stat-value"
    return f'<li><span class="{css}">{value}</span><span class="stat-label">{label}</span></li>'


YAML_KEYWORDS = {"true", "false", "null", "yes", "no", "on", "off", "~", ""}

# Scalars YAML would reinterpret if left plain. Dates would become Date objects
# and digit strings would become integers, so the YAML export would silently
# disagree with the JSON export about types -- an org_nr that arrives as a
# number breaks anyone joining on it. Anything matching these is quoted to keep
# the export type-faithful.
YAML_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}([T ].*)?$")
YAML_NUMBER = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$")


def yaml_scalar(value) -> str:
    """Render a scalar, quoting whenever it could be read as anything else."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    needs_quotes = (
        text.strip() != text
        or text.lower() in YAML_KEYWORDS
        or text[0] in "-?:,[]{}#&*!|>'\"%@`"
        or ": " in text
        or " #" in text
        or any(char in text for char in "\n\t\"'")
        or YAML_DATE.match(text) is not None
        or YAML_NUMBER.match(text) is not None
    )
    return json.dumps(text, ensure_ascii=False) if needs_quotes else text


def yaml_lines(value, indent: int) -> list[str]:
    """Emit YAML as lines with explicit indentation.

    Mechanical and boring on purpose: this handles exactly the shapes the
    dataset uses (scalars, lists of scalars, lists of flat maps), and CI parses
    the result with a real YAML parser so a mistake here cannot ship.
    """
    pad = " " * indent
    if isinstance(value, dict):
        lines: list[str] = []
        for key, item in value.items():
            if isinstance(item, (dict, list)) and item:
                lines.append(f"{pad}{key}:")
                lines.extend(yaml_lines(item, indent + 2))
            elif isinstance(item, dict):
                lines.append(f"{pad}{key}: {{}}")
            elif isinstance(item, list):
                lines.append(f"{pad}{key}: []")
            else:
                lines.append(f"{pad}{key}: {yaml_scalar(item)}")
        return lines
    if isinstance(value, list):
        lines = []
        for item in value:
            if isinstance(item, (dict, list)) and item:
                nested = yaml_lines(item, indent + 2)
                lines.append(f"{pad}- {nested[0][indent + 2:]}")
                lines.extend(nested[1:])
            else:
                lines.append(f"{pad}- {yaml_scalar(item)}")
        return lines
    return [f"{pad}{yaml_scalar(value)}"]


def flat_row(record: dict) -> dict:
    row = {}
    for key, value in record.items():
        if isinstance(value, list):
            if key == "sources":
                row[key] = "; ".join(f'{s["url"]} ({s.get("type")}, {s.get("checked")})' for s in value)
            else:
                row[key] = "; ".join(str(item) for item in value)
        elif isinstance(value, bool):
            row[key] = "true" if value else "false"
        else:
            row[key] = "" if value is None else value
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="fail if any generated file is out of date")
    parser.add_argument("--today", help="override today's date (YYYY-MM-DD)")
    args = parser.parse_args()

    today = date.fromisoformat(args.today) if args.today else date.today()
    records = load_companies()
    if not records:
        sys.exit("no company records found")

    with_office = [r for r in records if r.get("office_in_norway")]
    without_office = [r for r in records if not r.get("office_in_norway")]
    with_org = [r for r in records if r.get("org_nr")]
    # "Publishing a headcount" means the company states the figure itself. Many
    # more rows carry a registry figure, which is a different claim.
    with_employees = [r for r in records if r.get("employees_total") is not None]
    with_any_headcount = [r for r in records if r.get("employees_total") is not None or r.get("brreg_employees") is not None]
    with_staff = [r for r in records if r.get("security_staff") is not None]
    confirmed_staff = [r for r in records if r.get("security_staff_basis") in {"company-site", "attestation"}]
    estimated_staff = [r for r in records if r.get("security_staff_basis") == "estimate"]
    last_updated = max((r.get("last_verified") or "") for r in records)
    # The build output must depend only on the data, not on the day it runs, or
    # `--check` would report every checkout as stale the next morning.
    generated = last_updated
    tag_use: dict[str, int] = {}
    for record in records:
        for capability in record.get("capabilities") or []:
            tag_use[capability] = tag_use.get(capability, 0) + 1

    counts = {
        "TOTAL": len(records),
        "WITH_OFFICE": len(with_office),
        "WITH_ORG_NR": len(with_org),
        "WITH_EMPLOYEES": len(with_employees),
        "WITH_ANY_HEADCOUNT": len(with_any_headcount),
        "WITH_STAFF": len(with_staff),
        "CONFIRMED_STAFF": len(confirmed_staff),
        "PUBLISHED_STAFF": sum(1 for r in records if r.get("security_staff_basis") == "company-site"),
        "ATTESTED_STAFF": sum(1 for r in records if r.get("security_staff_basis") == "attestation"),
        "ESTIMATED_STAFF": len(estimated_staff),
        "CROWD_STAFF": sum(1 for r in records if r.get("security_staff_basis") == "crowd-platform"),
        "UNKNOWN_STAFF": sum(1 for r in records if r.get("security_staff") is None),
        "IN_HOUSE": sum(1 for r in records if r.get("delivery") == "in-house"),
        "MIXED": sum(1 for r in records if r.get("delivery") == "mixed"),
        "PARTNER": sum(1 for r in records if r.get("delivery") == "partner-network"),
        "DELIVERY_UNKNOWN": sum(1 for r in records if r.get("delivery") in {None, "unknown"}),
        "CAPABILITY_TAGS": len(tag_use),
        "CAPABILITY_LINKS": sum(tag_use.values()),
        "COUNT_PRIMARY": len(with_office),
        "COUNT_SECONDARY": len(without_office),
        "COUNT_NORWEGIAN": sum(1 for r in records if r["category"] == "norwegian"),
        "COUNT_NORDIC": sum(1 for r in records if r["category"] == "nordic"),
        "COUNT_INTERNATIONAL": sum(1 for r in records if r["category"] == "international"),
        "LAST_UPDATED": last_updated,
        "GENERATED": generated,
        "REPO": REPO,
        "SITE_URL": SITE_URL,
    }

    # ---- README -----------------------------------------------------------
    readme_template = (TEMPLATE_DIR / "README.md.tmpl").read_text(encoding="utf-8")

    renames = []
    for record in records:
        if record.get("former_names"):
            history = " → ".join(record["former_names"] + [record.get("legal_name") or record["name"]])
            renames.append(f"- **{record['name']}**: *{history}*")
            if record.get("notes"):
                # Keep the prose separate from the mechanical registry history, and
                # use one arrow style throughout.
                renames.append(f"  - {record['notes'].replace('->', '→')}")
    rename_block = "\n".join(renames) if renames else "_No renames recorded yet._"

    readme = readme_template
    for key, value in counts.items():
        readme = readme.replace("{{" + key + "}}", str(value))
    readme = readme.replace("{{TABLE_PRIMARY}}", readme_table(with_office, today))
    readme = readme.replace("{{TABLE_SECONDARY}}", readme_table(without_office, today))
    readme = readme.replace("{{RENAMES}}", rename_block)

    # ---- site -------------------------------------------------------------
    site_template = (TEMPLATE_DIR / "site.html.tmpl").read_text(encoding="utf-8")
    css = (TEMPLATE_DIR / "site.css").read_text(encoding="utf-8")
    js = (TEMPLATE_DIR / "site.js").read_text(encoding="utf-8")
    capability_options = "\n          ".join(
        f'<option value="{slug}">{label}</option>'
        for slug, label in sorted(CAPABILITY_LABELS.items(), key=lambda kv: kv[1])
    )
    stats = "\n      ".join([
        stat_tile(counts["TOTAL"], "companies listed"),
        stat_tile(counts["WITH_STAFF"], "in-house staff counts known"),
        stat_tile(counts["CONFIRMED_STAFF"], "of those confirmed"),
        stat_tile(counts["ESTIMATED_STAFF"], "labelled estimates"),
        stat_tile(counts["UNKNOWN_STAFF"], "staff count still unknown"),
        stat_tile(f"{counts['CAPABILITY_TAGS']}", "capability tags in use"),
        stat_tile(counts["WITH_OFFICE"], "with an office in Norway"),
        stat_tile(counts["WITH_ANY_HEADCOUNT"], "with a headcount figure"),
    ])

    site = site_template
    site = site.replace("{{CSS}}", css).replace("{{JS}}", js)
    site = site.replace("{{TITLE}}", "Cybersecurity and information security companies in Norway")
    site = site.replace("{{HEADLINE}}", "Cybersecurity companies in Norway")
    site = site.replace(
        "{{DESCRIPTION}}",
        f"A verified, community-maintained directory of {counts['TOTAL']} cybersecurity and information "
        "security providers serving Norway, with in-house staff counts, delivery models, capability tags and sources.",
    )
    site = site.replace(
        "{{LEDE}}",
        f"{counts['TOTAL']} companies that sell cybersecurity and information security work to customers in "
        "Norway: penetration testing, red teaming and security assessment, 24/7 SOC and incident response, "
        "cloud and OT security, identity, forensics, GRC and security training. Every row carries its source, "
        "and the in-house staff figure says whether anyone has actually confirmed it.",
    )
    site = site.replace("{{STATS}}", stats)
    site = site.replace("{{CAPABILITY_OPTIONS}}", capability_options)
    ranks = {record["id"]: index for index, record in enumerate(records)}
    site = site.replace("{{ROWS_PRIMARY}}", site_rows(with_office, today, ranks))
    site = site.replace("{{ROWS_SECONDARY}}", site_rows(without_office, today, ranks))
    for key, value in counts.items():
        site = site.replace("{{" + key + "}}", str(value))

    # ---- exports ----------------------------------------------------------
    field_order = [
        "id", "name", "legal_name", "website", "category", "org_nr", "office_in_norway", "office_cities",
        "security_staff", "security_staff_basis", "security_staff_is_minimum", "security_staff_scope",
        "security_staff_source", "security_staff_note",
        "employees_total", "employees_source", "employees_note", "employees_as_of", "brreg_employees",
        "brreg_employees_as_of",
        "delivery", "delivery_source", "delivery_note",
        "specialty", "capabilities", "certifications", "founded", "former_names", "notes",
        "verification", "last_verified", "verified_by", "sources",
    ]
    rows = [flat_row(r) for r in records]
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=field_order, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    csv_text = buffer.getvalue()

    metadata = {
        "generated": generated,
        "last_verified": last_updated,
        "count": len(records),
        "license": "CC BY 4.0",
        "attribution": "Started in 2023 by Ahmad Abdur Rehman (https://ahmad.science/, https://www.linkedin.com/in/ahmadscience/) as a list of penetration testing companies in Norway. Continued as an open dataset covering cybersecurity and information security companies.",
        "source_repository": f"https://github.com/{REPO}",
        "methodology": "https://github.com/" + REPO + "/blob/main/docs/methodology.md",
        "notes": [
            "security_staff is null when no in-house count has been established; null does not mean zero.",
            "whenever security_staff is set, security_staff_basis says what kind of claim it is: "
            "company-site (published by the company), attestation (vouched for first-hand), estimate "
            "(the maintainer's guarded estimate, the weakest basis) or crowd-platform (a researcher pool, not staff).",
            "security_staff is never taken from Enhetsregisteret: brreg_employees is a whole-entity headcount and "
            "cannot be split into security and non-security staff.",
            "delivery says whether the Norwegian work is done by the company's own staff, mixed, or resold to a "
            "partner network; null or unknown means it was not established.",
            "capabilities are the tags the company itself publishes, and specialty is a plain-language summary.",
            "office_in_norway is false only when no Norwegian entity was found, not when staff are absent.",
            "brreg_* fields come from Enhetsregisteret, the Norwegian register of legal entities.",
        ],
    }
    json_text = json.dumps({**metadata, "companies": records}, indent=2, ensure_ascii=False) + "\n"

    yaml_text = "\n".join(yaml_lines({**metadata, "companies": [
        {**{key: r[key] for key in field_order if key in r}, **{k: v for k, v in r.items() if k not in field_order}}
        for r in records
    ]}, 0)) + "\n"

    exports_readme = f"""# Exports

Generated from [`data/companies/`](../data/companies) by `scripts/build.py`. Do not edit by hand.

| File | Contents |
| --- | --- |
| `companies.csv` | One row per company, lists joined with `; `. |
| `companies.json` | Same records, plus metadata. |
| `companies.yaml` | Same as JSON, in YAML. |

**Attribution (required by the licence):** this dataset was started in 2023 by
[Ahmad Abdur Rehman](https://ahmad.science/) ([LinkedIn](https://www.linkedin.com/in/ahmadscience/))
as a list of penetration testing companies in Norway, and is published under [CC BY 4.0](../LICENSE).
If you reuse it, credit the author and link to <https://github.com/{REPO}>.

Field notes: `security_staff` is `null` when no in-house count has been established, null means
"not stated" and never zero; whenever it is set, `security_staff_basis` says whether the figure is
`company-site` (published), `attestation` (vouched for first-hand), `estimate` (the maintainer's
guarded estimate) or `crowd-platform` (a researcher pool, not staff). Registry headcounts live in
`brreg_employees` and are never presented as security staff. `delivery` is `in-house`, `mixed`,
`partner-network` or `unknown`. `capabilities` are the company's own tags and `specialty` is a
plain-language summary. `office_in_norway` is `false` only when no Norwegian entity was found.

Dataset version: {last_updated}.
"""

    outputs = {
        ROOT / "README.md": readme,
        SITE_DIR / "index.html": site,
        EXPORT_DIR / "companies.csv": csv_text,
        EXPORT_DIR / "companies.json": json_text,
        EXPORT_DIR / "companies.yaml": yaml_text,
        EXPORT_DIR / "README.md": exports_readme,
    }

    if args.check:
        stale = []
        for path, content in outputs.items():
            existing = path.read_text(encoding="utf-8") if path.exists() else None
            if existing != content:
                stale.append(path.relative_to(ROOT))
        if stale:
            print("generated files are out of date:")
            for path in stale:
                print(f"  - {path}")
            print("\nrun: python3 scripts/build.py")
            return 1
        print(f"generated files are up to date ({len(outputs)} files)")
        return 0

    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")
    print(f"\n{len(records)} companies · {counts['WITH_OFFICE']} with a Norwegian office · "
          f"{counts['WITH_STAFF']} with an in-house staff count "
          f"({counts['CONFIRMED_STAFF']} confirmed, {counts['ESTIMATED_STAFF']} estimated, "
          f"{counts['CROWD_STAFF']} crowd) · {counts['UNKNOWN_STAFF']} still unknown · "
          f"{counts['PARTNER']} partner-sourced, {counts['MIXED']} mixed, {counts['IN_HOUSE']} in-house · "
          f"{counts['CAPABILITY_TAGS']} capability tags used")
    return 0


if __name__ == "__main__":
    sys.exit(main())
