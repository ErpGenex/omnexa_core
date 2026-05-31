# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core.branch_access import permission_query_conditions_for_branch_field
from omnexa_core.omnexa_core.session_context import set_view_context, get_view_context


class TestSessionContext(FrappeTestCase):
	def test_admin_view_scope_filters_branch(self):
		frappe.set_user("Administrator")
		companies = frappe.get_all("Company", pluck="name", limit=1)
		if not companies:
			self.skipTest("No company on site")
		company = companies[0]
		branches = frappe.get_all("Branch", filters={"company": company}, pluck="name", limit=2)
		if len(branches) < 1:
			self.skipTest("No branches on site")

		set_view_context(company=company, branch=branches[0], view_all_branches=0)
		cond = permission_query_conditions_for_branch_field("Journal Entry")
		self.assertIn(branches[0], cond)

		set_view_context(company=company, view_all_branches=1)
		ctx = get_view_context()
		self.assertTrue(ctx.get("view_all_branches"))
