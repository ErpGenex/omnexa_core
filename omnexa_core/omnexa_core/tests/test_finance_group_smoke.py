# Copyright (c) 2026, ErpGenEx
import unittest


class TestFinanceGroupSmoke(unittest.TestCase):
	def test_finance_group_smoke_audit(self):
		from omnexa_core.omnexa_core.finance_demo.finance_group_smoke import run_finance_group_smoke_audit

		report = run_finance_group_smoke_audit(repair_microfinance=1)
		self.assertGreaterEqual(report["apps_passed"], 12, report.get("failed"))
		if report.get("failed"):
			for row in report["failed"]:
				if row["app"] == "omnexa_sme_microfinance":
					self.assertGreaterEqual(row["workspace_links"], 25, row)
