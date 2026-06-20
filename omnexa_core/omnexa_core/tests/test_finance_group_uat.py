# Copyright (c) 2026, ErpGenEx
import frappe
from frappe.tests.utils import FrappeTestCase


class TestFinanceGroupUAT(FrappeTestCase):
	def test_automated_uat(self):
		from omnexa_core.omnexa_core.finance_demo.finance_group_uat import run_automated_uat

		out = run_automated_uat()
		self.assertTrue(out.get("ok"), msg=str([s for s in out.get("scenarios", []) if not s.get("passed")]))
		self.assertGreaterEqual(int(out.get("scenarios_passed") or 0), 20)

	def test_wave5_connectors(self):
		from omnexa_core.omnexa_core.finance_demo.finance_wave5_stubs import verify_wave5_connectors

		out = verify_wave5_connectors()
		self.assertTrue(out.get("ok"))
		self.assertEqual(out.get("connectors_passed"), 5)
