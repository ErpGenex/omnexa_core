# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core.test_data import create_test_company, ensure_pilot_geo


class TestOmnexaTestData(FrappeTestCase):
	def test_ensure_pilot_geo_idempotent(self):
		ensure_pilot_geo()
		ensure_pilot_geo()
		self.assertTrue(frappe.db.exists("Currency", "EGP"))
		self.assertTrue(frappe.db.exists("Country", "Egypt"))

	def test_create_test_company_returns_name(self):
		abbr = "OMNX-TDATA"
		name = create_test_company(abbr)
		self.assertTrue(name)
		self.assertEqual(frappe.db.get_value("Company", name, "abbr"), abbr)
		# second call returns same
		self.assertEqual(create_test_company(abbr), name)
