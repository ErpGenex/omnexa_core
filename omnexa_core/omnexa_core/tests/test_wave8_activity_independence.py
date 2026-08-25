# Copyright (c) 2026, ErpGenEx
import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core.activity_registry import (
	ACTIVITIES,
	FINANCIAL_CORE_APPS,
	INTEGRATION_COMMANDS,
	get_activity,
	resolve_company_activity,
)
from omnexa_core.omnexa_core.integration_bus import dispatch_command, list_integration_commands
from omnexa_core.omnexa_core.isolation_middleware import get_isolation_context
from omnexa_core.omnexa_core.wave8_certification import certify_wave8, wave8_gates


class TestActivityRegistry(FrappeTestCase):
	def test_activities_cover_major_verticals(self):
		self.assertIn("Healthcare", ACTIVITIES)
		self.assertIn("Construction", ACTIVITIES)
		self.assertIn("Financial Services", ACTIVITIES)
		self.assertIn("omnexa_healthcare", ACTIVITIES["Healthcare"].vertical_apps)

	def test_financial_core_apps(self):
		self.assertIn("omnexa_accounting", FINANCIAL_CORE_APPS)
		self.assertIn("omnexa_reporting_compliance", FINANCIAL_CORE_APPS)

	def test_resolve_company_activity(self):
		company = frappe.db.get_value("Company", {}, "name")
		if not company:
			self.skipTest("no company")
		spec = resolve_company_activity(company)
		self.assertTrue(spec.id)

	def test_isolation_context(self):
		ctx = get_isolation_context()
		self.assertIsInstance(ctx.allowed_apps, frozenset)
		self.assertTrue(ctx.activity_id)


class TestIntegrationBus(FrappeTestCase):
	def test_commands_registered(self):
		commands = set(list_integration_commands())
		self.assertTrue(INTEGRATION_COMMANDS.issubset(commands))

	def test_financial_snapshot(self):
		company = frappe.db.get_value("Company", {}, "name")
		if not company:
			self.skipTest("no company")
		out = dispatch_command(
			"reporting.get_financial_snapshot",
			{"company": company},
			source_app="omnexa_core",
			idempotency_key="test-fin-snap",
		)
		self.assertTrue(out.ok)
		self.assertEqual(out.data.get("company"), company)

	def test_idempotency(self):
		company = frappe.db.get_value("Company", {}, "name")
		if not company:
			self.skipTest("no company")
		payload = {"company": company}
		first = dispatch_command(
			"reporting.get_inventory_snapshot",
			payload,
			source_app="omnexa_core",
			idempotency_key="test-inv-snap",
		)
		second = dispatch_command(
			"reporting.get_inventory_snapshot",
			payload,
			source_app="omnexa_core",
			idempotency_key="test-inv-snap",
		)
		self.assertTrue(second.idempotent_hit)
		self.assertEqual(first.reference_name, second.reference_name)


class TestWave8Certification(FrappeTestCase):
	def test_wave8_gates_omnexa_core(self):
		gates = wave8_gates("omnexa_core")
		self.assertTrue(gates["activity_registry_aligned"])
		self.assertTrue(gates["integration_bus_ready"])

	def test_certify_wave8_core(self):
		cert = certify_wave8("omnexa_core")
		self.assertIn("wave8_gates", cert)
		self.assertTrue(cert["wave8_integration"])
		self.assertIn("omnexa_accounting", cert.get("financial_core_apps") or [])

	def test_healthcare_in_registry(self):
		spec = get_activity("Healthcare")
		self.assertEqual(spec.label_ar, "الرعاية الصحية")
