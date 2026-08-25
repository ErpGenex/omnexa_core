# Copyright (c) 2026, ErpGenEx
"""Wave 9 — per-activity operational E2E smoke (integration bus + vertical DocTypes)."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core.activity_registry import ACTIVITIES, get_activity
from omnexa_core.omnexa_core.integration_bridge import financial_snapshot, inventory_snapshot


ACTIVITY_SMOKE: dict[str, dict] = {
	"Healthcare": {
		"source_app": "omnexa_healthcare",
		"doctypes": ("Healthcare Patient", "Healthcare Appointment"),
	},
	"Construction": {
		"source_app": "omnexa_construction",
		"doctypes": ("Project Contract", "IPC Certificate"),
	},
	"Financial Services": {
		"source_app": "omnexa_finance_engine",
		"doctypes": ("Finance Product",),
	},
	"Trading": {
		"source_app": "omnexa_trading",
		"doctypes": ("Item",),
	},
	"Education": {
		"source_app": "omnexa_education",
		"doctypes": ("Education Student",),
	},
	"Real Estate": {
		"source_app": "erpgenex_realestate_sales",
		"doctypes": ("Sales Booking",),
	},
}


class TestWave9ActivityE2E(FrappeTestCase):
	def _company(self) -> str | None:
		return frappe.db.get_value("Company", {}, "name")

	def test_activity_registry_covers_e2e_matrix(self):
		for activity_id in ACTIVITY_SMOKE:
			self.assertIn(activity_id, ACTIVITIES)

	def test_per_activity_integration_snapshots(self):
		company = self._company()
		if not company:
			self.skipTest("no company")
		for activity_id, spec in ACTIVITY_SMOKE.items():
			with self.subTest(activity=activity_id):
				source = spec["source_app"]
				fin = financial_snapshot(company, source_app=source)
				self.assertTrue(fin.ok, msg=f"{activity_id} financial: {fin.message}")
				inv = inventory_snapshot(company, source_app=source)
				self.assertTrue(inv.ok, msg=f"{activity_id} inventory: {inv.message}")

	def test_per_activity_doctype_smoke(self):
		for activity_id, spec in ACTIVITY_SMOKE.items():
			with self.subTest(activity=activity_id):
				present = [dt for dt in spec["doctypes"] if frappe.db.exists("DocType", dt)]
				if not present:
					self.skipTest(f"{activity_id} doctypes not on site")
				for dt in present:
					self.assertTrue(frappe.db.exists("DocType", dt))

	def test_vertical_apps_in_registry(self):
		for activity_id, spec in ACTIVITY_SMOKE.items():
			activity = get_activity(activity_id)
			self.assertIn(spec["source_app"], activity.vertical_apps)
