"""Optional localhost-only fault proxy for the homework 5 browser demo.

Forward to the synthetic fixture on port 8015. A control JSON file can set
{"fail": true}, {"delay_query": "ЗАВТРАК"} or {"delay_query": "ЗАВТРАК", "fail_delayed": true}.
This script never changes the app or its database; it is test infrastructure.
"""

import argparse
import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit
from urllib.request import urlopen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8016)
    parser.add_argument("--upstream-port", type=int, default=8015)
    parser.add_argument("--control", type=Path, default=Path("/tmp/itmo-hw5-proxy.json"))
    args = parser.parse_args()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            control = json.loads(args.control.read_text()) if args.control.exists() else {}
            url = urlsplit(self.path)
            query = parse_qs(url.query).get("q", [""])[0]
            listing = url.path == "/api/collections"
            delayed = listing and query and query == control.get("delay_query")
            if delayed:
                time.sleep(4)
            if listing and (control.get("fail") or delayed and control.get("fail_delayed")):
                status, content, content_type = 503, b'{"detail":"storage unavailable"}', "application/json"
            else:
                try:
                    response = urlopen(f"http://127.0.0.1:{args.upstream_port}{self.path}", timeout=10)
                except HTTPError as error:
                    response = error
                with response:
                    status, content, content_type = response.status, response.read(), response.headers["Content-Type"]
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Browser fault proxy: http://127.0.0.1:{args.port}; control: {args.control}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
