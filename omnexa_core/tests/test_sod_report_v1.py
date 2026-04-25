# Copyright (c) 2026, ErpGenEx and contributors
# SPDX-License-Identifier: MIT

import json

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core.sod_report_v1 import collect_sod_v1_role_conflicts, print_sod_v1_role_conflict_report


class TestSodReportV1(FrappeTestCase):
	def test_collect_returns_list(self):
		out = collect_sod_v1_role_conflicts()
		self.assertIsInstance(out, list)
		for row in out:
			self.assertIn("user", row)
			self.assertIn("role_a", row)
			self.assertIn("role_b", row)

	def test_print_default_report_parses(self):
		line = print_sod_v1_role_conflict_report()
		data = json.loads(line)
		self.assertEqual(data.get("site"), frappe.local.site)
		self.assertIn("conflicts", data)
		self.assertIn("conflict_count", data)
		self.assertEqual(data["conflict_count"], len(data["conflicts"]))
