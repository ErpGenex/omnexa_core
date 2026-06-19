# Copyright (c) 2026, ErpGenEx
import unittest

import frappe


class TestFinanceGroupSidebar(unittest.TestCase):
	def test_accounting_not_under_finance_group(self):
		from omnexa_core.omnexa_core.finance_demo.finance_group_sidebar import sync_finance_group_sidebar

		sync_finance_group_sidebar()
		frappe.db.commit()
		parent = frappe.db.get_value("Workspace", "Accounting", "parent_page") or ""
		self.assertEqual(parent, "", f"Accounting parent_page should be empty, got {parent!r}")

	def test_finance_vertical_under_group(self):
		parent = frappe.db.get_value("Workspace", "SME Microfinance", "parent_page") or ""
		self.assertEqual(parent, "Finance Group")

	def test_finance_engine_has_valid_icon(self):
		icon = frappe.db.get_value("Workspace", "Finance Engine", "icon")
		self.assertIn(icon, ("accounting", "crm", "chart", "loan", "users", "quality", "sell", "assets", "organization", "project"))
