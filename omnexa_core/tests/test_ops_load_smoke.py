# Copyright (c) 2026, ErpGenEx and contributors
# SPDX-License-Identifier: MIT

import json

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core.ops_load_smoke import print_db_ping_latency_stats


class TestOpsLoadSmoke(FrappeTestCase):
	def test_db_ping_stats_shape(self):
		line = print_db_ping_latency_stats(iterations=20)
		data = json.loads(line)
		self.assertEqual(data.get("site"), frappe.local.site)
		self.assertEqual(data.get("iterations"), 20)
		self.assertIn("total_sec", data)
		self.assertIn("per_query_ms", data)
