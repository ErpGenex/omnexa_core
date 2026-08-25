# Copyright (c) 2026, ErpGenEx
"""Wave 10 — activity bench lane tests on primary site companies."""

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core.activity_bench_ops import develop_erpgenex_lane, inspect_lane
from omnexa_core.omnexa_core.activity_bench_registry import ACTIVITY_BENCH_LANES


class TestActivityBenchLanes(FrappeTestCase):
	def test_registry_has_five_lanes(self):
		self.assertEqual(len(ACTIVITY_BENCH_LANES), 5)

	def test_develop_all_activity_lanes(self):
		for lane in ACTIVITY_BENCH_LANES:
			with self.subTest(activity=lane.activity_id):
				out = develop_erpgenex_lane(lane)
				self.assertTrue(out.get("developed"))
				self.assertTrue(frappe.db.exists("Company", out["company"]))

	def test_lanes_are_activity_scoped(self):
		for lane in ACTIVITY_BENCH_LANES:
			with self.subTest(activity=lane.activity_id):
				develop_erpgenex_lane(lane)
				inspection = inspect_lane(lane)
				self.assertTrue(inspection.get("vertical_apps_installed"), msg=inspection)
				company = inspection.get("company") or {}
				if company:
					activity_fields = [
						v
						for k, v in company.items()
						if k in ("business_activity", "industry_sector", "production_demo_activity") and v
					]
					if activity_fields:
						self.assertIn(lane.activity_id, activity_fields[0])
