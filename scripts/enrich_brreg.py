#!/usr/bin/env python3
"""Enrich company records from the Norwegian Central Coordinating Register for
Legal Entities (Enhetsregisteret), via the free, open Brønnøysund Register
Centre API. No API key, no dependencies.

Two modes:

  propose   Search the registry for an entity that matches a company name and
            print ranked candidates. This is ASSISTIVE ONLY. The registry's
            name search is fuzzy -- searching for "NorSIS" returns a carpentry
            sole proprietorship -- so a human must confirm the organisasjonsnummer
            once. After that, `refresh` is safe and automatic.

  refresh   For entries that already carry a confirmed `org_nr`, re-read the
            registry and report (or apply) the derived fields: employee count,
            registered address, homepage, founding date, rename history.

Usage:
    python3 scripts/enrich_brreg.py propose --all
    python3 scripts/enrich_brreg.py propose --id river-security
    python3 scripts/enrich_brreg.py refresh --all
    python3 scripts/enrich_brreg.py refresh --all --write

Registry field notes:
  * `antallAnsatte` is the headcount the company reported to the registry. It
    covers the whole legal entity, not just the security staff, and it can be
    stale, which is why we always store `brreg_employees_as_of`. It is never
    promoted into `security_staff`: the registry does not say what anyone does.
  * `naeringskode1` is the registered industry code. This dataset uses it only
    as a signal when hunting for the right entity, never as a fact about what a
    company sells.
  * `historiskeNavn` is the authoritative rename history. This is what lets us
    state "formerly Watchcom" as a verified fact instead of folklore.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMPANY_DIR = ROOT / "data" / "companies"
CACHE_DIR = ROOT / ".build-tmp" / "brreg-cache"
PROPOSAL_PATH = ROOT / ".build-tmp" / "brreg-proposals.json"

API = "https://data.brreg.no/enhetsregisteret/api/enheter"

# Legal forms and filler words that carry no identifying weight when matching a
# company name from the list against a registry entry.
LEGAL_TOKENS = {
    "AS", "ASA", "ANS", "DA", "ENK", "NUF", "SA", "STI", "BA", "IKS", "KF",
    "FKF", "AVD", "FILIAL", "NORGE", "NORWAY", "NORSK", "NORSKE", "NORWEGIAN",
}


def _norm(value: str) -> str:
    """Normalise a company name for comparison."""
    value = value.upper()
    for char, repl in (("&", " OG "), ("Æ", "AE"), ("Ø", "O"), ("Å", "A")):
        value = value.replace(char, repl)
    cleaned = []
    for char in value:
        cleaned.append(char if (char.isalnum() or char == " " or char == "-") else " ")
    return " ".join("".join(cleaned).split())


def _tokens(value: str) -> list[str]:
    return [t for t in _norm(value).replace("-", " ").split() if t and t not in LEGAL_TOKENS]


def _fetch(url: str, cache_key: str) -> dict:
    """GET JSON with an on-disk cache so repeated review runs stay cheap."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cached = CACHE_DIR / f"{cache_key}.json"
    if cached.exists():
        try:
            return json.loads(cached.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Cybersecurity-companies-Norway/1.0 (community directory; +https://github.com/)",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        raw = response.read().decode("utf-8")
    data = json.loads(raw)
    cached.write_text(raw, encoding="utf-8")
    time.sleep(0.34)  # be polite to a public API we depend on
    return data


def search(name: str) -> list[dict]:
    query = urllib.parse.urlencode({"navn": name, "size": 25})
    key = "search-" + _norm(name).replace(" ", "_")
    data = _fetch(f"{API}?{query}", key)
    return (data.get("_embedded") or {}).get("enheter", []) or []


def score(target: str, candidate: dict) -> float:
    """Heuristic 0..1 confidence that a registry entry is the company we mean."""
    want = set(_tokens(target))
    got = set(_tokens(candidate.get("navn", "")))
    if not want or not got:
        return 0.0

    overlap = len(want & got) / len(want)
    # Extra tokens the candidate carries that we did not ask for mean it is
    # probably a different, unrelated business ("...GINTAUTAS NORSIS").
    extra = len(got - want)
    value = overlap - (0.18 * extra)
    if got == want:
        value += 0.35
    if candidate.get("organisasjonsform", {}).get("kode") in {"AS", "ASA", "NUF"}:
        value += 0.12
    if candidate.get("registrertIForetaksregisteret"):
        value += 0.08
    if candidate.get("harRegistrertAntallAnsatte"):
        value += 0.08
    if candidate.get("konkurs") or candidate.get("underAvvikling"):
        value -= 0.5
    return max(0.0, min(1.0, value))


def describe(candidate: dict) -> str:
    org_form = candidate.get("organisasjonsform", {}).get("kode", "?")
    address = candidate.get("forretningsadresse") or {}
    city = address.get("poststed") or address.get("kommune") or "-"
    country = address.get("landkode") or "-"
    employees = candidate.get("antallAnsatte")
    names = [h.get("navn") for h in candidate.get("historiskeNavn") or []]
    flags = []
    if candidate.get("konkurs"):
        flags.append("BANKRUPT")
    if candidate.get("underAvvikling"):
        flags.append("WINDING-UP")
    return (
        f"{candidate.get('organisasjonsnummer')}  {candidate.get('navn')} "
        f"[{org_form}] emp={employees if employees is not None else '-'} "
        f"{city}/{country} founded={candidate.get('stiftelsesdato') or '-'}"
        f"{' former=' + ' <- '.join(names) if names else ''}"
        f"{' ' + ','.join(flags) if flags else ''}"
    )


def load_companies(only_id: str | None = None) -> list[tuple[Path, dict]]:
    if not COMPANY_DIR.is_dir():
        sys.exit(f"No company data yet at {COMPANY_DIR}.")
    out = []
    for path in sorted(COMPANY_DIR.glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if only_id and record.get("id") != only_id:
            continue
        out.append((path, record))
    if only_id and not out:
        sys.exit(f"No company with id {only_id!r}.")
    return out


def cmd_propose(args: argparse.Namespace) -> int:
    proposals = {}
    for path, record in load_companies(args.id):
        target = record.get("search_name") or record["name"]
        queries = [target]
        words = [t for t in _tokens(target) if len(t) > 3]
        if words and words[0] != _norm(target):
            queries.append(words[0])

        scored = []
        seen = set()
        for query in queries:
            for candidate in search(query):
                org_nr = candidate.get("organisasjonsnummer")
                if not org_nr or org_nr in seen:
                    continue
                seen.add(org_nr)
                scored.append((score(target, candidate), candidate))
        scored.sort(key=lambda pair: (-pair[0], -(pair[1].get("antallAnsatte") or 0)))

        print(f"\n=== {record['id']}  (search: {target})  [{record.get('category')}]")
        if not scored:
            print("    no registry match -- likely no Norwegian entity (foreign vendor)")
        for value, candidate in scored[:3]:
            print(f"    {value:0.2f}  {describe(candidate)}")
        proposals[record["id"]] = [
            {"score": round(value, 3), **candidate} for value, candidate in scored[:5]
        ]

    PROPOSAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROPOSAL_PATH.write_text(json.dumps(proposals, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nFull proposals written to {PROPOSAL_PATH.relative_to(ROOT)}")
    return 0


def registry_fields(candidate: dict, existing: dict | None = None) -> dict:
    """Map a registry entry onto our schema. Only ever verified facts."""
    address = candidate.get("forretningsadresse") or candidate.get("postadresse") or {}
    fields: dict = {
        "legal_name": candidate.get("navn"),
        "org_nr": candidate.get("organisasjonsnummer"),
    }
    homepage = candidate.get("hjemmeside")
    # The registry's homepage field goes stale (it still lists aztek.no for the
    # entity that now trades as Accelerate at Iver), so a website we already
    # resolved is never overwritten -- we only report the disagreement.
    known = (existing or {}).get("website")
    if homepage and not known:
        fields["website"] = homepage if homepage.startswith("http") else f"https://{homepage}"
    elif homepage and known:
        normalised = homepage if homepage.startswith("http") else f"https://{homepage}"
        if normalised.rstrip("/") != known.rstrip("/"):
            print(f"     registry homepage differs: {normalised} (keeping {known})")
    if address.get("landkode") == "NO":
        city = address.get("poststed") or address.get("kommune")
        if city:
            fields["office_cities"] = sorted({city.title()})
    employees = candidate.get("antallAnsatte")
    if employees is not None:
        fields["brreg_employees"] = employees
    as_of = candidate.get("registreringsdatoAntallAnsatteEnhetsregisteret") or candidate.get(
        "registreringsdatoAntallAnsatteNAVAaregisteret"
    )
    if as_of:
        fields["brreg_employees_as_of"] = as_of
    if candidate.get("stiftelsesdato"):
        fields["founded"] = candidate["stiftelsesdato"]
    former = [h.get("navn") for h in candidate.get("historiskeNavn") or [] if h.get("navn")]
    if former:
        fields["former_names"] = former
    return fields


def cmd_refresh(args: argparse.Namespace) -> int:
    updates = 0
    for path, record in load_companies(args.id):
        org_nr = record.get("org_nr")
        if not org_nr:
            if not args.quiet:
                print(f"skip {record['id']}: no org_nr pinned yet")
            continue
        try:
            candidate = _fetch(f"{API}/{org_nr}", f"entity-{org_nr}")
        except urllib.error.HTTPError as exc:
            print(f"ERROR {record['id']}: registry returned {exc.code} for org.nr {org_nr}")
            continue

        fields = registry_fields(candidate, record)
        changed = {k: v for k, v in fields.items() if record.get(k) != v}
        source_url = f"https://data.brreg.no/enhetsregisteret/api/enheter/{org_nr}"
        sources = [s for s in record.get("sources", []) if s.get("type") != "registry"]
        sources.append({"url": source_url, "type": "registry", "checked": args.checked})
        fields["sources"] = sources

        if not changed:
            if not args.quiet:
                print(f"ok   {record['id']}: registry unchanged")
            continue

        updates += 1
        print(f"DIFF {record['id']}: " + ", ".join(f"{k}={v}" for k, v in changed.items() if k != "sources"))
        if args.write:
            record.update(fields)
            path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if updates and not args.write:
        print(f"\n{updates} record(s) differ. Re-run with --write to apply.")
    elif args.write:
        print(f"\n{updates} record(s) written.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("mode", choices=["propose", "refresh"])
    parser.add_argument("--id", help="limit to one company id")
    parser.add_argument("--all", action="store_true", help="process every company")
    parser.add_argument("--write", action="store_true", help="apply refresh changes to disk")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument(
        "--checked",
        default=time.strftime("%Y-%m-%d"),
        help="value to record as the source check date (default: today)",
    )
    args = parser.parse_args()
    if not args.id and not args.all:
        parser.error("pass --all or --id <id>")
    os.makedirs(CACHE_DIR, exist_ok=True)
    return cmd_propose(args) if args.mode == "propose" else cmd_refresh(args)


if __name__ == "__main__":
    raise SystemExit(main())
