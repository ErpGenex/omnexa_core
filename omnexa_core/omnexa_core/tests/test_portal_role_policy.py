# Copyright (c) 2026, ErpGenEx

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_core.vertical_workcenter.portal_role_policy import filter_grouped_portals_for_user, is_portal_admin
from omnexa_core.vertical_workcenter.role_portal_context import get_role_portal_context


class TestPortalRolePolicy(FrappeTestCase):
	def test_admin_sees_all_restaurant_portals(self):
		if "omnexa_restaurant" not in frappe.get_installed_apps():
			self.skipTest("restaurant not installed")
		self.assertTrue(is_portal_admin("Administrator"))
		ctx = get_role_portal_context("omnexa_restaurant", "executive-dashboard")
		self.assertTrue(ctx["is_admin"])
		self.assertGreaterEqual(len(ctx.get("sibling_portals") or []), 4)

	def test_role_portal_has_workspace_menus_for_manager(self):
		if "omnexa_restaurant" not in frappe.get_installed_apps():
			self.skipTest("restaurant not installed")
		ctx = get_role_portal_context("omnexa_restaurant", "executive-dashboard")
		self.assertIn("menu_sections", ctx)
		if ctx["is_admin"]:
			self.assertGreater(len(ctx.get("menu_sections") or []), 0)

	def test_filter_removes_inaccessible_portals(self):
		groups = [
			{
				"label_en": "Role Portals",
				"portals": [
					{"id": "x-executive-dashboard", "roles": ["System Manager"], "exists": True},
					{"id": "x-customer-portal", "roles": ["Customer"], "exists": True},
				],
			}
		]
		filtered = filter_grouped_portals_for_user(groups, user="Guest")
		self.assertEqual(len(filtered), 0)
