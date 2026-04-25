# Copyright (c) 2026, ErpGenEx and contributors
# SPDX-License-Identifier: MIT

from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core.custom_user import CustomUser


class TestCustomUserErrorLogSuppression(FrappeTestCase):
	def _doc(self) -> CustomUser:
		return CustomUser({"doctype": "User", "name": "test_smtp_log@example.com", "email": "test_smtp_log@example.com"})

	def test_suppresses_password_smtp_title_in_developer_mode(self):
		prev_dev = bool(frappe.conf.get("developer_mode"))
		prev_sup = frappe.conf.get("omnexa_suppress_smtp_password_error_log")
		try:
			frappe.conf.developer_mode = 1
			frappe.conf.omnexa_suppress_smtp_password_error_log = 0
			u = self._doc()
			with patch("frappe.log_error") as le:
				u.log_error(title="Unable to send new password notification", message="trace")
				le.assert_not_called()
		finally:
			frappe.conf.developer_mode = prev_dev
			if prev_sup is None:
				frappe.conf.pop("omnexa_suppress_smtp_password_error_log", None)
			else:
				frappe.conf.omnexa_suppress_smtp_password_error_log = prev_sup

	def test_still_logs_when_production_and_no_site_flag(self):
		prev_dev = bool(frappe.conf.get("developer_mode"))
		prev_sup = frappe.conf.get("omnexa_suppress_smtp_password_error_log")
		try:
			frappe.conf.developer_mode = 0
			frappe.conf.omnexa_suppress_smtp_password_error_log = 0
			u = self._doc()
			with patch("frappe.log_error") as le:
				u.log_error(title="Unable to send new password notification", message="trace")
				le.assert_called_once()
		finally:
			frappe.conf.developer_mode = prev_dev
			if prev_sup is None:
				frappe.conf.pop("omnexa_suppress_smtp_password_error_log", None)
			else:
				frappe.conf.omnexa_suppress_smtp_password_error_log = prev_sup

	def test_suppresses_when_site_config_flag_set(self):
		prev_dev = bool(frappe.conf.get("developer_mode"))
		prev_sup = frappe.conf.get("omnexa_suppress_smtp_password_error_log")
		try:
			frappe.conf.developer_mode = 0
			frappe.conf.omnexa_suppress_smtp_password_error_log = 1
			u = self._doc()
			with patch("frappe.log_error") as le:
				u.log_error(title="Unable to send new password notification", message="trace")
				le.assert_not_called()
		finally:
			frappe.conf.developer_mode = prev_dev
			if prev_sup is None:
				frappe.conf.pop("omnexa_suppress_smtp_password_error_log", None)
			else:
				frappe.conf.omnexa_suppress_smtp_password_error_log = prev_sup
