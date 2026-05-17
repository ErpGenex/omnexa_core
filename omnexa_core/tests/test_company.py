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

	def test_company_inserts_and_creates_head_office_branch(self):
		doc = frappe.new_doc("Company")
		doc.company_name = "Test Pilot Co 2"
		doc.abbr = frappe.generate_hash(length=4).upper()
		doc.default_currency = "EGP"
		doc.country = "Egypt"
		doc.status = "Draft"
		doc.insert(ignore_permissions=True)
		self.assertTrue(frappe.db.exists("Company", doc.name))
		self.assertTrue(frappe.db.exists("Branch", {"company": doc.name, "is_head_office": 1}))
		doc.delete(ignore_permissions=True)

	def test_company_save_with_rin_and_tax_id(self):
		doc = frappe.new_doc("Company")
		doc.company_name = "Test Pilot Co RIN"
		doc.abbr = frappe.generate_hash(length=4).upper()
		doc.default_currency = "EGP"
		doc.country = "Egypt"
		doc.status = "Draft"
		doc.tax_id = "258797215"
		doc.rin = "258797215"
		doc.insert(ignore_permissions=True)
		doc.save(ignore_permissions=True)
		self.assertEqual(frappe.db.get_value("Company", doc.name, "rin"), "258797215")
		doc.delete(ignore_permissions=True)
