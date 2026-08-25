# Copyright (c) 2026, ErpGenEx
"""Wave 9 — activity-aware PQC and cross-vertical SQL isolation."""

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core.activity_pqc import (
	activity_blocks_doctype,
	activity_permission_query_conditions,
	app_from_doctype,
	activity_pqc_self_test,
	site_has_multiple_vertical_apps,
)
from omnexa_core.omnexa_core.permissions import global_branch_permission_query_conditions


class TestActivityPQC(FrappeTestCase):
	def test_self_test_passes(self):
		report = activity_pqc_self_test()
		self.assertTrue(report["all_pass"], msg=str(report))

	def test_healthcare_doctype_resolves_app(self):
		if not frappe.db.exists("DocType", "Healthcare Patient"):
			self.skipTest("healthcare not installed")
		self.assertEqual(app_from_doctype("Healthcare Patient"), "omnexa_healthcare")

	def test_general_activity_does_not_block_verticals(self):
		"""General/demo companies keep cross-vertical visibility."""
		if not site_has_multiple_vertical_apps():
			self.skipTest("single vertical site")
		self.assertFalse(activity_blocks_doctype("Healthcare Patient"))

	def test_platform_doctype_never_blocked(self):
		if not frappe.db.exists("DocType", "Sales Invoice"):
			self.skipTest("accounting not installed")
		self.assertFalse(activity_blocks_doctype("Sales Invoice"))

	def test_global_permission_hook_chains_activity(self):
		if not frappe.db.exists("DocType", "Healthcare Patient"):
			self.skipTest("healthcare not installed")
		sql = global_branch_permission_query_conditions("Administrator", "Healthcare Patient")
		self.assertNotEqual(sql, "1=0")

	def test_permission_query_returns_empty_when_allowed(self):
		sql = activity_permission_query_conditions("Administrator", "Healthcare Patient")
		self.assertIn(sql, ("",))
