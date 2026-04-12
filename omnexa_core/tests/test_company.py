# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestOmnexaCompany(FrappeTestCase):
	def setUp(self):
		super().setUp()
		if not frappe.db.exists("Currency", "EGP"):
			frappe.get_doc(
				{"doctype": "Currency", "currency_name": "EGP", "symbol": "E£", "enabled": 1}
			).insert(ignore_permissions=True)
		if not frappe.db.exists("Country", "Egypt"):
			frappe.get_doc(
				{"doctype": "Country", "country_name": "Egypt", "code": "EG"}
			).insert(ignore_permissions=True)

	def test_rin_required_when_eta_enabled(self):
		doc = frappe.new_doc("Company")
		doc.company_name = "Test Pilot Co"
		doc.abbr = "TPCO"
		doc.default_currency = "EGP"
		doc.country = "Egypt"
		doc.status = "Draft"
		doc.eta_einvoice_enabled = 1
		doc.rin = ""
		with self.assertRaises(frappe.ValidationError):
			doc.insert(ignore_permissions=True)

	def test_company_inserts_when_eta_and_rin_set(self):
		doc = frappe.new_doc("Company")
		doc.company_name = "Test Pilot Co 2"
		doc.abbr = "TPC2"
		doc.default_currency = "EGP"
		doc.country = "Egypt"
		doc.status = "Draft"
		doc.eta_einvoice_enabled = 1
		doc.rin = "123456789"
		doc.insert(ignore_permissions=True)
		self.assertTrue(frappe.db.exists("Company", doc.name))
