# Copyright (c) 2026, ErpGenEx and contributors
# SPDX-License-Identifier: MIT

import json

from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core import ops_load_critical


class TestOpsLoadCritical(FrappeTestCase):
	def test_collect_critical_load_stats_shape(self):
		data = ops_load_critical.collect_critical_load_stats(iterations=25, include_app_roundtrip=True)
		self.assertIn("db_ping_ms", data)
		self.assertIn("p50", data["db_ping_ms"])
		self.assertIn("p95", data["db_ping_ms"])
		self.assertIn("app_count_user_ms", data)
		line = json.dumps(data, default=str)
		self.assertTrue(line)
