# Mourad.Soltani — CalloutSlip health tests
import json
import threading
import unittest
import urllib.request
from decimal import Decimal

from app import Handler, ThreadingHTTPServer
from src.quote import QuoteError, build_quote


SAMPLE = {
    "trade": "locksmith",
    "customer": "Harbor Apartments",
    "job_summary": "Night lockout",
    "window": "night",
    "callout_fee": 80,
    "miles": 10,
    "mileage_rate": 2,
    "labor_hours": 1,
    "labor_rate": 100,
    "parts_cost": 20,
    "parts_markup": 0.5,
    "tax_rate": 0.1,
    "deposit_rate": 0.25,
    "minimum_charge": 50,
}


class QuoteTests(unittest.TestCase):
    def test_night_multiplier(self):
        quote = build_quote(SAMPLE)
        # before = 80 + 20 + 100 + 30 = 230; night x1.60 = 368; tax 36.80; total 404.80
        self.assertEqual(quote.subtotal_before_window, "230.00")
        self.assertEqual(quote.taxable, "368.00")
        self.assertEqual(quote.total, "404.80")
        self.assertEqual(quote.deposit_due, "101.20")
        self.assertFalse(quote.minimum_applied)
        self.assertIn("Mourad.Soltani", quote.slip)

    def test_minimum_floor(self):
        raw = dict(SAMPLE, window="standard", callout_fee=10, miles=0, labor_hours=0, parts_cost=0, minimum_charge=150)
        quote = build_quote(raw)
        self.assertTrue(quote.minimum_applied)
        self.assertEqual(quote.taxable, "150.00")
        self.assertEqual(quote.total, "165.00")

    def test_rejects_bad_trade_and_rates(self):
        with self.assertRaises(QuoteError):
            build_quote(dict(SAMPLE, trade="dentist"))
        with self.assertRaises(QuoteError):
            build_quote(dict(SAMPLE, miles=-1))
        with self.assertRaises(QuoteError):
            build_quote(dict(SAMPLE, tax_rate=0.5))


class HealthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def test_health(self):
        with urllib.request.urlopen(self.base + "/health") as response:
            body = json.loads(response.read().decode())
        self.assertEqual(response.status, 200)
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["author"], "Mourad.Soltani")

    def test_quote_endpoint(self):
        request = urllib.request.Request(
            self.base + "/api/quote",
            data=json.dumps(SAMPLE).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request) as response:
            body = json.loads(response.read().decode())
        self.assertEqual(body["total"], "404.80")
        self.assertTrue(body["slip"].startswith("CALLOUTSLIP"))


if __name__ == "__main__":
    unittest.main()
