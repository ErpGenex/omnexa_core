# Copyright (c) 2026, ErpGenEx
import unittest


class TestFinanceDemoHub(unittest.TestCase):
	def test_portal_catalog(self):
		from omnexa_core.omnexa_core.finance_demo.finance_portal_catalog import PORTAL_CATALOG, get_portal_catalog

		self.assertGreater(len(PORTAL_CATALOG), 10)
		catalog = get_portal_catalog(include_missing=1)
		self.assertTrue(any(p["id"] == "demo-hub" for p in catalog))

	def test_role_specs(self):
		from omnexa_core.omnexa_core.finance_demo.finance_role_demo import ROLE_SPECS

		self.assertGreaterEqual(len(ROLE_SPECS), 12)
		emails = [s["email"] for s in ROLE_SPECS]
		self.assertEqual(len(emails), len(set(emails)))
