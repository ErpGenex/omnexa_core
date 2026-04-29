# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import json

import frappe


def _normalize_bool(value) -> bool:
	if isinstance(value, bool):
		return value
	if isinstance(value, (int, float)):
		return value != 0
	if isinstance(value, str):
		return value.strip().lower() in {"1", "true", "yes", "on", "enabled"}
	return False


def get_feature_flags() -> dict:
	conf = frappe.get_conf() or {}
	flags = conf.get("omnexa_feature_flags") or {}
	if isinstance(flags, str) and flags.strip():
		# Support JSON-encoded dict stored in site_config/common_site_config.
		# (bench set-config sometimes persists dicts as JSON strings)
		try:
			parsed = json.loads(flags)
			if isinstance(parsed, dict):
				flags = parsed
		except Exception:
			return {}
	if not isinstance(flags, dict):
		return {}
	return flags


def is_feature_enabled(flag_name: str, default: bool = False) -> bool:
	flags = get_feature_flags()
	if flag_name not in flags:
		return default
	return _normalize_bool(flags.get(flag_name))


def get_enabled_modules() -> set[str]:
	conf = frappe.get_conf() or {}
	raw = conf.get("omnexa_enabled_modules") or []
	if isinstance(raw, str):
		raw = [x.strip() for x in raw.split(",") if x.strip()]
	if not isinstance(raw, (list, tuple, set)):
		return set()
	return {str(x).strip().lower() for x in raw if str(x).strip()}


def is_module_enabled(module_key: str, default: bool = True) -> bool:
	enabled = get_enabled_modules()
	if not enabled:
		return default
	return module_key.strip().lower() in enabled
