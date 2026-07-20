# Copyright (c) 2026, ErpGenEx
from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core.infra_parity import preview_infra


class TestSapParityInfra(FrappeTestCase):
	def test_eng_stub_bridge(self):
		out = preview_infra("eng_document_control")
		self.assertIn("consulting_bridge_available", out["kpi"])

	def test_n8n_pending(self):
		out = preview_infra("n8n_bridge", pending_events=5, failed_deliveries=1)
		self.assertEqual(out["kpi"]["pending_events"], 5)

	def test_backup_sla(self):
		out = preview_infra("backup", hours_since_backup=12, backup_sla_hours=24)
		self.assertTrue(out["kpi"]["within_sla"])
