# Copyright (c) 2026, ErpGenEx and contributors
# SPDX-License-Identifier: MIT
"""E2.1 — ICP smoke: accounting + e-invoice both participate in Sales Invoice lifecycle (CI Must-Pass)."""

import frappe
from frappe.tests.utils import FrappeTestCase


class TestQualityIcpAccountingEinvoiceE2e(FrappeTestCase):
	def test_sales_invoice_doc_events_link_accounting_and_einvoice(self):
		"""Cross-app chain: SI validate/submit hooks from omnexa_accounting + omnexa_einvoice."""
		installed = set(frappe.get_installed_apps())
		if "omnexa_accounting" not in installed:
			self.skipTest("omnexa_accounting not installed")
		if "omnexa_einvoice" not in installed:
			self.skipTest("omnexa_einvoice not installed")
		if not frappe.db.exists("DocType", "Sales Invoice"):
			self.skipTest("Sales Invoice DocType missing")

		doc_events = (frappe.get_hooks("doc_events") or {}).get("Sales Invoice") or {}
		self.assertIsInstance(doc_events, dict)

		validate_hooks = doc_events.get("validate") or []
		if not isinstance(validate_hooks, list):
			validate_hooks = [validate_hooks]
		self.assertTrue(
			any("omnexa_accounting" in str(h) for h in validate_hooks),
			msg=f"Expected omnexa_accounting validate hooks, got {validate_hooks}",
		)

		before_submit = doc_events.get("before_submit") or []
		if not isinstance(before_submit, list):
			before_submit = [before_submit]
		self.assertTrue(
			any("omnexa_einvoice" in str(h) for h in before_submit),
			msg=f"Expected omnexa_einvoice before_submit hooks, got {before_submit}",
		)
