"""Security regressions use the actual loopback HTTP server and real SQLite/files."""

import json
import socket
import time
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlencode
from unittest.mock import patch

from attacks import INJECTION, LocalShop
from service import ShopHTTPServer, make_handler


class SecurityTest(unittest.TestCase):
    def setUp(self):
        self.local = LocalShop()
        self.local.__enter__()
        self.addCleanup(self.local.__exit__, None, None, None)
        self.alice = self.local.login()
        self.bob = self.local.login("bob")
        self.staff = self.local.login("staff")

    def call(self, method, path, body=None, auth=None, raw=None):
        return self.local.call(method, path, body, auth, raw)

    def test_sensitive_routes_require_a_session(self):
        routes = [("GET", "/profile"), ("GET", "/search"), ("GET", "/orders"),
                  ("GET", "/files"), ("GET", "/admin/export"), ("GET", "/debug/logs"),
                  ("GET", "/assistant/context"), ("POST", "/assistant/execute"),
                  ("POST", "/reviews"), ("POST", "/orders")]
        for method, path in routes:
            for headers in ({}, {"X-Token": "forged", "X-Role": "staff"}):
                with self.subTest(method=method, path=path, headers=headers):
                    self.assertEqual(self.call(method, path, {}, headers)[0], 401)

    def test_customer_cannot_access_another_profile_or_order(self):
        for path in ("/profile?id=2", "/assistant/context?order_id=2"):
            with self.subTest(path=path):
                status, body = self.call("GET", path, auth=self.alice)
                self.assertEqual(status, 403)
                self.assertNotIn("TEST_BOB", json.dumps(body))
        self.assertEqual([r["owner"] for r in self.call("GET", "/orders", auth=self.alice)[1]], [1])
        self.assertEqual([r["owner"] for r in self.call("GET", "/orders", auth=self.bob)[1]], [2])

    def test_profile_search_is_staff_only_and_literal(self):
        self.assertEqual(self.call("GET", "/search?q=", auth=self.alice)[0], 403)
        for text in ("' OR 1=1 --", "%", "TEST%ALICE", "\\"):
            with self.subTest(query=text):
                status, result = self.call("GET", "/search?" + urlencode({"q": text}), auth=self.staff)
                self.assertEqual((status, result), (200, []))
        self.assertEqual(len(self.call("GET", "/search?q=ALICE", auth=self.staff)[1]), 1)
        self.assertEqual(len(self.call("GET", "/search?q=_", auth=self.staff)[1]), 2)

    def test_id_sql_injections_are_rejected(self):
        for field, path in (("id", "/profile"), ("order_id", "/assistant/context")):
            for value in ("1 OR 1=1", "1 UNION SELECT 1,2,3,4", "-1", "0", "1.0", "a", "9" * 500):
                with self.subTest(field=field, value=value):
                    self.assertEqual(self.call("GET", path + "?" + urlencode({field: value}), auth=self.alice)[0], 400)

    def test_only_server_session_grants_staff_permissions(self):
        for path in ("/admin/export", "/debug/logs"):
            self.assertEqual(self.call("GET", path, auth={**self.alice, "X-Role": "staff"})[0], 403)
            self.assertEqual(self.call("GET", path, auth=self.staff)[0], 200)
        self.assertEqual(len(self.call("GET", "/orders", auth=self.staff)[1]), 2)
        self.assertEqual(self.call("GET", "/profile?id=2", auth=self.staff)[1][0]["name"], "TEST_BOB")

    def test_price_and_owner_are_derived_on_the_server(self):
        for price in (-100, 0, 1, "free", None, {"nested": "object"}):
            with self.subTest(price=price):
                status, order = self.call("POST", "/orders", {"product": "chair", "price": price, "owner": 2}, self.alice)
                self.assertEqual(status, 201)
                self.assertEqual((order["owner"], order["price"]), (1, 5000))

    def test_files_are_limited_to_the_authenticated_owner_receipt(self):
        paths = ["/files?user=bob&path=receipt.txt", "/files?user=alice&path=../bob/receipt.txt",
                 "/files?user=alice&path=../../private/operator-note.txt",
                 "/files?user=../private&path=operator-note.txt", "/files?path=/etc/passwd",
                 "/files?path=%2e%2e%2f%2e%2e%2fprivate%2foperator-note.txt"]
        for path in paths:
            with self.subTest(path=path):
                status, body = self.call("GET", path, auth=self.alice)
                self.assertEqual(status, 403)
                self.assertNotIn("TEST_ONLY_OPERATOR_SECRET", json.dumps(body))
        self.assertIn("TEST_ALICE", self.call("GET", "/files", auth=self.alice)[1]["content"])
        self.assertIn("TEST_BOB", self.call("GET", "/files", auth=self.bob)[1]["content"])

    def test_stored_html_is_displayed_as_text(self):
        text = '<script>alert("xss")</script><img src=x onerror=alert(1)>'
        self.assertEqual(self.call("POST", "/reviews", {"product": "chair", "text": text}, self.alice)[0], 201)
        status, html = self.call("GET", "/reviews/view")
        self.assertEqual(status, 200)
        self.assertNotIn("<script>", html)
        self.assertNotIn("<img", html)
        self.assertIn("&lt;script&gt;", html)

    def test_logs_contain_no_passwords_tokens_or_user_text(self):
        self.call("POST", "/reviews", {"product": "chair", "text": "PRIVATE_REVIEW_MARKER"}, self.alice)
        self.call("GET", "/assistant/context?order_id=1&question=PRIVATE_QUESTION_MARKER", auth=self.alice)
        status, logs = self.call("GET", "/debug/logs", auth=self.staff)
        self.assertEqual(status, 200)
        text = json.dumps(logs)
        for secret in ("learn-alice", "learn-bob", self.alice["X-Token"], "PRIVATE_REVIEW_MARKER", "PRIVATE_QUESTION_MARKER"):
            self.assertNotIn(secret, text)
        self.assertTrue(logs)

    def test_assistant_cannot_execute_dangerous_or_forged_tools(self):
        decisions = [{"tool": "export_profiles"}, {"tool": "delete_tree", "arguments": {"path": "."}},
                     {"tool": "read_file", "arguments": {"path": "files/bob/receipt.txt"}},
                     {"tool": "read_file", "arguments": {"path": "private/operator-note.txt"}},
                     {"tool": "read_file", "arguments": {"path": "files/alice/../bob/receipt.txt"}},
                     {"tool": "read_file", "arguments": {"path": "/etc/passwd"}}]
        for decision in decisions:
            with self.subTest(decision=decision):
                self.assertEqual(self.call("POST", "/assistant/execute", {"decision": decision}, self.alice)[0], 403)
        self.assertTrue((self.local.shop.sandbox.root / "files/alice/receipt.txt").exists())
        # Staff must use the explicit admin endpoint; the AI executor has no admin capability.
        self.assertEqual(self.call("POST", "/assistant/execute", {"decision": {"tool": "export_profiles"}}, self.staff)[0], 403)

    def test_injection_is_untrusted_data_and_server_rejects_its_action(self):
        self.call("POST", "/reviews", {"product": "chair", "text": INJECTION}, self.bob)
        self.call("POST", "/reviews", {"product": "lamp", "text": "UNRELATED_LAMP_REVIEW"}, self.bob)
        status, context = self.call("GET", "/assistant/context?order_id=1", auth=self.alice)
        self.assertEqual(status, 200)
        self.assertIn(INJECTION, json.loads(context["prompt"])["untrusted_reviews"][0]["text"])
        self.assertNotIn("UNRELATED_LAMP_REVIEW", context["prompt"])
        self.assertNotIn("TEST_BOB", context["prompt"])
        self.assertEqual(self.call("POST", "/assistant/execute", {"decision": {"tool": "delete_tree", "arguments": {"path": "."}}}, self.alice)[0], 403)
        self.assertIn("TEST_ALICE", self.call("GET", "/files", auth=self.alice)[1]["content"])

    def test_assistant_supports_normal_receipt_and_explicit_refusal(self):
        for auth, owner in ((self.alice, "alice"), (self.bob, "bob")):
            status, body = self.call("POST", "/assistant/execute", {"decision": {"tool": "read_file", "arguments": {"path": f"files/{owner}/receipt.txt"}}}, auth)
            self.assertEqual(status, 200)
            self.assertIn("TEST_" + owner.upper(), body["content"])
        status, body = self.call("POST", "/assistant/execute", {"decision": {"tool": "refuse", "arguments": {"reason": "untrusted instructions"}}}, self.alice)
        self.assertEqual(status, 200)
        self.assertTrue(body["refused"])

    def test_malformed_requests_fail_without_tracebacks_or_mutation(self):
        for raw in (b'{', b'[]', b'null', b'42', b'"text"', b'\xff', b'{"product":"chair","product":"lamp"}', b'{"price":NaN}'):
            with self.subTest(raw=raw):
                status, result = self.call("POST", "/orders", auth=self.alice, raw=raw)
                self.assertEqual(status, 400)
                self.assertNotIn("type", result)
                self.assertNotIn("Traceback", json.dumps(result))
        for body in ({}, {"product": []}, {"product": {}}):
            self.assertEqual(self.call("POST", "/orders", body, self.alice)[0], 400)
        self.assertEqual(len(self.call("GET", "/orders", auth=self.alice)[1]), 1)

    def test_nested_decisions_and_login_types_are_validated(self):
        for decision in (None, [], "read_file", {}, {"tool": []}, {"tool": "read_file", "arguments": []}, {"tool": "read_file", "arguments": {"path": 1}}):
            with self.subTest(decision=decision):
                self.assertEqual(self.call("POST", "/assistant/execute", {"decision": decision}, self.alice)[0], 400)
        for body in ({}, {"username": [], "password": "x"}, {"username": "alice", "password": []}):
            self.assertEqual(self.call("POST", "/login", body)[0], 400)

    def test_missing_resources_and_query_ambiguity_are_safe(self):
        for path in ("/profile?id=999", "/assistant/context?order_id=999", "/files?path=missing.txt"):
            status, body = self.call("GET", path, auth=self.staff if "files" not in path else self.alice)
            self.assertIn(status, (403, 404))
            self.assertNotIn("/private/", json.dumps(body))
            self.assertNotIn("FileNotFoundError", json.dumps(body))
        for path in ("/profile?id=1&id=2", "/assistant/context?order_id=1&order_id=2"):
            self.assertEqual(self.call("GET", path, auth=self.alice)[0], 400)

    def test_review_validation_and_context_limits(self):
        for body in ({}, {"product": "unknown", "text": "x"}, {"product": "chair", "text": []},
                     {"product": "chair", "text": " "}, {"product": "chair", "text": "x" * 2001}):
            self.assertEqual(self.call("POST", "/reviews", body, self.alice)[0], 400)
        self.assertEqual(self.call("GET", "/assistant/context?" + urlencode({"question": "x" * 2001}), auth=self.alice)[0], 400)

    def raw_http(self, headers, body=b""):
        with socket.create_connection(self.local.server.server_address, timeout=3) as connection:
            connection.sendall(b"POST /orders HTTP/1.1\r\nHost: localhost\r\n" + headers + b"Connection: close\r\n\r\n" + body)
            response = b""
            while chunk := connection.recv(65536):
                response += chunk
        return response

    def test_ambiguous_or_oversized_http_framing_is_rejected(self):
        for headers, expected in ((b"Content-Length: bad\r\n", 400), (b"Content-Length: -1\r\n", 400),
                                  (b"Content-Length: 65537\r\n", 413), (b"Content-Length: 2\r\nContent-Length: 2\r\n", 400),
                                  (b"Transfer-Encoding: chunked\r\n", 400)):
            with self.subTest(headers=headers):
                self.assertIn(f" {expected} ".encode(), self.raw_http(headers, b'{}').split(b'\r\n')[0])

    def test_content_type_and_browser_origin_are_checked(self):
        for headers, expected in ((b"Content-Type: text/plain\r\n", 415),
                                  (b"Content-Type: application/json\r\nOrigin: https://evil.invalid\r\n", 403)):
            response = self.raw_http(headers + b"Content-Length: 2\r\n", b'{}')
            self.assertIn(f" {expected} ".encode(), response.split(b'\r\n')[0])

    def test_response_headers_and_safe_internal_errors(self):
        response = self.raw_http(b"Content-Type: application/json\r\nContent-Length: 2\r\n", b'{}')
        self.assertIn(b"X-Content-Type-Options: nosniff", response)
        self.local.shop.db.close()
        status, body = self.call("GET", "/orders", auth=self.alice)
        self.assertEqual((status, body), (500, {"error": "internal error"}))

    def test_session_expiry_and_login_throttling(self):
        for _ in range(5):
            self.assertEqual(self.call("POST", "/login", {"username": "alice", "password": "wrong"})[0], 401)
        self.assertEqual(self.call("POST", "/login", {"username": "alice", "password": "wrong"})[0], 429)
        now = time.monotonic()
        with patch("service.time.monotonic", return_value=now + 61):
            self.assertEqual(self.call("POST", "/login", {"username": "alice", "password": "learn-alice"})[0], 200)
        with patch("service.time.monotonic", return_value=now + 3602):
            self.assertEqual(self.call("GET", "/orders", auth=self.alice)[0], 401)

    def test_state_quotas_prevent_unbounded_growth_without_corrupting_existing_data(self):
        with patch("service.MAX_SESSIONS", 3):
            self.assertEqual(self.call("POST", "/login", {"username": "alice", "password": "learn-alice"})[0], 429)
        with patch("service.MAX_REVIEWS", 1):
            self.assertEqual(self.call("POST", "/reviews", {"product": "chair", "text": "first"}, self.alice)[0], 201)
            self.assertEqual(self.call("POST", "/reviews", {"product": "chair", "text": "overflow"}, self.alice)[0], 429)
            self.assertNotIn("overflow", self.call("GET", "/reviews/view")[1])
        with patch("service.MAX_ORDERS", 3):
            self.assertEqual(self.call("POST", "/orders", {"product": "chair"}, self.alice)[0], 201)
            self.assertEqual(self.call("POST", "/orders", {"product": "chair"}, self.alice)[0], 429)
            self.assertEqual(len(self.call("GET", "/orders", auth=self.staff)[1]), 3)
        for _ in range(205):
            self.call("GET", "/health")
        self.assertEqual(len(self.call("GET", "/debug/logs", auth=self.staff)[1]), 200)

    def test_non_loopback_host_is_rejected(self):
        with socket.create_connection(self.local.server.server_address, timeout=3) as connection:
            connection.sendall(b"GET /health HTTP/1.1\r\nHost: evil.invalid\r\nConnection: close\r\n\r\n")
            self.assertIn(b" 403 ", connection.recv(4096).split(b"\r\n")[0])

    def test_slow_client_timeout_and_worker_limit_keep_server_available(self):
        started = threading.Event()
        handler = make_handler(self.local.shop)

        class ObservedHandler(handler):
            def setup(inner):
                super().setup()
                started.set()

        server = ShopHTTPServer(("127.0.0.1", 0), ObservedHandler, max_workers=1)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with socket.create_connection(server.server_address, timeout=5) as slow:
                slow.sendall(b"POST /login HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\nContent-Length: 100\r\n\r\n{")
                self.assertTrue(started.wait(2))
                with socket.create_connection(server.server_address, timeout=2) as overflow:
                    self.assertIn(b" 503 ", overflow.recv(4096).split(b"\r\n")[0])
                self.assertIn(b" 408 ", slow.recv(4096).split(b"\r\n")[0])
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()

    def test_concurrent_orders_keep_their_owners_and_catalog_prices(self):
        def buy(i):
            return self.call("POST", "/orders", {"product": "lamp", "price": 0}, self.alice if i % 2 == 0 else self.bob)
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(buy, range(8)))
        self.assertEqual([r[0] for r in results], [201] * 8)
        self.assertEqual(len({r[1]["id"] for r in results}), 8)
        self.assertEqual([r[1]["owner"] for r in results], [1, 2] * 4)
        self.assertEqual([r[1]["price"] for r in results], [1500] * 8)


if __name__ == "__main__":
    unittest.main()
