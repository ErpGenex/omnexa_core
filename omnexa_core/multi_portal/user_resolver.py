# Copyright (c) 2026, ErpGenEx
"""Resolve Frappe user roles to multi-portal application + role identifiers."""

from __future__ import annotations

import frappe

from omnexa_core.multi_portal import APPLICATION_APP_MAP, VALID_APPLICATIONS, resolve_application
from omnexa_core.multi_portal.config_loader import ConfigLoader


FRAPPE_ROLE_PORTAL_MAP: dict[str, dict[str, str]] = {
	"healthcare": {
		"healthcare_user": "healthcare_receptionist",
		"physician": "healthcare_doctor",
		"nursing_user": "healthcare_nurse",
		"laboratory_user": "healthcare_lab_technician",
		"radiology_user": "healthcare_radiology"
	},
	"education": {
		"education_manager": "education_principal",
		"education_user": "education_teacher",
		"student": "education_student",
		"parent": "education_parent"
	},
	"commerce": {
		"sales_manager": "commerce_sales",
		"sales_user": "commerce_sales",
		"sales_master_manager": "commerce_sales",
		"stock_user": "commerce_warehouse",
		"stock_manager": "commerce_warehouse",
		"purchase_user": "commerce_purchasing",
		"purchase_manager": "commerce_purchasing",
		"accounts_user": "commerce_finance",
		"accounts_manager": "commerce_finance",
		"hr_user": "commerce_hr",
		"hr_manager": "commerce_hr",
		"customer": "commerce_customer_service",
		"company_admin": "commerce_general_manager",
		"pharma_warehouse_manager": "commerce_warehouse",
		"pharma_quality_manager": "commerce_inventory",
		"pharma_sales_representative": "commerce_sales",
		"pharma_finance_manager": "commerce_finance",
		"pharma_regulatory_officer": "commerce_purchasing",
		"pharma_cold_chain_manager": "commerce_warehouse",
		"trading_customer_portal": "commerce_customer_service",
		"auditor": "commerce_system_administrator",
		"ceo": "commerce_general_manager",
		"chairman": "commerce_general_manager",
		"finance_director": "commerce_finance",
		"hr_director": "commerce_hr",
		"area_manager": "commerce_sales",
		"sales_supervisor": "commerce_sales",
		"customer_service": "commerce_customer_service",
		"treasury": "commerce_finance",
		"cashier": "commerce_pos_cashier",
		"store_keeper": "commerce_warehouse",
		"dispatch": "commerce_warehouse",
		"receiving": "commerce_warehouse",
		"operations_director": "commerce_inventory"}
	}


def _normalize_role(role: str) -> str:
	return role.lower().replace(" ", "_").replace("-", "_")


def _resolve_application_id(application_id: str) -> str:
	return resolve_application(application_id)


def get_user_applications(user: str | None = None) -> list[str]:
	user = user or frappe.session.user
	if user == "Guest":
		return []

	installed = set(frappe.get_installed_apps() or [])
	available = [app_id for app_id in VALID_APPLICATIONS if APPLICATION_APP_MAP.get(app_id) in installed]
	if user == "Administrator" or "System Manager" in frappe.get_roles(user):
		return available

	user_roles = {_normalize_role(role) for role in frappe.get_roles(user)}
	matched: list[str] = []
	loader = ConfigLoader()
	for application_id in available:
		try:
			app_config = loader.load_application_config(application_id)
		except Exception:
			continue
		role_map = FRAPPE_ROLE_PORTAL_MAP.get(application_id, {})
		for role_id in app_config.get("roles", []):
			if _normalize_role(role_id) in user_roles or role_id.split("_", 1)[-1] in user_roles:
				matched.append(application_id)
				break
		if application_id in matched:
			continue
		for frappe_role, portal_role in role_map.items():
			if frappe_role in user_roles and portal_role in app_config.get("roles", []):
				matched.append(application_id)
				break
	return matched or available[:1]


def get_user_primary_application(user: str | None = None) -> str | None:
	applications = get_user_applications(user)
	return applications[0] if applications else None


def get_user_portal_role(user: str | None, application_id: str) -> str | None:
	user = user or frappe.session.user
	if user == "Guest":
		return None

	application_id = _resolve_application_id(application_id)
	loader = ConfigLoader()
	try:
		app_config = loader.load_application_config(application_id)
	except Exception:
		return None

	user_roles = {_normalize_role(role) for role in frappe.get_roles(user)}
	for role_id in app_config.get("roles", []):
		if _normalize_role(role_id) in user_roles:
			return role_id

	role_map = FRAPPE_ROLE_PORTAL_MAP.get(application_id, {})
	for frappe_role, portal_role in role_map.items():
		if frappe_role in user_roles and portal_role in app_config.get("roles", []):
			return portal_role

	if user == "Administrator" or "System Manager" in frappe.get_roles(user):
		roles = app_config.get("roles", [])
		for preferred in (f"{application_id}_system_administrator", f"{application_id}_general_manager"):
			if preferred in roles:
				return preferred
		return roles[0] if roles else None

	return None
