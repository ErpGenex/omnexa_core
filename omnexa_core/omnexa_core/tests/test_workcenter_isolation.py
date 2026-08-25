# Copyright (c) 2026, ErpGenEx

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_core.vertical_workcenter.context import get_workcenter_context


class TestWorkcenterIsolation(FrappeTestCase):
	def test_restaurant_context_is_not_healthcare_branded(self):
		if "omnexa_restaurant" not in frappe.get_installed_apps():
			self.skipTest("restaurant not installed")

		ctx = get_workcenter_context("omnexa_restaurant")
		self.assertEqual(ctx["app"], "omnexa_restaurant")
		self.assertFalse(ctx["use_clinic_portal_grid"])
		self.assertNotIn("Healthcare", ctx["brand_name_en"])
		self.assertEqual(ctx["portal_subtitle_en"], "Role portal")

	def test_healthcare_context_keeps_clinic_grid(self):
		if "omnexa_healthcare" not in frappe.get_installed_apps():
			self.skipTest("healthcare not installed")

		ctx = get_workcenter_context("omnexa_healthcare")
		self.assertTrue(ctx["use_clinic_portal_grid"])
		self.assertEqual(ctx["brand_name_en"], "Omnexa Healthcare")
		self.assertEqual(ctx["portal_subtitle_en"], "Outpatient portal")

	def test_grouped_portals_scoped_to_app(self):
		if "omnexa_restaurant" not in frappe.get_installed_apps():
			self.skipTest("restaurant not installed")

		ctx = get_workcenter_context("omnexa_restaurant")
		routes = [
			p.get("route")
			for g in ctx.get("grouped_portals") or []
			for p in g.get("portals") or []
		]
		self.assertTrue(all("/restaurant-" in (r or "") for r in routes if r))
