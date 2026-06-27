# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core.branch_access import permission_query_conditions_for_branch_field
from omnexa_core.tests.test_helpers import clear_privileged_view_context


class TestOmnexaBranch(FrappeTestCase):
	def setUp(self):
		super().setUp()
		clear_privileged_view_context()
		if not frappe.db.exists("Currency", "EGP"):
			frappe.get_doc(
				{"doctype": "Currency", "currency_name": "EGP", "symbol": "E£", "enabled": 1}
			).insert(ignore_permissions=True)
		if not frappe.db.exists("Country", "Egypt"):
			frappe.get_doc(
				{"doctype": "Country", "country_name": "Egypt", "code": "EG"}
			).insert(ignore_permissions=True)

	def _make_company(self, label: str):
		abbr = f"{label[:2].upper()}{frappe.generate_hash(length=3).upper()}"
		doc = frappe.new_doc("Company")
		doc.company_name = f"Branch Co {label} {abbr}"
		doc.abbr = abbr
		doc.default_currency = "EGP"
		doc.country = "Egypt"
		doc.status = "Active"
		doc.insert(ignore_permissions=True)
		return doc

	def _make_tax_authority_profile(self, company: str, suffix: str):
		return frappe.get_doc(
			{
				"doctype": "Tax Authority Profile",
				"company": company,
				"country_code": "EG",
				"adapter_id": "EGY_ETA",
				"api_base_url": f"https://eta.example/{suffix}",
			}
		).insert(ignore_permissions=True)

	def _make_signing_profile(self, company: str, suffix: str):
		return frappe.get_doc(
			{
				"doctype": "Signing Profile",
				"company": company,
				"profile_name": f"Sign {suffix}",
				"certificate_vault_ref": f"vault://{suffix}",
			}
		).insert(ignore_permissions=True)

	def test_branch_code_unique_within_company(self):
		company = self._make_company("A")
		a = frappe.get_doc(
			{
				"doctype": "Branch",
				"company": company.name,
				"branch_name": "Main",
				"branch_code": "MAIN",
			}
		).insert(ignore_permissions=True)
		self.assertTrue(a.name)
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "Branch",
					"company": company.name,
					"branch_name": "Main 2",
					"branch_code": "MAIN",
				}
			).insert(ignore_permissions=True)

	def test_same_code_allowed_in_different_companies(self):
		company_a = self._make_company("B")
		company_b = self._make_company("C")
		x = frappe.get_doc(
			{
				"doctype": "Branch",
				"company": company_a.name,
				"branch_name": "HQ A",
				"branch_code": "HQ",
			}
		).insert(ignore_permissions=True)
		y = frappe.get_doc(
			{
				"doctype": "Branch",
				"company": company_b.name,
				"branch_name": "HQ B",
				"branch_code": "HQ",
			}
		).insert(ignore_permissions=True)
		self.assertTrue(x.name and y.name)

	def test_parent_branch_must_belong_to_same_company(self):
		company_a = self._make_company("D")
		company_b = self._make_company("E")
		parent = frappe.get_doc(
			{
				"doctype": "Branch",
				"company": company_a.name,
				"branch_name": "Parent A",
				"branch_code": "PA",
			}
		).insert(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "Branch",
					"company": company_b.name,
					"branch_name": "Child B",
					"branch_code": "CB",
					"parent_branch": parent.name,
				}
			).insert(ignore_permissions=True)

	def test_branch_eta_requires_profiles(self):
		company = self._make_company("F")
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "Branch",
					"company": company.name,
					"branch_name": "ETA Branch",
					"branch_code": "ETA",
					"eta_einvoice_enabled": 1,
				}
			).insert(ignore_permissions=True)

	def test_branch_eta_profiles_must_belong_to_same_company(self):
		company_a = self._make_company("G")
		company_b = self._make_company("H")
		tax_b = self._make_tax_authority_profile(company_b.name, "b-tax")
		sign_b = self._make_signing_profile(company_b.name, "b-sign")
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "Branch",
					"company": company_a.name,
					"branch_name": "ETA Wrong",
					"branch_code": "ETW",
					"eta_einvoice_enabled": 1,
					"tax_authority_profile": tax_b.name,
					"signing_profile": sign_b.name,
				}
			).insert(ignore_permissions=True)

	def test_single_head_office_per_company(self):
		company = self._make_company("I")
		# Company bootstrap creates one head office automatically.
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "Branch",
					"company": company.name,
					"branch_name": "Head Office Extra",
					"branch_code": "HOX",
					"is_head_office": 1,
				}
			).insert(ignore_permissions=True)

	def test_branch_permission_query_unrestricted_for_admin(self):
		frappe.set_user("Administrator")
		self.assertEqual(permission_query_conditions_for_branch_field("Project Contract"), "")

	def test_branch_permission_query_accepts_spaced_doctype_names(self):
		frappe.set_user("Administrator")
		self.assertEqual(permission_query_conditions_for_branch_field("BOQ Item"), "")

	def test_branch_must_belong_to_selected_company_on_document(self):
		company_a = self._make_company("J")
		company_b = self._make_company("K")
		branch_b = frappe.get_doc(
			{
				"doctype": "Branch",
				"company": company_b.name,
				"branch_name": "Branch B",
				"branch_code": "BB",
			}
		).insert(ignore_permissions=True)
		from omnexa_core.omnexa_core.branch_access import enforce_branch_company_coherence

		doc = frappe.new_doc("Event Audit Log")
		doc.company = company_a.name
		doc.branch = branch_b.name
		with self.assertRaises(frappe.ValidationError):
			enforce_branch_company_coherence(doc)
