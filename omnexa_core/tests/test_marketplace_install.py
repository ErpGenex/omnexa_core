# Copyright (c) 2026, ErpGenEx

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core.marketplace import _uninstall_protected_apps
from omnexa_core.omnexa_core.marketplace_install import (
	basic_platform_apps,
	marketplace_basic_deps_only_enabled,
	missing_basic_platform_apps,
	skipped_required_apps_for,
)


class TestMarketplaceInstall(FrappeTestCase):
	def test_basic_deps_only_enabled_by_default(self):
		self.assertTrue(marketplace_basic_deps_only_enabled())

	def test_basic_platform_apps_includes_core(self):
		apps = basic_platform_apps()
		self.assertIn("frappe", apps)
		self.assertIn("omnexa_core", apps)
		self.assertIn("omnexa_accounting", apps)

	def test_missing_basic_platform_apps_excludes_target(self):
		missing = missing_basic_platform_apps(exclude="omnexa_accounting")
		self.assertNotIn("omnexa_accounting", missing)

	def test_uninstall_protects_basic_apps(self):
		protected = _uninstall_protected_apps()
		for app in basic_platform_apps():
			self.assertIn(app, protected)

	def test_skipped_required_apps_is_list(self):
		skipped = skipped_required_apps_for("omnexa_trading")
		self.assertIsInstance(skipped, list)
