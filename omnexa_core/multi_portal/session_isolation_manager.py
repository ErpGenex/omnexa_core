# Copyright (c) 2026, ErpGenEx
"""Session isolation using Frappe cache — one active portal application per session."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

import frappe


class SessionIsolationManager:
	"""Tracks portal application context per user session."""

	def __init__(self, session_timeout: int = 1800):
		self.session_timeout = session_timeout

	def _session_key(self, session_id: str) -> str:
		return f"multi_portal:session:{session_id}"

	def _user_sessions_key(self, user: str) -> str:
		return f"multi_portal:user_sessions:{user}"

	def create_session(self, user: str, application: str) -> str:
		self._invalidate_user_sessions(user)
		session_id = str(uuid4())
		session_data = {
			"user": user,
			"application": application,
			"created_at": datetime.now().isoformat(),
			"last_activity": datetime.now().isoformat(),
			"expires_at": (datetime.now() + timedelta(seconds=self.session_timeout)).isoformat()
	}
		frappe.cache.set_value(self._session_key(session_id), session_data, expires_in_sec=self.session_timeout)
		user_sessions = frappe.cache.get_value(self._user_sessions_key(user)) or []
		user_sessions.append(session_id)
		frappe.cache.set_value(self._user_sessions_key(user), user_sessions, expires_in_sec=self.session_timeout)
		return session_id

	def validate_session_isolation(self, request: dict[str, Any], application: str) -> bool:
		session_id = request.get("session_id")
		if not session_id:
			return False

		session = frappe.cache.get_value(self._session_key(session_id))
		if not session:
			return False

		expires_at = datetime.fromisoformat(session["expires_at"])
		if datetime.now() > expires_at:
			self.invalidate_session(session_id)
			return False

		if session.get("application") != application:
			return False

		session["last_activity"] = datetime.now().isoformat()
		frappe.cache.set_value(self._session_key(session_id), session, expires_in_sec=self.session_timeout)
		return True

	def invalidate_session(self, session_id: str) -> None:
		session = frappe.cache.get_value(self._session_key(session_id))
		if session:
			user = session.get("user")
			if user:
				user_sessions = frappe.cache.get_value(self._user_sessions_key(user)) or []
				user_sessions = [sid for sid in user_sessions if sid != session_id]
				frappe.cache.set_value(self._user_sessions_key(user), user_sessions, expires_in_sec=self.session_timeout)
		frappe.cache.delete_value(self._session_key(session_id))

	def _invalidate_user_sessions(self, user: str) -> None:
		for session_id in frappe.cache.get_value(self._user_sessions_key(user)) or []:
			frappe.cache.delete_value(self._session_key(session_id))
		frappe.cache.delete_value(self._user_sessions_key(user))

	def get_session_info(self, session_id: str) -> dict[str, Any] | None:
		return frappe.cache.get_value(self._session_key(session_id))

	def get_active_sessions_count(self) -> int:
		return 0
