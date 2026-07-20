# Copyright (c) 2026, ErpGenEx
import frappe
from frappe.tests.utils import FrappeTestCase


class TestFinanceVerticalBPE(FrappeTestCase):
	def test_sync_all_finance_vertical_bpe(self):
		from omnexa_core.omnexa_core.finance_demo.finance_vertical_bpe import sync_all_finance_vertical_bpe

		out = sync_all_finance_vertical_bpe()
		self.assertTrue(out.get("ok"))
		results = out.get("results") or []
		self.assertGreaterEqual(len(results), 13)
		failed = [r for r in results if not r.get("ok")]
		self.assertEqual(failed, [], msg=str(failed))
		self.assertEqual(out.get("stage_gate_version"), "14-state-universal")

	def test_workflows_created_for_consumer(self):
		if "omnexa_consumer_finance" not in frappe.get_installed_apps():
			self.skipTest("consumer finance not installed")
		name = frappe.db.get_value(
			"Workflow",
			{"document_type": "Consumer Finance Case", "is_active": 1
	},
			"name",
		)
		self.assertTrue(name)

	def test_cf_roles_exist(self):
		if "omnexa_consumer_finance" not in frappe.get_installed_apps():
			self.skipTest("consumer finance not installed")
		self.assertTrue(frappe.db.exists("Role", "CF Branch Manager"))
