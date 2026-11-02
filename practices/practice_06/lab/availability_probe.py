"""Reproduce the two review findings only against disposable loopback servers."""

import argparse
import hashlib
import json
import socket
import threading
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen
from unittest.mock import patch

import service
from attacks import LocalShop


def unicode_probe():
    with LocalShop() as local:
        auth = local.login()
        result = {"post_status": local.call("POST", "/reviews", {"product": "chair", "text": "\ud800"}, auth)[0]}
        for name, path in (("reviews", "/reviews/view"), ("assistant", "/assistant/context?order_id=1")):
            try:
                status, _ = local.call("GET", path, auth=auth)
                result[name] = {"status": status}
            except (OSError, ValueError) as error:
                result[name] = {"error": type(error).__name__}
        result["stored_reviews"] = len(local.shop.reviews)
        return result


def health_status(address):
    try:
        response = urlopen(f"http://127.0.0.1:{address[1]}/health", timeout=1)
    except HTTPError as error:
        response = error
    with response:
        response.read()
        return response.status


def trickle_probe(stage, deadline=0.4, interval=0.08, duration=1.2):
    """Send often enough to avoid inactivity timeout, retaining the socket open.

    The deadline is configured, not the clock mocked. Before the fix the absent
    setting is harmlessly installed by patch(create=True) and remains unused.
    """
    prefixes = {
        "request_line": b"GET /health ",
        "headers": b"GET /health HTTP/1.1\r\nHost: localhost\r\nX-Slow: ",
        "body": b"POST /login HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\nContent-Length: 1000\r\n\r\n{",
        "headers_then_body": b"POST /login HTTP/1.1\r\nHost: localhost\r\nX-Slow: ",
    }
    started = threading.Event()
    stop = threading.Event()
    shop = service.Shop()
    handler = service.make_handler(shop)

    class ObservedHandler(handler):
        def setup(self):
            super().setup()
            started.set()

    with patch.object(service, "REQUEST_TIMEOUT", deadline, create=True):
        server = service.ShopHTTPServer(("127.0.0.1", 0), ObservedHandler, max_workers=1)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        try:
            with socket.create_connection(server.server_address, timeout=duration + 0.5) as slow:
                beginning = time.monotonic()
                slow.sendall(prefixes[stage])
                if not started.wait(2):
                    raise RuntimeError("request handler did not start")
                initial_health = health_status(server.server_address)
                writes = []
                body_started = []

                def send_bytes():
                    while time.monotonic() - beginning < duration and not stop.wait(interval):
                        try:
                            if stage == "headers_then_body" and not body_started and time.monotonic() - beginning >= deadline * 0.75:
                                slow.sendall(b"\r\nContent-Type: application/json\r\nContent-Length: 1000\r\n\r\n{")
                                body_started.append(time.monotonic() - beginning)
                            slow.sendall(b" ")
                            writes.append(time.monotonic() - beginning)
                        except OSError:
                            return

                writer = threading.Thread(target=send_bytes, daemon=True)
                writer.start()
                response = b""
                closed = False
                try:
                    while chunk := slow.recv(4096):
                        response += chunk
                    closed = True
                except TimeoutError:
                    pass
                except (ConnectionResetError, BrokenPipeError):
                    closed = True
                finally:
                    elapsed = time.monotonic() - beginning
                    stop.set()
                    writer.join(timeout=1)
                # Keep the attack socket open while checking worker recovery.
                # A bounded retry allows the worker's finally block to run.
                recovery_limit = time.monotonic() + 0.3
                while True:
                    recovered = health_status(server.server_address)
                    if recovered == 200 or time.monotonic() >= recovery_limit:
                        break
                    time.sleep(0.01)
                return {"stage": stage, "configured_deadline": deadline, "byte_interval": interval,
                        "client_observed_seconds": round(elapsed, 3), "server_closed": closed,
                        "response_status_line": response.split(b"\r\n", 1)[0].decode("ascii", "replace"),
                        "bytes_trickled": len(writes), "initial_health": initial_health,
                        "health_after_deadline": recovered,
                        "body_started_seconds": round(body_started[0], 3) if body_started else None}
        finally:
            server.shutdown()
            server_thread.join(timeout=5)
            server.server_close()
            shop.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--deadline", type=float, default=0.4)
    parser.add_argument("--interval", type=float, default=0.08)
    parser.add_argument("--duration", type=float, default=1.2)
    parser.add_argument("--stage", choices=("all", "body"), default="all")
    args = parser.parse_args()
    evidence = {"service_sha256": hashlib.sha256(Path(service.__file__).read_bytes()).hexdigest(),
                "unicode_review": unicode_probe(),
                "trickle": [trickle_probe(stage, args.deadline, args.interval, args.duration)
                            for stage in (("body",) if args.stage == "body" else ("request_line", "headers", "body"))]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, ensure_ascii=True, indent=2) + "\n")
    print(json.dumps(evidence, ensure_ascii=True, indent=2))
