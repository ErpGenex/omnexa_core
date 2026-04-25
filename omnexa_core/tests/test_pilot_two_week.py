# Copyright (c) 2026, ErpGenEx and contributors
# SPDX-License-Identifier: MIT

import json
import shutil
from pathlib import Path

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core import pilot_two_week


class TestPilotTwoWeek(FrappeTestCase):
	def test_collect_pilot_metrics_shape(self):
		data = pilot_two_week.collect_pilot_metrics()
		self.assertIsInstance(data, dict)
		for key in (
			"error_log_24h",
			"error_log_7d",
			"error_log_14d",
			"top_error_methods_14d",
			"queues",
			"scheduler",
			"email_queue_by_status_7d",
			"communication_email_sent_7d",
		):
			self.assertIn(key, data)

	def test_deviation_report_empty_pilot(self):
		code = f"EMPTY_{frappe.generate_hash(length=10)}"
		try:
			rep = pilot_two_week.build_pilot_deviation_report(code)
			self.assertEqual(rep["pilot_code"], code)
			self.assertEqual(rep["snapshots_total"], 0)
			self.assertIsNone(rep["week1"])
			self.assertIsNone(rep["week2"])
			self.assertEqual(rep["deviations_numeric"], [])
		finally:
			pdir = pilot_two_week._pilot_dir(code)
			if pdir.is_dir():
				shutil.rmtree(pdir, ignore_errors=True)

	def test_record_two_weeks_and_report_then_cleanup(self):
		code = f"UNIT_{frappe.generate_hash(length=8)}"
		pdir = pilot_two_week._pilot_dir(code)
		try:
			with self.set_user("Administrator"):
				r1 = pilot_two_week.record_pilot_snapshot(pilot_code=code, week_index=1)
				r2 = pilot_two_week.record_pilot_snapshot(pilot_code=code, week_index=2)
			self.assertTrue(Path(r1["path"]).is_file())
			self.assertTrue(Path(r2["path"]).is_file())
			payload = json.loads(Path(r1["path"]).read_text(encoding="utf-8"))
			self.assertEqual(payload["schema"], "omnexa_pilot_snapshot_v1")
			self.assertEqual(payload["week_index"], 1)
			self.assertIn("metrics", payload)
			self.assertIn("frappe_version", payload)

			rep = pilot_two_week.build_pilot_deviation_report(code)
			self.assertGreaterEqual(rep["snapshots_total"], 2)
			self.assertIsNotNone(rep["week1"])
			self.assertIsNotNone(rep["week2"])

			with self.set_user("Administrator"):
				md = pilot_two_week.print_pilot_deviation_report(code)
			self.assertIn(code, md)
			self.assertIn("انحرافات", md)
		finally:
			if pdir.is_dir():
				shutil.rmtree(pdir, ignore_errors=True)

	def test_record_retrospective_pilot_snapshots_and_report(self):
		code = f"RETRO_{frappe.generate_hash(length=8)}"
		pdir = pilot_two_week._pilot_dir(code)
		try:
			with self.set_user("Administrator"):
				out = pilot_two_week.record_retrospective_pilot_snapshots(
					pilot_code=code, start_date="2000-01-01"
				)
			self.assertTrue(out["ok"])
			self.assertIn("w1_path", out)
			self.assertIn("w2_path", out)
			p1 = json.loads(Path(out["w1_path"]).read_text(encoding="utf-8"))
			p2 = json.loads(Path(out["w2_path"]).read_text(encoding="utf-8"))
			self.assertTrue(p1.get("retrospective"))
			self.assertTrue(p2.get("retrospective"))
			self.assertEqual(p1["week_index"], 1)
			self.assertEqual(p2["week_index"], 2)
			self.assertFalse((p1["metrics"].get("retrospective_window") or {}).get("start_exclusive"))
			self.assertTrue((p2["metrics"].get("retrospective_window") or {}).get("start_exclusive"))

			rep = pilot_two_week.build_pilot_deviation_report(code)
			self.assertGreaterEqual(rep["snapshots_total"], 2)
			self.assertIsNotNone(rep["week1"])
			self.assertIsNotNone(rep["week2"])
		finally:
			if pdir.is_dir():
				shutil.rmtree(pdir, ignore_errors=True)

	def test_record_retrospective_pilot_snapshots_and_report(self):
		code = f"RETRO_{frappe.generate_hash(length=8)}"
		pdir = pilot_two_week._pilot_dir(code)
		try:
			with self.set_user("Administrator"):
				out = pilot_two_week.record_retrospective_pilot_snapshots(
					pilot_code=code, start_date="2000-01-01"
				)
			self.assertTrue(out["ok"])
			self.assertIn("w1_path", out)
			self.assertIn("w2_path", out)
			p1 = json.loads(Path(out["w1_path"]).read_text(encoding="utf-8"))
			p2 = json.loads(Path(out["w2_path"]).read_text(encoding="utf-8"))
			self.assertTrue(p1.get("retrospective"))
			self.assertTrue(p2.get("retrospective"))
			self.assertEqual(p1["week_index"], 1)
			self.assertEqual(p2["week_index"], 2)
			self.assertFalse((p1["metrics"].get("retrospective_window") or {}).get("start_exclusive"))
			self.assertTrue((p2["metrics"].get("retrospective_window") or {}).get("start_exclusive"))

			rep = pilot_two_week.build_pilot_deviation_report(code)
			self.assertGreaterEqual(rep["snapshots_total"], 2)
			self.assertIsNotNone(rep["week1"])
			self.assertIsNotNone(rep["week2"])
		finally:
			if pdir.is_dir():
				shutil.rmtree(pdir, ignore_errors=True)
