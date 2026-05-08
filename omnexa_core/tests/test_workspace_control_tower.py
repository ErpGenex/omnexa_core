# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import json

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core.workspace_control_tower import (
	_aggregatable_doctype,
	_app_installed,
	infer_workspace_spec,
	sync_workspace_for_app,
)


class TestWorkspaceControlTower(FrappeTestCase):
	def test_app_installed_reflects_bench(self):
		self.assertTrue(_app_installed("frappe"))
		self.assertTrue(_app_installed("omnexa_core"))

	def test_single_doctype_not_aggregatable_for_kpis(self):
		"""Single DocTypes (e.g. Website Settings) have no row table — Number Card Count must skip them."""
		if frappe.db.exists("DocType", "Website Settings"):
			self.assertFalse(_aggregatable_doctype("Website Settings"))
		if frappe.db.exists("DocType", "User"):
			self.assertTrue(_aggregatable_doctype("User"))

	def test_sync_noop_for_unknown_app(self):
		sync_workspace_for_app("not_a_registered_omnexa_app")

	def test_infer_spec_caps_kpi_trends(self):
		if not frappe.db.exists("Workspace", "Sell"):
			return
		ws = frappe.get_doc("Workspace", "Sell")
		spec = infer_workspace_spec(ws)
		self.assertLessEqual(len(spec.get("kpi_trends") or []), 6)
		# After control-tower sync, Sell may be card-only; infer still respects caps when doctypes exist.
		if spec.get("trend_doctypes"):
			self.assertLessEqual(len(spec["trend_doctypes"]), 3)

	def test_sell_workspace_control_tower_kpis(self):
		if not frappe.db.exists("Workspace", "Sell"):
			return
		from omnexa_core.workspace_onboarding_sync import enable_onboarding_setting, sync_workspace_database

		enable_onboarding_setting()
		sync_workspace_database()
		sync_workspace_for_app("omnexa_core")
		ws = frappe.get_doc("Workspace", "Sell")
		self.assertGreaterEqual(len(ws.number_cards or []), 4)
		self.assertGreaterEqual(len(ws.charts or []), 2)
		self.assertGreaterEqual(len(ws.shortcuts or []), 4)
		settings_targets = {
			s.get("link_to")
			for s in (ws.shortcuts or [])
			if (s.get("type") or "").strip() == "DocType"
		}
		if frappe.db.exists("DocType", "Omnexa Sales Settings"):
			self.assertIn("Omnexa Sales Settings", settings_targets)
		report_links = {
			r.get("link_to")
			for r in (ws.links or [])
			if r.get("type") == "Link" and r.get("link_type") == "Report"
		}
		if frappe.db.exists("Report", "Sales by Customer"):
			self.assertIn("Sales by Customer", report_links)
		self.assertNotIn("Customer Ledger", report_links)
		self.assertNotIn("Receivables Aging", report_links)
		blocks = json.loads(ws.content or "[]")
		types = [b.get("type") for b in blocks]
		self.assertIn("onboarding", types)
		# Control tower layout: Operations → Reports → KPIs → Charts (single hierarchy, no orphaned KPI strip).
		self.assertIn("Operations", ws.content or "")
		self.assertIn("KPIs", ws.content or "")
		self.assertIn("Charts", ws.content or "")

	def test_buy_stock_finance_hr_control_tower_kpis(self):
		for key in (
			"omnexa_core_buy",
			"omnexa_core_stock",
			"omnexa_core_finance",
		):
			sync_workspace_for_app(key)
		if _app_installed("omnexa_hr"):
			sync_workspace_for_app("omnexa_hr")
		for name, min_cards, min_ch in (
			("Buy", 4, 2),
			("Stock", 3, 2),
		):
			if not frappe.db.exists("Workspace", name):
				continue
			ws = frappe.get_doc("Workspace", name)
			self.assertGreaterEqual(len(ws.number_cards or []), min_cards, msg=name)
			self.assertGreaterEqual(len(ws.charts or []), min_ch, msg=name)
		if _app_installed("omnexa_accounting") and frappe.db.exists("Workspace", "Accounting"):
			ws = frappe.get_doc("Workspace", "Accounting")
			self.assertGreaterEqual(len(ws.number_cards or []), 4, msg="Accounting")
			self.assertGreaterEqual(len(ws.charts or []), 2, msg="Accounting")
		if _app_installed("omnexa_hr") and frappe.db.exists("Workspace", "HR"):
			ws = frappe.get_doc("Workspace", "HR")
			self.assertGreaterEqual(len(ws.number_cards or []), 4, msg="HR")
			self.assertGreaterEqual(len(ws.charts or []), 2, msg="HR")
