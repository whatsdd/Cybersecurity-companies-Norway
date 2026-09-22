#!/usr/bin/env python3
"""Fetch company pages and surface candidate claims for HUMAN review.

This tool deliberately does not write to the dataset. It downloads each
company's homepage, follows a few likely "about / team / services" links, and
prints the sentences that mention headcount, testers, certifications or a
Norwegian address. A maintainer then decides what is true and records the exact
source URL in the company's JSON file.

The reason for the human gate is visible in the data: companies describe
themselves in incompatible ways ("170+ ansatte", "our 12 pentesters", "a team of
specialists"), and several of the entries in the original list have no
verifiable web presence at all. A scraper that "extracted the number" would
invent facts, which is the one thing this dataset must never do.

Usage:
    python3 scripts/fetch_signals.py --all
    python3 scripts/fetch_signals.py --id river-security
    python3 scripts/fetch_signals.py --all --category norwegian
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMPANY_DIR = ROOT / "data" / "companies"
CACHE_DIR = ROOT / ".build-tmp" / "site-cache"
REPORT_PATH = ROOT / ".build-tmp" / "site-signals.json"

USER_AGENT = (
    "Mozilla/5.0 (compatible; Cybersecurity-companies-Norway/1.0; "
    "+https://github.com/; community directory, contact via repository issues)"
)

# Sentences worth a human's attention. Wider than the pentest edition on
# purpose: a SOC, an OT team and a GRC house describe themselves in different
# words, and a keyword list tuned for offensive work finds none of them.
KEYWORDS = (
    "ansatte", "medarbeider", "employees", "employee", "headcount", "staff",
    "pentester", "pentest", "penetrasjonstest", "sikkerhetstester", "tester",
    "testers", "etisk hacking", "red team", "specialist", "spesialist",
    "ekspert", "expert", "konsulent", "consultant", "team",
    "soc", "mdr", "overvåkning", "monitoring", "incident response",
    "beredskap", "hendelseshåndtering", "gis", "forensics", "etterforskning",
    "ciso", "grc", "nis2", "dora", "gdpr", "personvern", "compliance",
    "iso 27001", "iso/iec 27001", "crest", "osstmm", "offensive security",
    "oscp", "owasp", "nsm", "godkjent", "certif", "partner",
)

# Any of these in a snippet usually means we found a real Norwegian presence.
NORWAY_HINTS = (
    "oslo", "bergen", "trondheim", "stavanger", "tromsø", "tromso", "kristiansand",
    "grimstad", "sandnes", "fornebu", "lysaher", "høvik", "gjerdrum", "drammen",
    "norge", "norway", "postboks", "org.nr", "org nr", "organisasjonsnummer",
    "n0", "\nno",
)

ABOUT_HINTS = (
    "about", "om-oss", "om_oss", "omoss", "team", "medarbeidere", "ansatte",
    "folka", "people", "who-we-are", "company", "selskapet", "expertise",
    "ekspertise", "services", "tjenester", "kontakt", "contact", "careers",
    "karriere", "jobs", "offensive", "pentest", "sikkerhetstesting",
    "soc", "mdr", "tjenester", "capabilities", "kompetanse", "ekspertise",
)


class _Extractor(HTMLParser):
    """Collect visible text and links, skipping script/style/noscript bodies."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.chunks: list[str] = []
        self.links: list[tuple[str, str]] = []
        self._skip = 0
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "svg", "template"}:
            self._skip += 1
        elif tag == "a":
            self._href = dict(attrs).get("href")
            self._text = []
        elif tag in {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "tr", "section", "footer"}:
            self.chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg", "template"} and self._skip:
            self._skip -= 1
        elif tag == "a" and self._href is not None:
            label = " ".join("".join(self._text).split())
            self.links.append((self._href, label))
            self._href, self._text = None, []

    def handle_data(self, data: str) -> None:
        if self._skip:
            return
        self.chunks.append(data)
        if self._href is not None:
            self._text.append(data)

    @property
    def text(self) -> str:
        raw = "".join(self.chunks)
        raw = re.sub(r"[ \t\u00a0]+", " ", raw)
        raw = re.sub(r"\n\s*\n+", "\n", raw)
        return raw.strip()


def fetch(url: str, cache_key: str) -> str | None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cached = CACHE_DIR / f"{cache_key}.html"
    if cached.exists():
        return cached.read_text(encoding="utf-8", errors="replace")
    # Norwegian URLs carry ae/oe/aa characters that must be percent-encoded
    # before they can go on the wire.
    url = urllib.parse.quote(url, safe=":/?&=#%+~@[]!$'()*,;")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "nb-NO,nb;q=0.9,en;q=0.8"})
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            body = response.read().decode(charset, errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
        return None
    cached.write_text(body, encoding="utf-8")
    time.sleep(0.25)
    return body


def snippets(text: str, terms: tuple[str, ...], limit: int, width: int = 300) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for line in text.split("\n"):
        line = line.strip()
        if not line or len(line) < 12:
            continue
        low = line.lower()
        if not any(term in low for term in terms):
            continue
        if len(line) > width:
            for term in terms:
                at = low.find(term)
                if at >= 0:
                    start = max(0, at - width // 3)
                    line = line[start : start + width]
                    break
        key = line[:90].lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(line)
        if len(out) >= limit:
            break
    return out


def candidate_pages(base: str, links: list[tuple[str, str]], limit: int = 4) -> list[str]:
    host = urllib.parse.urlsplit(base).netloc.replace("www.", "")
    scored: list[tuple[int, str]] = []
    seen = {base.rstrip("/")}
    for href, label in links:
        if not href or href.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue
        absolute = urllib.parse.urljoin(base, href)
        parts = urllib.parse.urlsplit(absolute)
        if parts.scheme not in {"http", "https"}:
            continue
        if host not in parts.netloc.replace("www.", ""):
            continue
        if parts.path.lower().endswith((".pdf", ".jpg", ".png", ".zip", ".svg", ".webp", ".mp4")):
            continue
        clean = f"{parts.scheme}://{parts.netloc}{parts.path}".rstrip("/")
        if clean in seen:
            continue
        blob = f"{parts.path} {label}".lower()
        rank = sum(1 for hint in ABOUT_HINTS if hint in blob)
        if rank:
            scored.append((rank, clean))
    scored.sort(key=lambda pair: -pair[0])
    picked: list[str] = []
    for _, url in scored:
        if url not in picked:
            picked.append(url)
        if len(picked) >= limit:
            break
    return picked


def load(only_id: str | None, category: str | None) -> list[tuple[Path, dict]]:
    out = []
    for path in sorted(COMPANY_DIR.glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if only_id and record.get("id") != only_id:
            continue
        if category and record.get("category") != category:
            continue
        out.append((path, record))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--id")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--category")
    parser.add_argument("--max-snippets", type=int, default=6)
    args = parser.parse_args()
    if not args.id and not args.all and not args.category:
        parser.error("pass --all, --id <id> or --category <name>")

    report: dict[str, dict] = {}
    for path, record in load(args.id, args.category):
        website = record.get("website")
        if not website:
            report[record["id"]] = {"website": None, "reachable": False, "pages": [], "claims": [], "contacts": []}
            print(f"\n=== {record['id']}: no website on record")
            continue
        try:
            body = fetch(website, record["id"] + "-home")
        except (urllib.error.URLError, OSError, ValueError) as exc:
            print(f"\n=== {record['id']}: FETCH ERROR {type(exc).__name__} {website}")
            report[record["id"]] = {"website": website, "reachable": False, "pages": [], "claims": [], "contacts": []}
            continue
        if not body:
            report[record["id"]] = {"website": website, "reachable": False, "pages": [], "claims": [], "contacts": []}
            print(f"\n=== {record['id']}: UNREACHABLE {website}")
            continue

        extractor = _Extractor()
        extractor.feed(body)
        text = extractor.text
        pages = [website] + candidate_pages(website, extractor.links)
        claims = snippets(text, KEYWORDS, args.max_snippets)
        contacts = snippets(text, NORWAY_HINTS, 4, width=160)

        for page in pages[1:]:
            try:
                page_body = fetch(page, record["id"] + "-" + re.sub(r"[^a-z0-9]+", "-", page.lower())[-40:])
            except (urllib.error.URLError, OSError, ValueError):
                continue
            if not page_body:
                continue
            sub = _Extractor()
            sub.feed(page_body)
            sub_text = sub.text
            claims.extend(snippets(sub_text, KEYWORDS, 4))
            contacts.extend(snippets(sub_text, NORWAY_HINTS, 2, width=160))

        report[record["id"]] = {
            "website": website,
            "reachable": True,
            "pages": pages,
            "claims": claims,
            "contacts": contacts,
        }
        print(f"\n=== {record['id']}  {website}  (pages: {len(pages)})")
        for claim in claims:
            print(f"    - {claim}")
        for contact in contacts[:2]:
            print(f"    @ {contact}")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nReport written to {REPORT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
