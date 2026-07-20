# Copyright (c) 2026, ErpGenEx

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core.app_visibility import (
	app_matches_company_activity,
	get_activity_hidden_apps,
	get_hidden_desk_apps,
	get_user_company_activity,
	set_desk_app_hidden,
)


class TestAppVisibility(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")

	def test_hide_and_show_desk_app(self):
		if not frappe.db.exists("DocType", "Omnexa Marketplace Settings"):
			self.skipTest("Omnexa Marketplace Settings not migrated")
		slug = "omnexa_healthcare"
		if slug not in (frappe.get_installed_apps() or []):
			self.skipTest("omnexa_healthcare not installed")

		set_desk_app_hidden(slug, hidden=True)
		self.assertIn(slug, get_hidden_desk_apps())

		set_desk_app_hidden(slug, hidden=False)
		self.assertNotIn(slug, get_hidden_desk_apps())

	def test_cannot_hide_platform_core(self):
		if not frappe.db.exists("DocType", "Omnexa Marketplace Settings"):
			self.skipTest("Omnexa Marketplace Settings not migrated")
		with self.assertRaises(frappe.ValidationError):
			set_desk_app_hidden("omnexa_core", hidden=True)

	def test_healthcare_activity_hides_leasing(self):
		if "omnexa_leasing_finance" not in (frappe.get_installed_apps() or []):
			self.skipTest("leasing app not installed")
		hidden = get_activity_hidden_apps("Healthcare")
		self.assertIn("omnexa_leasing_finance", hidden)
		self.assertTrue(app_matches_company_activity("omnexa_healthcare", "Healthcare"))
		self.assertFalse(app_matches_company_activity("omnexa_leasing_finance", "Healthcare"))

	def test_financial_services_shows_leasing(self):
		if "omnexa_leasing_finance" not in (frappe.get_installed_apps() or []):
			self.skipTest("leasing app not installed")
		hidden = get_activity_hidden_apps("Financial Services")
		self.assertNotIn("omnexa_leasing_finance", hidden)

	def test_get_user_company_activity_reads_company(self):
		company = frappe.db.get_value("Company", {}, "name")
		if not company:
			self.skipTest("no company")
		frappe.defaults.set_user_default("Company", company)
		activity = get_user_company_activity()
		self.assertTrue(isinstance(activity, str) and activity)
