# Copyright (c) 2026, ErpGenEx

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core.app_uninstall_groups import (
	APP_UNINSTALL_GROUPS,
	get_group_apps,
	get_uninstall_groups_summary,
)


class TestAppUninstallGroups(FrappeTestCase):
	def test_finance_group_contains_verticals(self):
		apps = get_group_apps("finance")
		self.assertIn("omnexa_leasing_finance", apps)
		self.assertIn("omnexa_finance_engine", apps)
		self.assertNotIn("omnexa_accounting", apps)

	def test_summary_returns_all_groups(self):
		frappe.set_user("Administrator")
		rows = get_uninstall_groups_summary()
		self.assertEqual(len(rows), len(APP_UNINSTALL_GROUPS))
		for row in rows:
			self.assertIn("key", row)
			self.assertIn("installed_count", row)
