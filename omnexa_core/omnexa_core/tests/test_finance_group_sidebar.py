# Copyright (c) 2026, ErpGenEx
import unittest

import frappe


class TestFinanceGroupSidebar(unittest.TestCase):
	def test_accounting_not_under_finance_group(self):
		from omnexa_core.omnexa_core.finance_demo.finance_group_sidebar import sync_finance_group_sidebar

		sync_finance_group_sidebar()
		frappe.db.commit()
		parent = frappe.db.get_value("Workspace", "Accounting", "parent_page") or ""
		self.assertNotEqual(
			parent,
			"Finance Group",
			f"Accounting parent_page must not be Finance Group, got {parent!r}",
		)

	def test_finance_vertical_under_group(self):
		parent = frappe.db.get_value("Workspace", "SME Microfinance", "parent_page") or ""
		self.assertIn(parent, {"Finance", "Finance Group"})

	def test_finance_engine_has_valid_icon(self):
		icon = frappe.db.get_value("Workspace", "Finance Engine", "icon")
		self.assertIn(icon, ("accounting", "crm", "chart", "loan", "users", "quality", "sell", "assets", "organization", "project"))

	def test_finance_sidebars_have_icons(self):
		from omnexa_core.omnexa_core.finance_demo.finance_group_sidebar import (
			CORE_PLATFORM_WORKSPACES,
			_finance_vertical_workspaces,
			sync_finance_group_sidebar,
		)

		sync_finance_group_sidebar()
		frappe.db.commit()

		names = {"Finance Group", *CORE_PLATFORM_WORKSPACES, *_finance_vertical_workspaces()}
		for ws_name in names:
			if not frappe.db.exists("Workspace", ws_name):
				continue
			icon = frappe.db.get_value("Workspace", ws_name, "icon") or ""
			self.assertTrue(icon.strip(), f"Workspace {ws_name!r} must have an icon")

	def test_factoring_governance_hidden_if_present(self):
		if not frappe.db.exists("Workspace", "Factoring Governance"):
			return
		is_hidden = frappe.db.get_value("Workspace", "Factoring Governance", "is_hidden")
		parent = frappe.db.get_value("Workspace", "Factoring Governance", "parent_page") or ""
		self.assertEqual(is_hidden, 1)
		self.assertEqual(parent, "")
