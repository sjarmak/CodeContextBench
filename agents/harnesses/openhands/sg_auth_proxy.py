#!/usr/bin/env python3
"""HTTP auth proxy for Sourcegraph MCP.

OpenHands sends 'Authorization: Bearer <token>', but Sourcegraph requires
'Authorization: token <token>'. This proxy listens on localhost and forwards
requests to Sourcegraph with the correct auth header.

Runs as a background daemon inside the container. OpenHands SHTTP config
points at http://localhost:<port> with no api_key; this proxy adds auth.

Usage:
    SG_MCP_URL=https://sourcegraph.sourcegraph.com/.api/mcp \
    SG_MCP_TOKEN=sgp_... \
    python3 sg_auth_proxy.py [--port 18973]

Writes the actual listen port to /tmp/sg_proxy_port on startup.
"""

import argparse
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import urllib.error

SG_URL = os.environ.get("SG_MCP_URL", "https://sourcegraph.sourcegraph.com/.api/mcp")
SG_TOKEN = os.environ.get("SG_MCP_TOKEN", "")


class ProxyHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else b""

        # Forward headers, replacing auth
        fwd_headers = {}
        for key, val in self.headers.items():
            lower = key.lower()
            if lower in ("host", "authorization", "s", "x-session-api-key"):
                continue
            fwd_headers[key] = val

        if SG_TOKEN:
            fwd_headers["Authorization"] = f"token {SG_TOKEN}"
        fwd_headers["Host"] = urllib.request.urlparse(SG_URL).netloc

        req = urllib.request.Request(
            SG_URL, data=body, headers=fwd_headers, method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                resp_body = resp.read()
                self.send_response(resp.status)
                for key, val in resp.getheaders():
                    if key.lower() not in ("transfer-encoding", "connection"):
                        self.send_header(key, val)
                self.end_headers()
                self.wfile.write(resp_body)
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            err_body = e.read() if e.fp else b""
            self.wfile.write(err_body)
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(str(e).encode())

    def do_GET(self):
        # MCP streamable HTTP also uses GET for SSE streams
        fwd_headers = {}
        for key, val in self.headers.items():
            lower = key.lower()
            if lower in ("host", "authorization", "s", "x-session-api-key"):
                continue
            fwd_headers[key] = val

        if SG_TOKEN:
            fwd_headers["Authorization"] = f"token {SG_TOKEN}"
        fwd_headers["Host"] = urllib.request.urlparse(SG_URL).netloc

        req = urllib.request.Request(SG_URL, headers=fwd_headers, method="GET")

        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                resp_body = resp.read()
                self.send_response(resp.status)
                for key, val in resp.getheaders():
                    if key.lower() not in ("transfer-encoding", "connection"):
                        self.send_header(key, val)
                self.end_headers()
                self.wfile.write(resp_body)
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.end_headers()
            self.wfile.write(e.read() if e.fp else b"")
        except Exception as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(str(e).encode())

    def log_message(self, format, *args):
        # Suppress request logging to keep container logs clean
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=18973)
    args = parser.parse_args()

    server = HTTPServer(("127.0.0.1", args.port), ProxyHandler)
    port = server.server_address[1]

    # Write port for config discovery
    with open("/tmp/sg_proxy_port", "w") as f:
        f.write(str(port))

    print(f"SG auth proxy listening on 127.0.0.1:{port} -> {SG_URL}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
