# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core.feature_flags import (
	get_enabled_modules,
	is_feature_enabled,
	is_module_enabled,
)


class TestFeatureFlags(FrappeTestCase):
	def test_feature_flag_reads_boolean_and_string_values(self):
		old = frappe.local.conf.get("omnexa_feature_flags")
		try:
			frappe.local.conf["omnexa_feature_flags"] = {"new_checkout": "true", "legacy_mode": 0}
			self.assertTrue(is_feature_enabled("new_checkout"))
			self.assertFalse(is_feature_enabled("legacy_mode"))
			self.assertTrue(is_feature_enabled("missing_flag", default=True))
		finally:
			if old is None:
				frappe.local.conf.pop("omnexa_feature_flags", None)
			else:
				frappe.local.conf["omnexa_feature_flags"] = old

	def test_module_toggle_parsing_and_lookup(self):
		old = frappe.local.conf.get("omnexa_enabled_modules")
		try:
			frappe.local.conf["omnexa_enabled_modules"] = "accounting,experience"
			enabled = get_enabled_modules()
			self.assertIn("accounting", enabled)
			self.assertTrue(is_module_enabled("experience"))
			self.assertFalse(is_module_enabled("fintech", default=False))
		finally:
			if old is None:
				frappe.local.conf.pop("omnexa_enabled_modules", None)
			else:
				frappe.local.conf["omnexa_enabled_modules"] = old
