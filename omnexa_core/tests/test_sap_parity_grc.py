# Copyright (c) 2026, ErpGenEx
from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core.grc_parity import preview_grc


class TestSapParityGrc(FrappeTestCase):
	def test_statutory_audit_evidence_ratio(self):
		out = preview_grc("statutory_audit", open_findings=2, evidence_locked=8, evidence_total=10)
		self.assertEqual(out["kpi"]["evidence_lock_ratio"], 0.8)

	def test_reporting_compliance_coverage(self):
		out = preview_grc("reporting_compliance", controls_total=20, controls_effective=18)
		self.assertEqual(out["kpi"]["control_coverage"], 0.9)

	def test_operational_risk_score(self):
		out = preview_grc("operational_risk", loss_amount=50000, severity="High", open_incidents=1)
		self.assertIn("risk_score_preview", out["kpi"])
