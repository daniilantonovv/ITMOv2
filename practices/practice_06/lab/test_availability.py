"""Regressions for invalid Unicode storage and active slow-request exhaustion."""

import json
import unittest
from unittest.mock import patch

from attacks import LocalShop
from availability_probe import trickle_probe


class UnicodeAvailabilityTest(unittest.TestCase):
    def setUp(self):
        self.local = LocalShop()
        self.local.__enter__()
        self.addCleanup(self.local.__exit__, None, None, None)
        self.auth = self.local.login()

    def test_unpaired_surrogates_are_rejected_without_poisoning_read_endpoints(self):
        for review in ("\ud800", "\udfff", "prefix\ud800suffix"):
            with self.subTest(review=ascii(review)):
                status, _ = self.local.call("POST", "/reviews", {"product": "chair", "text": review}, self.auth)
                self.assertEqual(status, 400)
        self.assertEqual(self.local.call("GET", "/reviews/view")[0], 200)
        status, context = self.local.call("GET", "/assistant/context?order_id=1", auth=self.auth)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(context["prompt"])["untrusted_reviews"], [])

    def test_direct_dispatch_rejects_unicode_before_storage(self):
        with self.local.shop.lock:
            status, _ = self.local.shop.dispatch("POST", "/reviews", {"product": "chair", "text": "\ud800"}, self.auth)
        self.assertEqual(status, 400)
        self.assertEqual(self.local.shop.reviews, [])

    def test_valid_non_bmp_review_is_preserved(self):
        review = "Удобный стул 😀 𐐀"
        self.assertEqual(self.local.call("POST", "/reviews", {"product": "chair", "text": review}, self.auth)[0], 201)
        self.assertIn(review, self.local.call("GET", "/reviews/view")[1])
        status, context = self.local.call("GET", "/assistant/context?order_id=1", auth=self.auth)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(context["prompt"])["untrusted_reviews"][0]["text"], review)

    def test_serialization_failures_return_safe_json_before_headers_are_sent(self):
        for result in ("\ud800", {"unexpected": "\udfff"}, {"unexpected": {1, 2}}, {"unexpected": float("nan")}):
            with self.subTest(result=ascii(result)):
                # Inject an application-result fault; the real HTTP encoder and
                # socket must return a complete safe error, never disconnect.
                with patch.object(self.local.shop, "dispatch", return_value=(200, result)):
                    status, body = self.local.call("GET", "/health")
                self.assertEqual((status, body), (500, {"error": "internal error"}))
        self.assertEqual(self.local.call("GET", "/health"), (200, {"status": "ok"}))


class ActiveSlowRequestTest(unittest.TestCase):
    def assert_deadline(self, stage):
        result = trickle_probe(stage)
        self.assertGreaterEqual(result["bytes_trickled"], 2)
        self.assertEqual(result["initial_health"], 503)
        self.assertTrue(result["server_closed"], result)
        self.assertLess(result["client_observed_seconds"], 1.0, result)
        self.assertEqual(result["health_after_deadline"], 200, result)
        if stage == "body":
            self.assertIn(" 408 ", result["response_status_line"])

    def test_trickled_request_line_cannot_extend_absolute_deadline(self):
        self.assert_deadline("request_line")

    def test_trickled_headers_cannot_extend_absolute_deadline(self):
        self.assert_deadline("headers")

    def test_trickled_body_cannot_extend_absolute_deadline(self):
        self.assert_deadline("body")

    def test_headers_and_body_share_the_same_request_deadline(self):
        result = trickle_probe("headers_then_body", deadline=1.0, interval=0.08, duration=2.0)
        self.assertGreaterEqual(result["body_started_seconds"], 0.75)
        self.assertTrue(result["server_closed"], result)
        self.assertLess(result["client_observed_seconds"], 1.4, result)
        self.assertIn(" 408 ", result["response_status_line"])
        self.assertEqual(result["health_after_deadline"], 200, result)


if __name__ == "__main__":
    unittest.main()
