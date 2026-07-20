# Copyright (c) 2026, ErpGenEx
"""Whitelisted API for Multi-Portal Architecture."""

from __future__ import annotations

import frappe

from omnexa_core.multi_portal import ALL_APPLICATION_KEYS, VALID_APPLICATIONS, resolve_application
from omnexa_core.multi_portal.authentication_flow import AuthenticationFlow
from omnexa_core.multi_portal.config_loader import ConfigLoader
from omnexa_core.multi_portal.dynamic_portal_loader import DynamicPortalLoader
from omnexa_core.multi_portal.portal_factory import PortalFactory
from omnexa_core.multi_portal.portal_isolation_middleware import PortalIsolationMiddleware
from omnexa_core.multi_portal.serialization import to_serializable
from omnexa_core.multi_portal.user_resolver import get_user_applications, get_user_portal_role


def _validate_application(application: str) -> str:
	application = resolve_application((application or "").strip().lower())
	if application not in VALID_APPLICATIONS:
		frappe.throw(f"Unknown application: {application}")
	return application


@frappe.whitelist()
def get_portal_config(application: str, role: str | None = None) -> dict:
	"""Return portal configuration for an application and optional role."""
	application = _validate_application(application)
	role = (role or get_user_portal_role(frappe.session.user, application) or "").strip()
	if not role:
		frappe.throw(f"No portal role resolved for application: {application}")

	factory = PortalFactory()
	portal = factory.create_portal(application, role)
	return to_serializable(portal)


@frappe.whitelist()
def load_portal(user: str | None = None, application: str | None = None, role: str | None = None) -> dict:
	"""Load a cached portal instance for the current or specified user."""
	user = user or frappe.session.user
	if user != frappe.session.user and "System Manager" not in frappe.get_roles():
		frappe.throw("Not permitted", frappe.PermissionError)

	application = _validate_application(application or "")
	role = (role or get_user_portal_role(user, application) or "").strip()
	if not role:
		frappe.throw(f"No portal role resolved for application: {application}")

	loader = DynamicPortalLoader()
	portal = loader.load_portal(user, application, role)
	return to_serializable(portal)


@frappe.whitelist()
def route_user_portal(application: str | None = None) -> dict:
	"""Route the current authenticated user to their portal."""
	flow = AuthenticationFlow()
	if application:
		application = _validate_application(application)
	return flow.route_current_user(application)


@frappe.whitelist()
def switch_portal_application(application: str, session_id: str) -> dict:
	"""Switch the current user to another portal application."""
	application = _validate_application(application)
	flow = AuthenticationFlow()
	return flow.switch_application(frappe.session.user, session_id, application)


@frappe.whitelist()
def get_available_portals() -> dict:
	"""List applications and roles available to the current user."""
	factory = PortalFactory()
	user = frappe.session.user
	applications = get_user_applications(user)
	result = []
	for application_id in applications:
		roles = factory.get_available_roles(application_id)
		resolved_role = get_user_portal_role(user, application_id)
		app_config = factory.config_loader.load_application_config(application_id)
		result.append(
			{
				"application_id": application_id,
				"application_name": app_config.get("application_name"),
				"base_url": app_config.get("base_url"),
				"theme": factory.config_loader.load_theme_config(application_id),
				"roles": roles,
				"resolved_role": resolved_role,
				"portals": app_config.get("portals", []),
			}
		)
	return {"applications": result, "design_system": ConfigLoader().load_shared_design_system()}


@frappe.whitelist()
def validate_portal_request(path: str, doctype: str | None = None, action: str = "read", session_id: str | None = None) -> dict:
	"""Validate portal isolation for a request path (diagnostic / pre-flight)."""
	middleware = PortalIsolationMiddleware()
	request = {
		"user": frappe.session.user,
		"path": path,
		"doctype": doctype,
		"action": action,
		"session_id": session_id,
	}
	redirect = middleware.process_request(request)
	return {
		"allowed": redirect is None,
		"redirect": redirect,
		"url_valid": middleware.validate_url_structure(request),
	}


def inject_multi_portal_boot(bootinfo) -> None:
	"""Inject lightweight multi-portal metadata into Desk boot (non-breaking)."""
	try:
		factory = PortalFactory()
		applications = factory.get_available_applications()
		user_apps = get_user_applications()
		bootinfo.multi_portal = {
			"enabled": bool(applications),
			"applications": applications,
			"user_applications": user_apps,
			"primary_application": user_apps[0] if user_apps else None,
			"design_system": ConfigLoader().load_shared_design_system(),
		}
	except Exception:
		bootinfo.multi_portal = {"enabled": False, "applications": [], "user_applications": []}
