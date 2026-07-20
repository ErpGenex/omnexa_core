# Copyright (c) 2026, Omnexa and contributors
# License: MIT

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_core.core_gap_register import GAPS_TOTAL, get_gap_status
from omnexa_core.core_global_benchmark import get_global_core_score


class TestCoreGlobalBenchmark(FrappeTestCase):
	def test_gap_register_structure(self):
		status = get_gap_status()
		self.assertEqual(status["gaps_total"], GAPS_TOTAL)
		self.assertEqual(len(status["gaps"]), GAPS_TOTAL)
		self.assertIn("gaps_open", status)
		self.assertEqual(status["app"], "omnexa_core")

	def test_global_core_score_shape(self):
		score = get_global_core_score()
		self.assertEqual(score["app"], "omnexa_core")
		self.assertIn("weighted_score", score)
		self.assertIn("global_leader_gate", score)
		self.assertIn("matrix", score)
		self.assertTrue(score["weighted_score"] > 0)

	def test_export_core_global_audit(self):
		frappe.set_user("Administrator")
		from omnexa_core.core_assessment import export_core_global_audit

		out = export_core_global_audit()
		self.assertIn("path", out)
		self.assertIn("weighted_score", out)
