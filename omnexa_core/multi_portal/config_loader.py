# Copyright (c) 2026, ErpGenEx
"""Load multi-portal JSON configuration from omnexa_core app path."""

from __future__ import annotations

import json
import os
from typing import Any

import frappe


def get_config_root() -> str:
	return frappe.get_app_path("omnexa_core", "config", "multi_portal")


class ConfigLoader:
	"""Loads application and role configuration files."""

	def __init__(self, config_path: str | None = None):
		self.config_path = config_path or get_config_root()

	def load_application_config(self, application_id: str) -> dict[str, Any]:
		config_file = os.path.join(self.config_path, f"{application_id}_application_config.json")
		if not os.path.isfile(config_file):
			frappe.throw(f"Application config not found: {application_id}")
		with open(config_file, encoding="utf-8") as handle:
			return json.load(handle)

	def load_role_config(self, application_id: str, role_id: str) -> dict[str, Any]:
		config_file = os.path.join(self.config_path, "roles", f"{role_id}_role_config.json")
		if not os.path.isfile(config_file):
			frappe.throw(f"Role config not found: {role_id}")
		with open(config_file, encoding="utf-8") as handle:
			return json.load(handle)

	def load_theme_config(self, application_id: str) -> dict[str, str]:
		app_config = self.load_application_config(application_id)
		return {
			"primary": app_config.get("primary_color", "#2196F3"),
			"secondary": app_config.get("secondary_color", "#1976D2"),
			"accent": app_config.get("accent_color", "#FF4081")}

	def load_shared_design_system(self) -> dict[str, Any]:
		config_file = os.path.join(self.config_path, "shared_design_system.json")
		if not os.path.isfile(config_file):
			return {}
		with open(config_file, encoding="utf-8") as handle:
			return json.load(handle)

	def load_url_structure(self) -> dict[str, Any]:
		config_file = os.path.join(self.config_path, "url_structure_config.json")
		if not os.path.isfile(config_file):
			return {}
		with open(config_file, encoding="utf-8") as handle:
			return json.load(handle)
