# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core.branch_access import (
	enforce_branch_access,
	get_allowed_branches,
	permission_query_conditions_for_branch_field,
)
from omnexa_core.tests.test_helpers import clear_privileged_view_context


class TestRolePermissions(FrappeTestCase):
	def setUp(self):
		super().setUp()
		clear_privileged_view_context()
		self._email = "branch-restricted@example.com"
		self._ensure_user()

	def _ensure_user(self):
		if not frappe.db.exists("User", self._email):
			u = frappe.new_doc("User")
			u.email = self._email
			u.first_name = "Branch"
			u.last_name = "Restricted"
			u.enabled = 1
			u.new_password = "test123"
			u.insert(ignore_permissions=True)
		else:
			u = frappe.get_doc("User", self._email)
		# Strip privileged roles — keep a minimal desk role only.
		u.roles = []
		u.append("roles", {"role": "Desk User"
	})
		u.save(ignore_permissions=True)

	def _company_with_two_branches(self):
		if not frappe.db.exists("Currency", "EGP"):
			frappe.get_doc(
				{"doctype": "Currency", "currency_name": "EGP", "symbol": "E£", "enabled": 1
	}
			).insert(ignore_permissions=True)
		if not frappe.db.exists("Country", "Egypt"):
			frappe.get_doc(
				{"doctype": "Country", "country_name": "Egypt", "code": "EG"
	}
			).insert(ignore_permissions=True)
		abbr = frappe.generate_hash(length=4).upper()
		co = frappe.get_doc(
			{
				"doctype": "Company",
				"company_name": f"Perm Co {abbr
	}",
				"abbr": abbr,
				"default_currency": "EGP",
				"country": "Egypt",
				"status": "Active"
	}
		).insert(ignore_permissions=True)
		b1 = frappe.get_doc(
			{
				"doctype": "Branch",
				"company": co.name,
				"branch_name": f"Branch A {abbr
	}",
				"branch_code": f"A{abbr[:2]
	}",
				"status": "Active"
	}
		).insert(ignore_permissions=True)
		b2 = frappe.get_doc(
			{
				"doctype": "Branch",
				"company": co.name,
				"branch_name": f"Branch B {abbr
	}",
				"branch_code": f"B{abbr[:2]
	}",
				"status": "Active"
	}
		).insert(ignore_permissions=True)
		return co.name, b1.name, b2.name

	def _grant_branch(self, company: str, branch: str):
		for row in frappe.get_all("User Branch Access", filters={"user": self._email
	}, pluck="name"):
			frappe.delete_doc("User Branch Access", row, force=1, ignore_permissions=True)
		frappe.db.delete(
			"DefaultValue",
			{"parent": self._email, "defkey": ("in", ("company", "Company", "branch", "Branch"))},
		)
		frappe.get_doc(
			{
				"doctype": "User Branch Access",
				"user": self._email,
				"company": company,
				"branch": branch,
				"is_default": 1
	}
		).insert(ignore_permissions=True)
		frappe.defaults.set_user_default("company", company, self._email)
		frappe.defaults.set_user_default("branch", branch, self._email)

	def test_restricted_user_allowed_branches(self):
		company, branch_a, _branch_b = self._company_with_two_branches()
		self._grant_branch(company, branch_a)
		allowed = get_allowed_branches(self._email, company)
		self.assertEqual(allowed, [branch_a])

	def test_restricted_user_permission_query_filters_branch(self):
		company, branch_a, branch_b = self._company_with_two_branches()
		self._grant_branch(company, branch_a)
		frappe.set_user(self._email)
		try:
			cond = permission_query_conditions_for_branch_field("Journal Entry", self._email)
			self.assertIn(branch_a, cond)
			self.assertNotIn(branch_b, cond)
			self.assertIn("branch", cond.lower())
		finally:
			frappe.set_user("Administrator")

	def test_restricted_user_cannot_use_foreign_branch(self):
		company, branch_a, branch_b = self._company_with_two_branches()
		self._grant_branch(company, branch_a)
		frappe.set_user(self._email)
		try:
			doc = frappe.new_doc("Event Audit Log")
			doc.company = company
			doc.branch = branch_b
			doc.event_type = "Test"
			with self.assertRaises(frappe.ValidationError):
				enforce_branch_access(doc, user=self._email)
		finally:
			frappe.set_user("Administrator")
