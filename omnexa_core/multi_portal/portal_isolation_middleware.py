# Copyright (c) 2026, ErpGenEx
"""Portal isolation middleware — validates application access without blocking Desk."""

from __future__ import annotations

from typing import Any

import frappe

from omnexa_core.multi_portal import ALL_APPLICATION_KEYS, VALID_APPLICATIONS, resolve_application
from omnexa_core.multi_portal.dynamic_permission_engine import DynamicPermissionEngine
from omnexa_core.multi_portal.session_isolation_manager import SessionIsolationManager
from omnexa_core.multi_portal.user_resolver import get_user_applications, get_user_portal_role


class PortalIsolationMiddleware:
	"""Validates portal isolation for explicit multi-portal API requests."""

	def __init__(self):
		self.session_manager = SessionIsolationManager()
		self.permission_engine = DynamicPermissionEngine()

	def process_request(self, request: dict[str, Any]) -> dict[str, Any] | None:
		try:
			application = self._get_application_from_request(request)
		except ValueError:
			return {"action": "redirect", "url": "/app"}

		if not self._validate_application_isolation(request, application):
			return self._redirect_to_correct_portal(request)

		if not self.session_manager.validate_session_isolation(request, application):
			return {"action": "redirect", "url": "/login"}

		if not self._validate_permissions(request, application):
			return {"action": "redirect", "url": "/unauthorized"}

		return None

	def _get_application_from_request(self, request: dict[str, Any]) -> str:
		path = request.get("path", "")
		parts = [part for part in path.split("/") if part]
		if len(parts) >= 2 and parts[0] == "app" and parts[1] in ALL_APPLICATION_KEYS:
			return resolve_application(parts[1])
		application = request.get("application")
		if application:
			application = resolve_application(application)
			if application in VALID_APPLICATIONS:
				return application
		raise ValueError("Invalid request path format")

	def _validate_application_isolation(self, request: dict[str, Any], application: str) -> bool:
		user = request.get("user") or frappe.session.user
		if not user or user == "Guest":
			return False
		return application in get_user_applications(user)

	def _validate_permissions(self, request: dict[str, Any], application: str) -> bool:
		user = request.get("user") or frappe.session.user
		doctype = request.get("doctype")
		action = request.get("action", "read")
		if not doctype:
			return True

		role_id = request.get("role_id") or get_user_portal_role(user, application)
		if not role_id:
			return False

		return self.permission_engine.validate_permission(user, doctype, action, application, role_id)

	def _redirect_to_correct_portal(self, request: dict[str, Any]) -> dict[str, Any]:
		user = request.get("user") or frappe.session.user
		application = get_user_applications(user)
		if application:
			return {"action": "redirect", "url": f"/app/{application[0]}"}
		return {"action": "redirect", "url": "/app"}

	def validate_url_structure(self, request: dict[str, Any]) -> bool:
		path = request.get("path", "")
		parts = [part for part in path.split("/") if part]
		if len(parts) < 2 or parts[0] != "app":
			return False
		return resolve_application(parts[1]) in VALID_APPLICATIONS
