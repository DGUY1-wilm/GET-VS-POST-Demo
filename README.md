# GET vs POST Demo

A hands-on project that shows how HTTP `GET` and `POST` requests differ in practice: where the data travels, what the server receives, and, from a defender's point of view, what actually ends up in web server logs. It has two parts:

1. **`demo_server.py`** is a small local web server with a fake login page that you can submit with either method, then inspect the raw request and the resulting access log.
2. **`log_analyzer.py`** is a log scanner that flags credentials in URLs, common injection patterns, and brute-force login attempts, and points out what it *cannot* see in POST traffic.

New to the command line? See [GETTING_STARTED.md](GETTING_STARTED.md) for a walkthrough written for non-technical users.

## What this project demonstrates

- The same login data sent two ways produces visibly different requests.
- `GET` parameters appear in the request line, so they are recorded in access logs, browser history, and proxy logs.
- `POST` parameters travel in the request body, which standard access logs do not record.
- Why that difference matters for both privacy (secrets in URLs) and detection (payloads hidden in POST bodies).
- How a few regular expressions and a counter can turn raw logs into triage-ready findings, and where those methods run out.

## Quick start

Requires Python 3.8+. There are no third-party dependencies.

```bash
git clone https://github.com/<DGUY1-wilm>/get-vs-post-demo.git
cd get-vs-post-demo
python demo_server.py            # then open http://127.0.0.1:8000
python log_analyzer.py access.log
python log_analyzer.py sample_access.log
```

On macOS/Linux use `python3`. To use a different port: `python demo_server.py --port 8080`.

## Background: GET vs POST

| | GET | POST |
|---|---|---|
| **Intended purpose** | Retrieve a resource | Submit data for processing, often changing server state |
| **Where parameters go** | Query string in the URL (`/login?user=a&pw=b`) | Request body |
| **HTTP semantics** | Safe and idempotent (RFC 9110) | Neither safe nor idempotent |
| **Recorded in access logs** | Yes, the full request line including the query string | The request line only; the body is not recorded by default |
| **Browser history / bookmarks** | URL (with parameters) is stored | Body is not stored |
| **Caching** | Responses can be cached | Responses generally are not |
| **Refresh / back button** | Re-sends silently | Browser warns before re-submitting |
| **Size limits** | Practical URL length limits in browsers and servers (commonly a few thousand characters) | Much larger bodies allowed (server-configured) |

### What each looks like on the wire

```http
GET /login?username=demo&password=demo123 HTTP/1.1
Host: 127.0.0.1:8000
User-Agent: ...
```

```http
POST /login HTTP/1.1
Host: 127.0.0.1:8000
Content-Type: application/x-www-form-urlencoded
Content-Length: 30

username=demo&password=demo123
```

The data is identical. Only its location differs: in the first request it is part of the request line, in the second it follows the headers.

### Common misconception: "POST is secure"

POST is not encrypted and does not protect data on its own. Over plain HTTP, a POST body is readable by anyone on the network path, exactly like a URL. **HTTPS (TLS) is what protects data in transit**, for both methods. The real differences are about where the data gets *stored* afterward: sensitive values in a GET URL leak into server logs, browser history, bookmarks, analytics tools, and sometimes `Referer` headers, even when the connection itself was encrypted. This is tracked as [CWE-598: Use of GET Request Method With Sensitive Query Strings](https://cwe.mitre.org/data/definitions/598.html).

This demo runs over plain HTTP on localhost, so nothing is encrypted in either case.

## How the demo server works

`demo_server.py` uses Python's standard-library `http.server`. It binds to `127.0.0.1` only, so it is unreachable from other machines.

### Routes

| Route | Method | Behavior |
|---|---|---|
| `/` | GET | Page with two identical forms: one `method="get"`, one `method="post"` |
| `/login` | GET, POST | Reads `username` and `password` from the query string (GET) or body (POST), checks them against a fake account (`demo` / `demo123`), and shows a result page |
| `/log` | GET | Displays the current `access.log` in the browser. Viewing the log is itself not logged |
| `/favicon.ico` | any | Returns `204 No Content` and is not logged (keeps browser noise out of the log) |
| anything else | any | `404` |

`/login` returns `200` for the correct fake credentials and `401` for anything else, which gives the analyzer realistic failed-login events.

### Request handling

```
browser ──► do_GET / do_POST ──► handle_request ──► route ──► reply ──► write_log
                │
                └─ POST only: read up to Content-Length bytes (capped at 10,000) as the body
```

### What the result page shows

For every `/login` request the page displays two things side by side:

- **The raw request the server received:** the request line, the headers, and, for POST, the body. This is *reconstructed* from what Python's HTTP parser exposes (`requestline` and the parsed headers), so header order and casing reflect the parser, not a packet capture.
- **What the access log will record:** just the request line. For a GET it contains the password; for a POST it does not.

### Access log format

Each request is appended to `access.log` (created next to the script) in a Common Log Format style:

```
127.0.0.1 - - [08/Oct/2026:00:22:55 +0000] "GET /login?username=demo&password=demo123 HTTP/1.1" 200 1298
127.0.0.1 - - [08/Oct/2026:00:22:55 +0000] "POST /login HTTP/1.1" 401 1349
```

Fields: client IP, `-` (identd, unused), `-` (authenticated user, unused), timestamp, request line, status code, response size in bytes. This is the same shape Apache and nginx produce by default, so the analyzer works on real logs from those servers too.

The terminal running the server additionally prints each POST body, to make the point that the server received data the log did not keep.

## How the log analyzer works

`log_analyzer.py` reads a log file line by line and applies four kinds of checks.

### 1. Parsing
Each line is matched against a Common Log Format regex to extract IP, timestamp, method, request target, and status. Lines that don't match are counted and skipped rather than crashing the scan.

### 2. Detections

| Detection | How it works | Severity | CWE | ATT&CK |
|---|---|---|---|---|
| Sensitive data in URL | Parses the query string and checks parameter names against a list (`password`, `passwd`, `pwd`, `pass`, `token`, `api_key`, `apikey`, `secret`, `ssn`, `card`, `cc`) | HIGH | CWE-598 | n/a |
| SQL injection pattern | Regex for tautologies (`' OR '1'='1`), `UNION SELECT`, `; DROP TABLE`, `SLEEP(n)` | HIGH | CWE-89 | T1190 |
| XSS pattern | Regex for `<script`, `onerror=` / `onload=`, `javascript:` | HIGH | CWE-79 | n/a |
| Path traversal pattern | Regex for `../`, `..\`, `/etc/passwd`, `boot.ini` | HIGH | CWE-22 | T1190 |
| Command injection pattern | Regex for `;` or `|` followed by common commands, and `$(` | HIGH | CWE-78 | T1190 |
| Brute force | 5 or more failed logins (`401`/`403` on `/login`, `/signin`, `/wp-login.php`) from one IP within 60 seconds | MEDIUM | CWE-307 | T1110 |

The pattern checks run on the request target after URL-decoding it **twice**, so single- and double-encoded payloads (`%27`, `%2527`) are both caught.

### 3. Brute-force logic
Failed logins are grouped by source IP and sorted by time. A sliding window checks whether any 5 consecutive failures fall within 60 seconds. One finding is reported per IP. The thresholds are constants at the top of the file.

### 4. Visibility note
If the log contains POST requests, the report ends with a reminder that their bodies are not in the log and cannot be inspected from it. This is the central defender takeaway of the project.

### Example output (`sample_access.log`)

`sample_access.log` is a fabricated log. Its IP addresses come from the reserved documentation ranges (`192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24`).

```
Scanned 21 requests (13 GET, 8 POST, 0 other); skipped 0 unreadable lines.

Line  Severity Source IP        Finding
------------------------------------------------------------------------------
3     HIGH     198.51.100.10    Sensitive data in URL: password
      request: /login?username=demo&password=demo123
11    MEDIUM   203.0.113.45     Possible brute force: 7 failed logins (5+ within 60s)
      request: (multiple login requests)
14    HIGH     203.0.113.45     SQL injection pattern
      request: /products?id=1'%20OR%20'1'='1
15    HIGH     203.0.113.45     SQL injection pattern
      request: /search?q=1%20UNION%20SELECT%20username,password%20FROM%20users
16    HIGH     198.51.100.99    Cross-site scripting (XSS) pattern
      request: /search?q=%3Cscript%3Ealert(1)%3C/script%3E
18    HIGH     203.0.113.200    Path traversal pattern
      request: /download?file=../../../../etc/passwd
19    HIGH     203.0.113.200    Command injection pattern
      request: /ping?host=8.8.8.8;cat%20/etc/shadow
20    HIGH     192.0.2.31       Sensitive data in URL: token
      request: /api/data?token=abc123secret

Total findings: 8

Visibility note: 8 POST request(s) in this log. Access logs do not record POST bodies, so any payload inside them cannot be inspected here (you would need WAF, application, or proxy logs).
```

## Defender takeaways

- **Access logs show GET parameters but not POST bodies.** An attacker who sends a payload by POST leaves only `POST /endpoint` in the standard log. Detecting that traffic needs a web application firewall, application-level logging, or a proxy that records bodies.
- **Secrets in URLs persist.** Anything in a query string is likely stored in server logs, browser history, and possibly third-party tools. Finding credentials or tokens in logs is both an exposure and a reason to rotate them.
- **Status codes and rates carry signal.** A burst of `401`s from one IP against a login path is detectable without ever seeing a password.
- **Pattern matching is a starting point, not a verdict.** Findings are leads for an analyst to confirm. Check the response code and size to see whether an attempt succeeded.

## Project structure

```
get-vs-post-demo/
├── demo_server.py       # local demo web server
├── log_analyzer.py      # access log scanner
├── sample_access.log    # fabricated log with benign and suspicious traffic
├── .gitignore           # keeps your own access.log out of Git
├── README.md
└── GETTING_STARTED.md   # beginner tutorial
```

## Security notes

- **Use fake credentials only.** The server writes GET passwords into `access.log` in plain text and prints POST bodies to the terminal. The result page also echoes the raw request, password included. This is deliberate for teaching and is exactly what a real application should never do.
- **The server binds to `127.0.0.1` only.** Don't change `HOST` to `0.0.0.0` or run it on a shared network.
- **No real authentication, sessions, or HTTPS.** The "login" is a fake string comparison.
- `access.log` is git-ignored so your test requests aren't published.

## Limitations

- `http.server` is single-threaded and not meant for production use.
- The raw request shown on the result page is reconstructed, not captured from the network. For a true wire-level view, pair the demo with browser developer tools (Network tab) or Wireshark on the loopback interface.
- POST bodies are read up to 10,000 bytes; larger bodies are truncated.
- The analyzer uses regex heuristics. It will miss obfuscated payloads (unusual encodings, case or comment tricks) and can flag benign requests (false positives).
- Brute-force detection relies on `401`/`403` status codes. Applications that return `200` for a failed login won't trigger it.
- Pattern checks look at the request target only, never at POST bodies or headers.
- Only Common/Combined Log Format timestamps and fields are supported.

## Ideas for extension

- Add a third mode that sends the password over HTTPS (self-signed certificate) and compare it in a packet capture
- Capture the demo traffic with Wireshark and add annotated screenshots
- Extend the analyzer to read nginx/Apache combined logs with user-agent and referrer fields
- Add output to CSV/JSON and a severity filter
- Add a "successful login after many failures" detection
- Write unit tests for each detection rule using sample log lines

## License

Licensed under the MIT License. See [LICENSE](LICENSE) for details.
