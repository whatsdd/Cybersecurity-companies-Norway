#!/usr/bin/env python3
"""Check every source URL in the dataset. Standard library only.

Link rot is how a verified directory quietly becomes wrong, so this runs weekly
and on every pull request.

The important design decision: a 403 or 429 from a company site is **not** a
broken link. Several perfectly healthy vendors (and the registry's own
documentation pages) refuse automated requests. Those are reported as
"blocked" and do not fail the build, because turning a bot filter into a red
build trains people to ignore the check. Only 404/410, dead DNS and connection
failures count as broken.

Usage:
    python3 scripts/linkcheck.py
    python3 scripts/linkcheck.py --only-broken
    python3 scripts/linkcheck.py --json report.json
"""

from __future__ import annotations

import argparse
import json
import socket
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMPANY_DIR = ROOT / "data" / "companies"

USER_AGENT = (
    "Mozilla/5.0 (compatible; Cybersecurity-companies-Norway-linkcheck/1.0; "
    "+https://github.com/whatsdd/Cybersecurity-companies-Norway)"
)
TIMEOUT = 25

# Hosts that reliably answer bots are still worth marking, so a maintainer can
# check them by hand rather than wondering whether the check is lying.
BLOCKED_CODES = {401, 403, 405, 406, 429, 503}


def probe(url: str) -> tuple[str, str, str]:
    """Return (url, status, detail) where status is ok|blocked|broken|warning."""
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "*/*"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return url, "ok", f"HTTP {response.status}"
    except urllib.error.HTTPError as exc:
        if exc.code in BLOCKED_CODES:
            return url, "blocked", f"HTTP {exc.code} (bots refused; verify by hand)"
        if exc.code in {404, 410}:
            return url, "broken", f"HTTP {exc.code}"
        if 500 <= exc.code < 600:
            return url, "warning", f"HTTP {exc.code} (server error, may be transient)"
        return url, "warning", f"HTTP {exc.code}"
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", exc)
        if isinstance(reason, socket.gaierror):
            return url, "broken", f"DNS failure: {reason}"
        return url, "broken", f"connection failed: {reason}"
    except (TimeoutError, socket.timeout):
        return url, "warning", "timed out"
    except Exception as exc:  # noqa: BLE001
        return url, "warning", f"{type(exc).__name__}: {exc}"


def collect() -> list[tuple[str, str]]:
    """Every unique source URL with the companies that rely on it."""
    seen: dict[str, list[str]] = {}
    for path in sorted(COMPANY_DIR.glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        urls = [s.get("url") for s in record.get("sources", []) if s.get("url")]
        if record.get("website"):
            urls.append(record["website"])
        for field in ("employees_source", "security_staff_source", "delivery_source"):
            if record.get(field):
                urls.append(record[field])
        for url in urls:
            if url:
                seen.setdefault(url, []).append(record["id"])
    return sorted(seen.items())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--only-broken", action="store_true", help="print only broken links")
    parser.add_argument("--json", help="also write a JSON report to this path")
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    urls = collect()
    if not urls:
        sys.exit("no source URLs found")

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(lambda item: probe(item[0]) + (item[1],), urls))

    buckets: dict[str, list[tuple[str, str, list[str]]]] = {"broken": [], "blocked": [], "warning": [], "ok": []}
    for url, status, detail, owners in results:
        buckets[status].append((url, detail, owners))

    if not args.only_broken:
        for status in ("broken", "blocked", "warning"):
            for url, detail, owners in buckets[status]:
                print(f"{status.upper():8} {url} - {detail} (used by: {', '.join(sorted(set(owners)))})")
        print()

    print(f"checked {len(urls)} unique source URLs: "
          f"{len(buckets['ok'])} ok, {len(buckets['blocked'])} blocked by bot filters, "
          f"{len(buckets['warning'])} warnings, {len(buckets['broken'])} broken")

    if buckets["broken"]:
        print("\nBroken links need fixing. Replace the source or restore the claim:")
        for url, detail, owners in buckets["broken"]:
            print(f"  - {url} ({detail}) used by {', '.join(sorted(set(owners)))}")

    if args.json:
        Path(args.json).write_text(
            json.dumps(
                {status: [{"url": u, "detail": d, "companies": sorted(set(o))} for u, d, o in items]
                 for status, items in buckets.items()},
                indent=2,
                ensure_ascii=False,
            ) + "\n",
            encoding="utf-8",
        )

    return 1 if buckets["broken"] else 0


if __name__ == "__main__":
    sys.exit(main())
