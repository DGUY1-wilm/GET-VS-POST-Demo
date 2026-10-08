#!/usr/bin/env python3
"""GET vs POST demo: a tiny local web server that shows how each method sends
data and what ends up in the server's access log.

Runs only on 127.0.0.1 (your own computer). Use FAKE credentials only.
Standard library only, so there is nothing to install.
"""
import argparse
import html
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

HOST = "127.0.0.1"
LOG_FILE = Path(__file__).with_name("access.log")
MAX_BODY = 10_000
DEMO_USER, DEMO_PASS = "demo", "demo123"

CSS = """
body{font-family:system-ui,sans-serif;max-width:880px;margin:2rem auto;padding:0 1rem;line-height:1.5;color:#1b1f23}
.row{display:flex;gap:1.5rem;flex-wrap:wrap}
form{flex:1;min-width:260px;border:1px solid #d0d7de;border-radius:8px;padding:0 1rem 1rem}
input{display:block;margin:.4rem 0 .8rem;padding:.4rem;width:95%}
button{padding:.5rem 1.2rem;cursor:pointer}
pre{background:#f6f8fa;border:1px solid #d0d7de;border-radius:6px;padding:.8rem;overflow-x:auto}
.warn{background:#fff8c5;border:1px solid #d4a72c;border-radius:6px;padding:.6rem .9rem}
.ok{color:#1a7f37}.bad{color:#cf222e}
"""

INDEX = """
<h1>GET vs POST demo</h1>
<p class="warn">Use <b>fake</b> credentials only. Try <code>demo</code> / <code>demo123</code>.
This server only runs on your own computer.</p>
<div class="row">
  <form method="get" action="/login">
    <h2>Form A: GET</h2>
    <label>Username<input name="username" autocomplete="off"></label>
    <label>Password<input name="password" type="password" autocomplete="off"></label>
    <button type="submit">Log in with GET</button>
  </form>
  <form method="post" action="/login">
    <h2>Form B: POST</h2>
    <label>Username<input name="username" autocomplete="off"></label>
    <label>Password<input name="password" type="password" autocomplete="off"></label>
    <button type="submit">Log in with POST</button>
  </form>
</div>
<p>After submitting each form, look at your browser's address bar, then open
<a href="/log">the server's access log</a>.</p>
"""


def page(title, body):
    return (f"<!doctype html><html><head><meta charset='utf-8'><title>{html.escape(title)}</title>"
            f"<style>{CSS}</style></head><body>{body}</body></html>")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # we write our own access log instead of the default one

    # ---- helpers ----
    def reply(self, status, content):
        data = content.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
        self.status, self.size = status, len(data)

    def raw_request(self, body):
        lines = [self.requestline] + [f"{k}: {v}" for k, v in self.headers.items()]
        text = "\n".join(lines) + "\n"
        return text + ("\n" + body if body else "")

    def write_log(self, body):
        ts = datetime.now().astimezone().strftime("%d/%b/%Y:%H:%M:%S %z")
        line = f'{self.client_address[0]} - - [{ts}] "{self.requestline}" {self.status} {self.size}'
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
        print(f"  access log : {line}")
        if body:
            print(f"  POST body  : {body}   <-- the server saw this, the access log did not")
        print()

    # ---- routes ----
    def login(self, parts, body):
        method = self.command
        params = parse_qs(parts.query if method == "GET" else body)
        user = params.get("username", [""])[0]
        pw = params.get("password", [""])[0]
        ok = (user, pw) == (DEMO_USER, DEMO_PASS)
        where = ("in the <b>URL</b> (look at your address bar now)" if method == "GET"
                 else "in the <b>request body</b> (the address bar just says /login)")
        result = ('<span class="ok">Login OK (fake)</span>' if ok
                  else '<span class="bad">Login failed (fake)</span>')
        body_html = f"""
<h1>You sent a {method} request</h1>
<p>{result}. Your username and password traveled {where}.</p>
<h2>The raw request the server received</h2>
<pre>{html.escape(self.raw_request(body))}</pre>
<h2>What the access log will record</h2>
<pre>{html.escape(self.requestline)}</pre>
<p>{"Notice the password is right there in the logged line." if method == "GET"
   else "Notice the password is <b>not</b> in the logged line."}</p>
<p><a href="/">Back to the forms</a> &middot; <a href="/log">View the access log</a></p>
"""
        self.reply(200 if ok else 401, page(f"{method} result", body_html))

    def show_log(self):
        try:
            text = LOG_FILE.read_text(encoding="utf-8") or "(empty)"
        except FileNotFoundError:
            text = "(no requests logged yet)"
        self.reply(200, page("Access log", f"""
<h1>Server access log</h1>
<p>This is what a typical web server writes down. Compare the GET and POST lines.</p>
<pre>{html.escape(text)}</pre>
<p><a href="/">Back to the forms</a> &middot; <a href="/log">Refresh</a></p>"""))

    def handle_request(self, body=""):
        self.status, self.size = 0, 0
        parts = urlsplit(self.path)
        if parts.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return
        if parts.path == "/log" and self.command == "GET":
            self.show_log()
            return  # viewing the log is not logged
        if parts.path == "/" and self.command == "GET":
            self.reply(200, page("GET vs POST demo", INDEX))
        elif parts.path == "/login" and self.command in ("GET", "POST"):
            self.login(parts, body)
        else:
            self.reply(404, page("Not found", "<h1>404 Not found</h1><p><a href='/'>Back</a></p>"))
        self.write_log(body)

    def do_GET(self):
        self.handle_request()

    def do_POST(self):
        try:
            n = int(self.headers.get("Content-Length", 0))
        except ValueError:
            n = 0
        body = self.rfile.read(max(0, min(n, MAX_BODY))).decode("utf-8", "replace")
        self.handle_request(body)


def main():
    ap = argparse.ArgumentParser(description="GET vs POST demo server")
    ap.add_argument("--port", type=int, default=8000, help="port to use (default 8000)")
    args = ap.parse_args()
    try:
        server = HTTPServer((HOST, args.port), Handler)
    except OSError as e:
        raise SystemExit(f"Could not start on port {args.port}: {e}\nTry another: python demo_server.py --port 8080")
    print(f"Demo running at http://{HOST}:{args.port}  (press Ctrl+C to stop)\n"
          f"Access log: {LOG_FILE}\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
