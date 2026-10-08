#!/usr/bin/env python3
"""Scan a web server access log for GET/POST-related red flags.

Reads Common/Combined Log Format lines (Apache, nginx, and this project's
demo_server.py) and reports suspicious requests. Standard library only.
"""
import argparse
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, unquote_plus, urlsplit

LINE_RE = re.compile(r'^(\S+) \S+ \S+ \[([^\]]+)\] "(\S+) (\S+)[^"]*" (\d{3}) (\S+)')

SENSITIVE_PARAMS = {"password", "passwd", "pwd", "pass", "token", "api_key",
                    "apikey", "secret", "ssn", "card", "cc"}

# (name, severity, regex applied to the URL-decoded request target)
RULES = [
    ("SQL injection pattern", "HIGH",
     re.compile(r"\b(or|and)\b\s+'?\w+'?\s*=\s*'?\w+|union\s+(all\s+)?select|;\s*drop\s+table|sleep\s*\(\s*\d+\s*\)", re.I)),
    ("Cross-site scripting (XSS) pattern", "HIGH",
     re.compile(r"<\s*script|on(error|load)\s*=|javascript:", re.I)),
    ("Path traversal pattern", "HIGH",
     re.compile(r"\.\./|\.\.\\|/etc/passwd|boot\.ini", re.I)),
    ("Command injection pattern", "HIGH",
     re.compile(r"[;|]\s*(cat|ls|whoami|wget|curl|nc)\b|\$\(", re.I)),
]

LOGIN_PATHS = {"/login", "/signin", "/wp-login.php"}
BRUTE_THRESHOLD, BRUTE_WINDOW = 5, 60   # failed logins within N seconds


def parse_time(ts):
    return datetime.strptime(ts, "%d/%b/%Y:%H:%M:%S %z")


def analyze(path):
    findings, failures = [], defaultdict(list)
    counts = {"GET": 0, "POST": 0, "other": 0}
    parsed = skipped = 0

    for n, line in enumerate(Path(path).read_text(errors="replace").splitlines(), 1):
        m = LINE_RE.match(line)
        if not m:
            skipped += 1
            continue
        parsed += 1
        ip, ts, method, target, status, _ = m.groups()
        counts[method if method in counts else "other"] += 1
        parts = urlsplit(target)

        # Sensitive data in the URL (GET query strings end up in logs and history)
        keys = {k.lower() for k in parse_qs(parts.query)}
        leaked = sorted(keys & SENSITIVE_PARAMS)
        if leaked:
            findings.append((n, ip, "HIGH", f"Sensitive data in URL: {', '.join(leaked)}", target))

        # Attack-pattern rules (decode twice to catch double encoding)
        decoded = unquote_plus(unquote_plus(target))
        for name, sev, rx in RULES:
            if rx.search(decoded):
                findings.append((n, ip, sev, name, target))

        # Failed logins for brute-force detection
        if parts.path in LOGIN_PATHS and status in ("401", "403"):
            failures[ip].append((n, parse_time(ts)))

    for ip, events in failures.items():
        events.sort(key=lambda e: e[1])
        for i in range(len(events) - BRUTE_THRESHOLD + 1):
            span = (events[i + BRUTE_THRESHOLD - 1][1] - events[i][1]).total_seconds()
            if span <= BRUTE_WINDOW:
                n = events[i + BRUTE_THRESHOLD - 1][0]
                findings.append((n, ip, "MEDIUM",
                                 f"Possible brute force: {len(events)} failed logins "
                                 f"({BRUTE_THRESHOLD}+ within {BRUTE_WINDOW}s)", "(multiple login requests)"))
                break

    return sorted(findings), counts, parsed, skipped


def main():
    ap = argparse.ArgumentParser(description="Scan an access log for suspicious requests.")
    ap.add_argument("logfile", nargs="?", default="access.log", help="log file (default: access.log)")
    args = ap.parse_args()
    if not Path(args.logfile).exists():
        raise SystemExit(f"Log file not found: {args.logfile}")

    findings, counts, parsed, skipped = analyze(args.logfile)
    print(f"Scanned {parsed} requests ({counts['GET']} GET, {counts['POST']} POST, "
          f"{counts['other']} other); skipped {skipped} unreadable lines.\n")

    if findings:
        print(f"{'Line':<5} {'Severity':<8} {'Source IP':<16} Finding")
        print("-" * 78)
        for n, ip, sev, name, req in findings:
            print(f"{n:<5} {sev:<8} {ip:<16} {name}")
            print(f"      request: {req[:90]}")
    else:
        print("No suspicious patterns found.")

    print(f"\nTotal findings: {len(findings)}")
    if counts["POST"]:
        print(f"\nVisibility note: {counts['POST']} POST request(s) in this log. "
              "Access logs do not record POST bodies, so any payload inside them "
              "cannot be inspected here (you would need WAF, application, or proxy logs).")


if __name__ == "__main__":
    main()
