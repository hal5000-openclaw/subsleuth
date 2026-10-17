import unittest
import sys
import os
import json
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from subs import parse_csv, detect_recurring, normalize_merchant

class TestSubs(unittest.TestCase):
    def setUp(self):
        self.csv_path = os.path.join(os.path.dirname(__file__), 'sample.csv')

    def test_parse_csv(self):
        txs = parse_csv(self.csv_path)
        self.assertGreater(len(txs), 0)
        self.assertIn('date', txs[0])
        self.assertIn('merchant', txs[0])
        self.assertIn('amount', txs[0])

    def test_normalize_merchant(self):
        self.assertEqual(normalize_merchant('Netflix'), 'netflix')
        self.assertEqual(normalize_merchant('Netflix!'), 'netflix')
        self.assertEqual(normalize_merchant('Spotify Premium'), 'spotify premium')

    def test_detect_monthly(self):
        txs = parse_csv(self.csv_path)
        rec = detect_recurring(txs)
        merchants = {r['merchant']: r for r in rec}
        self.assertIn('Netflix', merchants)
        self.assertEqual(merchants['Netflix']['cadence'], 'monthly')
        self.assertAlmostEqual(merchants['Netflix']['amount'], 12.99)
        self.assertGreaterEqual(merchants['Netflix']['occurrences'], 3)

    def test_detect_annual(self):
        txs = parse_csv(self.csv_path)
        rec = detect_recurring(txs)
        merchants = {r['merchant']: r for r in rec}
        self.assertIn('Amazon Prime', merchants)
        self.assertEqual(merchants['Amazon Prime']['cadence'], 'annual')

    def test_non_recurring_ignored(self):
        txs = parse_csv(self.csv_path)
        rec = detect_recurring(txs)
        merchants = {r['merchant']: r for r in rec}
        self.assertNotIn('Grocery Store', merchants)

    def test_json_output(self):
        txs = parse_csv(self.csv_path)
        rec = detect_recurring(txs)
        output = json.dumps(rec, default=str)
        data = json.loads(output)
        self.assertIsInstance(data, list)
        self.assertTrue(all('merchant' in r for r in data))

if __name__ == '__main__':
    unittest.main()
