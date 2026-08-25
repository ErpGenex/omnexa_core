# Copyright (c) 2026, ErpGenEx

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core.scoped_website_assets import (
	app_matches_path,
	path_matches_prefix,
	update_website_context,
)


class TestScopedWebsiteAssets(FrappeTestCase):
	def test_path_matches_prefix_avoids_telemedicine_admin_false_positive(self):
		self.assertTrue(path_matches_prefix("/telemedicine", "/telemedicine"))
		self.assertTrue(path_matches_prefix("/telemedicine/room", "/telemedicine"))
		self.assertFalse(path_matches_prefix("/telemedicine-admin", "/telemedicine"))
		self.assertTrue(path_matches_prefix("/telemedicine-admin", "/telemedicine-admin"))

	def test_path_matches_prefix_education_student_portal(self):
		self.assertTrue(path_matches_prefix("/education-student-portal", "/education-student-portal"))
		self.assertFalse(path_matches_prefix("/education-student-portal", "/education"))

	def test_app_matches_path(self):
		self.assertTrue(app_matches_path(["/hospital", "/telemedicine"], "/hospital/booking"))
		self.assertFalse(app_matches_path(["/hospital"], "/education"))

	def test_update_website_context_filters_healthcare_on_education(self):
		if "omnexa_healthcare" not in frappe.get_installed_apps():
			self.skipTest("healthcare not installed")
		if "omnexa_education" not in frappe.get_installed_apps():
			self.skipTest("education not installed")

		context = frappe._dict(
			path="education/index",
			web_include_css=[
				"/assets/frappe/css/frappe.css",
				"/assets/omnexa_healthcare/css/hospital_website.css",
				"/assets/omnexa_education/css/education_website.css",
			],
			web_include_js=[
				"/assets/frappe/js/frappe.js",
				"/assets/omnexa_healthcare/js/hospital_website.js",
				"/assets/omnexa_education/js/education_website.js",
			],
		)
		out = update_website_context(context)
		self.assertIn("/assets/omnexa_education/css/education_website.css", out["web_include_css"])
		self.assertNotIn("/assets/omnexa_healthcare/css/hospital_website.css", out["web_include_css"])
		self.assertIn("/assets/omnexa_education/js/education_website.js", out["web_include_js"])
		self.assertNotIn("/assets/omnexa_healthcare/js/hospital_website.js", out["web_include_js"])

	def test_update_website_context_keeps_healthcare_on_hospital(self):
		if "omnexa_healthcare" not in frappe.get_installed_apps():
			self.skipTest("healthcare not installed")

		context = frappe._dict(
			path="hospital/index",
			web_include_css=[
				"/assets/omnexa_healthcare/css/hospital_website.css",
				"/assets/omnexa_education/css/education_website.css",
			],
			web_include_js=[
				"/assets/omnexa_healthcare/js/hospital_website.js",
				"/assets/omnexa_education/js/education_website.js",
			],
		)
		out = update_website_context(context)
		self.assertIn("/assets/omnexa_healthcare/css/hospital_website.css", out["web_include_css"])
		self.assertNotIn("/assets/omnexa_education/css/education_website.css", out["web_include_css"])
