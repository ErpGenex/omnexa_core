# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import re
from copy import deepcopy

import frappe
from frappe import _


PROMPT_INJECTION_PATTERNS = [
	r"ignore\s+all\s+previous\s+instructions",
	r"reveal\s+(system|developer)\s+prompt",
	r"bypass\s+(security|guardrails?)",
	r"tool\s*:\s*shell",
]


def get_ai_inventory() -> list[dict]:
	raw = (frappe.get_conf() or {}).get("omnexa_ai_inventory") or []
	if not isinstance(raw, list):
		return []
	out: list[dict] = []
	for row in raw:
		if not isinstance(row, dict):
			continue
		model_key = str(row.get("model_key") or "").strip()
		if not model_key:
			continue
		out.append(
			{
				"model_key": model_key,
				"data_classes": [str(x).strip() for x in (row.get("data_classes") or []) if str(x).strip()],
				"tenants": [str(x).strip() for x in (row.get("tenants") or []) if str(x).strip()],
			}
		)
	return out


def is_ai_feature_opted_in(tenant: str, feature_key: str) -> bool:
	tenant = (tenant or "").strip()
	feature_key = (feature_key or "").strip()
	if not tenant or not feature_key:
		return False
	opt_in_map = (frappe.get_conf() or {}).get("omnexa_ai_tenant_opt_in") or {}
	if not isinstance(opt_in_map, dict):
		return False
	allowed = opt_in_map.get(feature_key) or []
	if allowed == "*":
		return True
	if isinstance(allowed, str):
		allowed = [x.strip() for x in allowed.split(",") if x.strip()]
	if not isinstance(allowed, (list, tuple, set)):
		return False
	return tenant in {str(x).strip() for x in allowed if str(x).strip()}


def assert_prompt_is_safe(prompt: str):
	text = (prompt or "").strip()
	if not text:
		return
	lower_text = text.lower()
	for pattern in PROMPT_INJECTION_PATTERNS:
		if re.search(pattern, lower_text):
			frappe.throw(
				_("Prompt blocked by AI safety policy (possible prompt injection)."),
				title=_("AI Safety"),
			)


def assert_no_cross_tenant_retrieval(records: list[dict], expected_tenant: str, tenant_field: str = "tenant"):
	expected_tenant = (expected_tenant or "").strip()
	if not expected_tenant:
		frappe.throw(_("Expected tenant is required."), title=_("Tenant Isolation"))
	for row in records or []:
		if not isinstance(row, dict):
			continue
		if str(row.get(tenant_field) or "").strip() != expected_tenant:
			frappe.throw(_("Cross-tenant retrieval detected and blocked."), title=_("Tenant Isolation"))


def append_model_change_log(
	model_key: str,
	from_version: str,
	to_version: str,
	rollback_version: str,
	change_note: str,
):
	model_key = (model_key or "").strip()
	from_version = (from_version or "").strip()
	to_version = (to_version or "").strip()
	rollback_version = (rollback_version or "").strip()
	if not all([model_key, from_version, to_version, rollback_version]):
		frappe.throw(_("Model key, from/to version, and rollback version are required."), title=_("AI Model Change"))
	if from_version == to_version:
		frappe.throw(_("Model change must move to a different version."), title=_("AI Model Change"))
	store = (frappe.get_conf() or {}).get("omnexa_ai_model_change_log") or []
	if not isinstance(store, list):
		store = []
	store = deepcopy(store)
	store.append(
		{
			"model_key": model_key,
			"from_version": from_version,
			"to_version": to_version,
			"rollback_version": rollback_version,
			"change_note": (change_note or "").strip(),
		}
	)
	frappe.local.conf["omnexa_ai_model_change_log"] = store
	return store[-1]
