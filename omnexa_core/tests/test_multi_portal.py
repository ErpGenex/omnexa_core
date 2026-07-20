# Copyright (c) 2026, ErpGenEx
"""Tests for Multi-Portal Architecture."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_core.multi_portal.config_loader import ConfigLoader
from omnexa_core.multi_portal.portal_factory import PortalFactory
from omnexa_core.multi_portal.portal_isolation_middleware import PortalIsolationMiddleware
from omnexa_core.multi_portal.serialization import to_serializable
from omnexa_core.multi_portal.user_resolver import get_user_applications, get_user_portal_role


class TestMultiPortal(FrappeTestCase):
	def test_config_loader_reads_healthcare_application(self):
		loader = ConfigLoader()
		config = loader.load_application_config("healthcare")
		self.assertEqual(config["application_id"], "healthcare")
		self.assertIn("healthcare_doctor", config.get("roles", []))

	def test_config_loader_reads_commerce_role(self):
		loader = ConfigLoader()
		role_config = loader.load_role_config("commerce", "commerce_sales")
		self.assertEqual(role_config["role_id"], "commerce_sales")
		self.assertTrue(role_config.get("dashboard", {}).get("kpis"))

	def test_portal_factory_creates_healthcare_doctor_portal(self):
		factory = PortalFactory()
		portal = factory.create_portal("healthcare", "healthcare_doctor")
		self.assertEqual(portal.config.application_id, "healthcare")
		self.assertEqual(portal.config.role_id, "healthcare_doctor")
		self.assertTrue(portal.sidebar.get("sections"))
		self.assertTrue(portal.dashboard.get("kpis"))

	def test_portal_serialization(self):
		factory = PortalFactory()
		portal = factory.create_portal("education", "education_teacher")
		payload = to_serializable(portal)
		self.assertEqual(payload["config"]["role_id"], "education_teacher")
		self.assertIn("sidebar", payload)

	def test_administrator_resolves_applications(self):
		frappe.set_user("Administrator")
		apps = get_user_applications()
		self.assertTrue(len(apps) >= 1)

	def test_administrator_resolves_healthcare_role(self):
		frappe.set_user("Administrator")
		role = get_user_portal_role("Administrator", "healthcare")
		self.assertTrue(role)
		self.assertTrue(role.startswith("healthcare_"))

	def test_middleware_validates_url_structure(self):
		middleware = PortalIsolationMiddleware()
		self.assertTrue(middleware.validate_url_structure({"path": "/app/healthcare/doctor/dashboard"
	}))
		self.assertFalse(middleware.validate_url_structure({"path": "/app/unknown/page"
	}))

	def test_api_get_available_portals(self):
		frappe.set_user("Administrator")
		from omnexa_core.api.multi_portal import get_available_portals

		result = get_available_portals()
		self.assertIn("applications", result)
		self.assertTrue(isinstance(result["applications"], list))

	def test_api_get_portal_config(self):
		frappe.set_user("Administrator")
		from omnexa_core.api.multi_portal import get_portal_config

		result = get_portal_config("commerce", "commerce_sales")
		self.assertEqual(result["config"]["role_id"], "commerce_sales")

	def test_boot_injection(self):
		from omnexa_core.api.multi_portal import inject_multi_portal_boot

		bootinfo = frappe._dict()
		inject_multi_portal_boot(bootinfo)
		self.assertIn("enabled", bootinfo.multi_portal)
		self.assertIn("applications", bootinfo.multi_portal)

	def test_trading_alias_resolves_to_commerce(self):
		from omnexa_core.multi_portal import resolve_application

		self.assertEqual(resolve_application("trading"), "commerce")

	def test_config_loader_reads_medical_records_role(self):
		loader = ConfigLoader()
		role_config = loader.load_role_config("healthcare", "healthcare_medical_records")
		self.assertEqual(role_config["role_id"], "healthcare_medical_records")

	def test_pharma_role_maps_to_commerce_portal(self):
		from omnexa_core.multi_portal.user_resolver import FRAPPE_ROLE_PORTAL_MAP

		self.assertEqual(FRAPPE_ROLE_PORTAL_MAP["commerce"]["pharma_warehouse_manager"], "commerce_warehouse")

	def test_api_accepts_trading_alias(self):
		frappe.set_user("Administrator")
		from omnexa_core.api.multi_portal import get_portal_config

		result = get_portal_config("trading", "commerce_sales")
		self.assertEqual(result["config"]["application_id"], "commerce")

	def test_trading_workcenter_includes_multi_portal(self):
		frappe.set_user("Administrator")
		from omnexa_trading.trading_portal_catalog import get_workcenter_context

		ctx = get_workcenter_context()
		self.assertTrue(ctx.get("multi_portal", {}).get("enabled"))
