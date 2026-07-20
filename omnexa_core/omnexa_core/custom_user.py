# Copyright (c) 2026, ErpGenEx and contributors
# SPDX-License-Identifier: MIT
"""User overrides: reduce Error Log noise when SMTP is not configured.

Frappe's ``User.send_password_notification`` logs ``Unable to send new password notification``
on ``OutgoingEmailError`` after already showing a desk alert. In development (or when opted in
via site config) we skip writing that Error Log row so weekly ops health / Error budget is not
polluted.

Site config (optional, non–dev environments)::

    "omnexa_suppress_smtp_password_error_log": 1
"""

from __future__ import annotations

import frappe
from frappe.core.doctype.user.user import User

_SMTP_PASSWORD_NOTIFICATION_TITLE = "Unable to send new password notification"


def _suppress_smtp_password_notification_error_log() -> bool:
	if frappe.conf.get("omnexa_suppress_smtp_password_error_log"):
		return True
	return bool(frappe.conf.get("developer_mode"))


class CustomUser(User):
	def log_error(self, title=None, message=None, *, defer_insert=False):
		t = (title or "").strip()
		if t == _SMTP_PASSWORD_NOTIFICATION_TITLE and _suppress_smtp_password_notification_error_log():
			return None
		return super().log_error(title=title, message=message, defer_insert=defer_insert)
