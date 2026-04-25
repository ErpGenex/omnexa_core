# Copyright (c) 2026, ErpGenEx and contributors
# SPDX-License-Identifier: MIT

import json

from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core import c2_workflow_preflight


class TestC2WorkflowPreflight(FrappeTestCase):
	def test_collect_preflight_shape(self):
		data = c2_workflow_preflight.collect_c2_workflow_preflight()
		self.assertIn("workflow_coverage", data)
		self.assertIn("version_rows_7d", data)
		self.assertIn("documents_touch_30d", data)
		self.assertIsInstance(data["workflow_coverage"], list)
		line = json.dumps(data, default=str)
		self.assertTrue(line)
