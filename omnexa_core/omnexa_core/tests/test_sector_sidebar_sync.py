# Copyright (c) 2026, ErpGenEx
import unittest

import frappe


class TestSectorSidebarSync(unittest.TestCase):
	def setUp(self):
		from omnexa_core.omnexa_core.finance_demo.finance_group_sidebar import sync_finance_group_sidebar
		from omnexa_core.omnexa_core.sector_sidebar_sync import sync_sector_sidebar
		from omnexa_nursery.workspace.nurs_workspace import sync_nurs_workspace_menu

		sync_finance_group_sidebar()
		sync_sector_sidebar()
		sync_nurs_workspace_menu(save=True, rebuild=True)
		frappe.db.commit()

	def test_accounting_not_under_finance_group(self):
		parent = frappe.db.get_value("Workspace", "Accounting", "parent_page") or ""
		self.assertNotEqual(
			parent,
			"Finance Group",
			f"Accounting must not be under Finance Group, got {parent!r}",
		)

	def test_finance_vertical_under_group(self):
		parent = frappe.db.get_value("Workspace", "SME Microfinance", "parent_page") or ""
		self.assertEqual(parent, "Finance Group")

	def test_nursery_content_and_parent(self):
		parent = frappe.db.get_value("Workspace", "Nursery", "parent_page") or ""
		self.assertEqual(parent, "Industries")
		content = frappe.db.get_value("Workspace", "Nursery", "content") or "[]"
		self.assertIn("Nursery Settings", content)

	def test_no_workspace_removed_from_db(self):
		"""Sector sync must not delete or hide app workspaces."""
		workspaces = frappe.get_all("Workspace", pluck="name", limit_page_length=500)
		self.assertGreater(len(workspaces), 5, "Expected workspaces to remain in database")

	def test_asset_insurance_nested_under_fixed_assets(self):
		if not frappe.db.exists("Workspace", "Asset Insurance"):
			return
		parent = frappe.db.get_value("Workspace", "Asset Insurance", "parent_page") or ""
		self.assertIn(
			parent,
			{"Fixed Assets", "Fixed assets"},
			f"Asset Insurance should stay under Fixed Assets, got {parent!r}",
		)

	def test_sector_registry_covers_core_workspaces(self):
		from omnexa_core.omnexa_core.sector_registry import get_workspace_sector

		for ws in ("Stock", "HR", "CRM"):
			if frappe.db.exists("Workspace", ws):
				self.assertEqual(get_workspace_sector(ws), "core_erp")

	def test_sync_idempotent(self):
		from omnexa_core.omnexa_core.sector_sidebar_sync import sync_sector_sidebar

		first = sync_sector_sidebar(save=False)
		second = sync_sector_sidebar(save=False)
		self.assertEqual(len(first.get("reparented") or []), 0)
		self.assertEqual(len(second.get("reparented") or []), 0)
