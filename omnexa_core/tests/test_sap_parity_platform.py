# Copyright (c) 2026, ErpGenEx
"""SAP parity wave A — platform audit + tenant license API."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core.platform_audit import get_audit_trail_summary, log_platform_event
from omnexa_core.omnexa_core.platform_api import get_platform_audit_summary, get_tenant_license_snapshot


class TestSapParityPlatform(FrappeTestCase):
	def test_tenant_license_snapshot_core_free(self):
		out = get_tenant_license_snapshot("omnexa_core")
		self.assertIn("apps", out)
		self.assertEqual(out["apps"]["omnexa_core"]["status"], "licensed_free")

	def test_platform_audit_log_roundtrip(self):
		frappe.local.conf["omnexa_feature_flags"] = {"platform_audit_api": True}
		try:
			event_hash = log_platform_event(
				"sap_parity.test",
				"Company",
				"_Test Company",
				action="parity_check",
				company="_Test Company",
				ledger_domain="General",
				payload={"wave": "A"},
			)
			self.assertTrue(event_hash)
			rows = get_audit_trail_summary(limit=5)
			self.assertTrue(any(r.get("event_name") == "sap_parity.test" for r in rows))
			summary = get_platform_audit_summary(limit=5)
			self.assertIn("rows", summary)
		finally:
			frappe.local.conf.pop("omnexa_feature_flags", None)
