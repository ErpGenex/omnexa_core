# Copyright (c) 2026, ErpGenEx

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core.activity_scope import (
	get_apps_to_keep_for_activity,
	get_apps_to_uninstall_for_activity,
	is_mandatory_site_app,
	list_company_activities,
)


class TestActivityScope(FrappeTestCase):
	def test_mandatory_apps_include_core_theme_backup(self):
		for app in ("frappe", "omnexa_core", "omnexa_backup", "erpgenex_theme_0426", "omnexa_accounting"):
			self.assertTrue(is_mandatory_site_app(app))

	def test_healthcare_scope_keeps_healthcare_not_construction(self):
		installed = set(frappe.get_installed_apps() or [])
		keep = get_apps_to_keep_for_activity("Healthcare")
		if "omnexa_healthcare" in installed:
			self.assertIn("omnexa_healthcare", keep)
		if "omnexa_construction" in installed:
			self.assertNotIn("omnexa_construction", keep)

	def test_construction_scope_keeps_construction_and_erpgenex_verticals(self):
		installed = set(frappe.get_installed_apps() or [])
		keep = get_apps_to_keep_for_activity("Construction")
		if "omnexa_construction" in installed:
			self.assertIn("omnexa_construction", keep)
		if "erpgenex_property_mgmt" in installed:
			self.assertIn("erpgenex_property_mgmt", keep)

	def test_uninstall_list_excludes_mandatory(self):
		remove = get_apps_to_uninstall_for_activity("Healthcare")
		for app in ("frappe", "omnexa_core", "omnexa_backup", "omnexa_accounting"):
			if app in (frappe.get_installed_apps() or []):
				self.assertNotIn(app, remove)

	def test_list_company_activities_not_empty(self):
		self.assertIn("Healthcare", list_company_activities())
		self.assertIn("General", list_company_activities())
