# Copyright (c) 2026, ErpGenEx

from unittest.mock import patch
from types import SimpleNamespace

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core import marketplace_install
from omnexa_core.omnexa_core.marketplace import (
	_uninstall_protected_apps,
	bulk_install_apps_now,
	bulk_update_apps_now,
	get_bulk_install_plan,
	get_bulk_update_plan,
)
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

	def test_install_app_on_site_does_not_recurse_basic_prereqs(self):
		installed = ["frappe"]

		def get_installed_apps():
			return list(dict.fromkeys(installed))

		def add_installed(app):
			if app not in installed:
				installed.append(app)

		def get_hooks(hook=None, default="_KEEP_DEFAULT_LIST", app_name=None):
			if app_name:
				return frappe._dict(before_install=[], after_install=[], after_sync=[], required_apps=[])
			return []

		with (
			patch.object(marketplace_install, "basic_platform_apps", return_value=["frappe", "omnexa_core", "omnexa_accounting"]),
			patch.object(marketplace_install, "marketplace_basic_deps_only_enabled", return_value=True),
			patch.object(marketplace_install, "_app_on_bench", return_value=True),
			patch.object(marketplace_install, "add_module_defs"),
			patch.object(marketplace_install, "sync_dashboards"),
			patch.object(marketplace_install, "set_all_patches_as_completed"),
			patch.object(marketplace_install, "add_to_installed_apps", side_effect=add_installed),
			patch("frappe.core.doctype.scheduled_job_type.scheduled_job_type.sync_jobs"),
			patch("frappe.model.sync.sync_for"),
			patch("frappe.modules.utils.sync_customizations"),
			patch("frappe.utils.fixtures.sync_fixtures"),
			patch.object(frappe, "get_installed_apps", side_effect=get_installed_apps),
			patch.object(frappe, "get_hooks", side_effect=get_hooks),
			patch.object(frappe, "only_for"),
			patch.object(frappe, "clear_cache"),
			patch.object(frappe, "get_doc", return_value=frappe._dict(sync_menu=lambda: None)),
		):
			marketplace_install.install_app_on_site("omnexa_core")

		self.assertEqual(installed.count("omnexa_core"), 1)
		self.assertEqual(installed.count("omnexa_accounting"), 1)
		self.assertIn("omnexa_core", installed)
		self.assertIn("omnexa_accounting", installed)

	def test_bulk_install_plan_and_action(self):
		plan = {"eligible": ["omnexa_a", "omnexa_b"], "already_installed": ["omnexa_c"], "blocked": [], "warning": "w"}
		with (
			patch("omnexa_core.omnexa_core.marketplace._bulk_install_plan", return_value=plan),
			patch("omnexa_core.omnexa_core.marketplace._backup_before_install", return_value={"ok": True}),
			patch("omnexa_core.omnexa_core.marketplace._run_post_bulk_app_change_hardening", return_value={"ok": True, "build_ok": True, "sync_ok": True}),
			patch("omnexa_core.omnexa_core.marketplace._can_install_on_this_site", return_value=True),
			patch("omnexa_core.omnexa_core.marketplace_install.install_app_on_site") as install_site,
			patch.object(frappe, "only_for"),
			patch.object(frappe, "clear_cache"),
			patch.object(frappe, "local", SimpleNamespace(site="test.local", flags=SimpleNamespace(in_test=True)), create=True),
		):
			result = bulk_install_apps_now(["omnexa_a", "omnexa_b"], confirm_install=1, install_source="local")
		self.assertTrue(result["installed"])
		self.assertEqual(result["installed_now"], ["omnexa_a", "omnexa_b"])
		self.assertEqual(install_site.call_count, 2)

	def test_bulk_update_plan_and_action(self):
		plan = {"eligible": ["omnexa_a", "omnexa_b"], "not_installed": ["omnexa_c"], "blocked": [], "warning": "w"}
		with (
			patch("omnexa_core.omnexa_core.marketplace._bulk_update_plan", return_value=plan),
			patch("omnexa_core.omnexa_core.marketplace._backup_before_install", return_value={"ok": True}),
			patch("omnexa_core.omnexa_core.marketplace._git_update_app_to_ref", return_value=(True, "ok")) as git_update,
			patch("omnexa_core.omnexa_core.marketplace._run_post_bulk_app_change_hardening", return_value={"ok": True, "build_ok": True, "sync_ok": True}),
			patch.object(frappe, "only_for"),
			patch.object(frappe, "clear_cache"),
			patch.object(frappe, "local", SimpleNamespace(site="test.local", flags=SimpleNamespace(in_test=True)), create=True),
		):
			result = bulk_update_apps_now(["omnexa_a", "omnexa_b"], confirm_update=1, update_source="github")
		self.assertTrue(result["updated"])
		self.assertEqual(result["updated_now"], ["omnexa_a", "omnexa_b"])
		self.assertEqual(git_update.call_count, 2)
