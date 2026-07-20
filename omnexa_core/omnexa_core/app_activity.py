# Copyright (c) 2026, ErpGenEx
"""Map installed app slugs to business activity labels."""

from __future__ import annotations

import frappe


def activity_for_app(app_slug: str) -> str:
	"""Resolve app activity/domain for marketplace and desk filtering."""
	custom = frappe.conf.get("omnexa_marketplace_activity_map") or {}
	if isinstance(custom, dict):
		val = custom.get(app_slug)
		if isinstance(val, str) and val.strip():
			return val.strip()

	if app_slug.startswith("erpgenex_"):
		return "ErpGenEx"
	parts = [p for p in app_slug.replace("omnexa_", "").split("_") if p]
	if not parts:
		return "General"
	if "finance" in parts:
		return "Finance"
	if "risk" in parts:
		return "Risk"
	if "rental" in parts or "vehicle" in parts:
		return "Mobility"
	if "healthcare" in parts:
		return "Healthcare"
	if "education" in parts:
		return "Education"
	if "nursery" in parts:
		return "Education"
	if "construction" in parts:
		return "Construction"
	if "agriculture" in parts:
		return "Agriculture"
	if "manufacturing" in parts:
		return "Manufacturing"
	if "trading" in parts:
		return "Trading"
	if "tourism" in parts:
		return "Tourism"
	if "restaurant" in parts:
		return "Restaurant"
	if "leasing" in parts:
		return "Leasing"
	if "mortgage" in parts:
		return "Mortgage"
	if "factoring" in parts:
		return "Factoring"
	if "consumer" in parts:
		return "Consumer"
	if "alm" in parts:
		return "Alm"
	if "accounting" in parts:
		return "Accounting"
	if "einvoice" in parts:
		return "Einvoice"
	if "fixed" in parts:
		return "Fixed"
	if "reporting" in parts:
		return "Reporting"
	if "customer" in parts:
		return "Customer"
	if "projects" in parts:
		return "Projects"
	if "statutory" in parts or "audit" in parts:
		return "Audit"
	if app_slug.startswith("omnexa_eng_") or "engineering" in parts:
		return "Engineering"
	if "setup" in parts:
		return "Setup"
	if "experience" in parts:
		return "Experience"
	if "n8n" in parts:
		return "Bridge"
	if "intelligence" in parts:
		return "Intelligence"
	if "hr" in parts:
		return "Hr"
	if "sme" in parts:
		return "Sme"
	if "car_rental" in parts:
		return "Mobility"
	if "services" in parts:
		return "Services"
	return parts[0].capitalize()
