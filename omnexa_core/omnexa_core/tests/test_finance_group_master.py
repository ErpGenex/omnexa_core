# Copyright (c) 2026, ErpGenEx
import frappe
from frappe.tests.utils import FrappeTestCase


class TestFinanceGroupMaster(FrappeTestCase):
	def test_run_full_finance_group_closure(self):
		from omnexa_core.omnexa_core.finance_demo.finance_group_master import run_full_finance_group_closure

		out = run_full_finance_group_closure(seed_roles=0, seed_verticals=0)
		self.assertTrue(out.get("ok"))
		self.assertGreaterEqual(float(out.get("weighted_score") or 0), 4.9)
		self.assertGreaterEqual(int(out.get("apps_passed") or 0), 12)
		self.assertTrue(out.get("all_closed"))

	def test_master_docs_path(self):
		from omnexa_core.omnexa_core.finance_demo.finance_group_master import get_master_docs_path

		p = get_master_docs_path()
		self.assertIn("MASTER_CHECKLIST", p.get("checklist", ""))
