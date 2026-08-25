# Copyright (c) 2026, Omnexa
import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core.session_scope import resolve_effective_branch, resolve_effective_company


class TestCoreSessionScope(FrappeTestCase):
	def test_resolve_effective_company(self):
		company = resolve_effective_company()
		if company:
			self.assertTrue(frappe.db.exists("Company", company))

	def test_resolve_effective_branch(self):
		company = resolve_effective_company()
		if not company:
			return
		branch = resolve_effective_branch(company)
		if branch:
			self.assertEqual(frappe.db.get_value("Branch", branch, "company"), company)
