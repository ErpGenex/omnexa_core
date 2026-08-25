# Copyright (c) 2026, Omnexa
"""Shared assertions for Wave 7 functional World-Class certification."""

from __future__ import annotations

from frappe.tests.utils import FrappeTestCase

STRUCTURAL_GATES = (
	"session_audit_script",
	"session_scope_test",
	"vertical_dashboard",
	"session_context_live",
)


class WorldClassFunctionalTestMixin:
	app_name: str

	def assert_world_class_certification(self):
		from omnexa_core.omnexa_core.world_class import certify_app

		cert = certify_app(self.app_name)
		for key in STRUCTURAL_GATES:
			self.assertTrue(cert["gates"][key], f"structural gate failed: {key}")
		self.assertGreaterEqual(cert["score_100"], 67, cert)

	def assert_vertical_dashboard_certified(self):
		from importlib import import_module

		mod = import_module(f"{self.app_name}.vertical_dashboard_api")
		out = mod.get_vertical_dashboard()
		self.assertIn("score_100", out)
		self.assertGreaterEqual(out.get("score_100") or 0, 67)
