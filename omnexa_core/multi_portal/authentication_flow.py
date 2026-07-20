# Copyright (c) 2026, ErpGenEx
"""Authentication flow with dynamic portal routing — complements Frappe login."""

from __future__ import annotations

from typing import Any

import frappe

from omnexa_core.multi_portal.dynamic_portal_loader import DynamicPortalLoader
from omnexa_core.multi_portal.portal_factory import PortalFactory
from omnexa_core.multi_portal.serialization import to_serializable
from omnexa_core.multi_portal.session_isolation_manager import SessionIsolationManager
from omnexa_core.multi_portal.user_resolver import (
	get_user_applications,
	get_user_portal_role,
	get_user_primary_application,
)


class AuthenticationFlow:
	"""Routes authenticated users to their configured portal."""

	def __init__(self):
		self.portal_factory = PortalFactory()
		self.portal_loader = DynamicPortalLoader()
		self.session_manager = SessionIsolationManager()

	def route_current_user(self, application: str | None = None) -> dict[str, Any]:
		user = frappe.session.user
		if not user or user == "Guest":
			return {"success": False, "error": "Not authenticated"
	}

		application = application or get_user_primary_application(user)
		if not application:
			return {"success": False, "error": "No portal application available for user"
	}

		role = get_user_portal_role(user, application)
		if not role:
			return {"success": False, "error": f"No portal role for application: {application}"
	}

		session_id = self.session_manager.create_session(user, application)
		portal = self.portal_loader.load_portal(user, application, role)
		self.portal_loader.preload_critical_modules(application)

		portal_url = self._portal_dashboard_url(application, portal.config.portal_id)
		return {
			"success": True,
			"session_id": session_id,
			"user": user,
			"application": application,
			"role": role,
			"branch": frappe.defaults.get_user_default("Branch") or None,
			"portal_url": portal_url,
			"portal": to_serializable(portal),
			"theme": portal.config.theme
	}

	def switch_application(self, user: str, session_id: str, new_application: str) -> dict[str, Any]:
		if new_application not in get_user_applications(user):
			return {"success": False, "error": "User does not have access to this application"
	}

		self.session_manager.invalidate_session(session_id)
		new_session_id = self.session_manager.create_session(user, new_application)
		role = get_user_portal_role(user, new_application)
		if not role:
			return {"success": False, "error": f"No portal role for application: {new_application}"
	}

		portal = self.portal_loader.load_portal(user, new_application, role)
		portal_url = self._portal_dashboard_url(new_application, portal.config.portal_id)
		return {
			"success": True,
			"session_id": new_session_id,
			"application": new_application,
			"role": role,
			"portal_url": portal_url,
			"portal": to_serializable(portal),
			"theme": portal.config.theme
	}

	def logout(self, session_id: str) -> bool:
		self.session_manager.invalidate_session(session_id)
		return True

	def _portal_dashboard_url(self, application: str, portal_id: str) -> str:
		try:
			app_config = self.portal_factory.config_loader.load_application_config(application)
			for portal in app_config.get("portals", []):
				if portal.get("portal_id") == portal_id:
					return portal.get("url") or f"/app/{application}/{portal_id}/dashboard"
		except Exception:
			pass
		return f"/app/{application}/{portal_id}/dashboard"
