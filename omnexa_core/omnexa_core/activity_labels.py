# Copyright (c) 2026, Omnexa and contributors
# License: MIT

from __future__ import annotations

import frappe

from omnexa_core.omnexa_core.app_visibility import _normalize_company_activity

# Normalized activity key → (English, Arabic)
ACTIVITY_I18N: dict[str, tuple[str, str]] = {
	"General": ("General", "عام"),
	"Healthcare": ("Healthcare", "الرعاية الصحية"),
	"Education": ("Education", "التعليم"),
	"Construction": ("Construction", "المقاولات"),
	"Engineering Consulting": ("Engineering Consulting", "الاستشارات الهندسية"),
	"Financial Services": ("Financial Services", "الخدمات المالية"),
	"Trading": ("Trading", "التجارة"),
	"Manufacturing": ("Manufacturing", "التصنيع"),
	"Agriculture": ("Agriculture", "الزراعة"),
	"Tourism": ("Tourism", "السياحة"),
	"Hotel Assets": ("Hotel Assets", "أصول الفنادق"),
	"Bakeries": ("Bakeries", "المخابز"),
	"Services": ("Services", "الخدمات"),
	"Statutory Audit": ("Statutory Audit", "التدقيق القانوني"),
}


def _is_arabic(lang: str | None) -> bool:
	return (lang or "").lower().startswith("ar")


def get_activity_display_label(activity: str | None, lang: str | None = None) -> str:
	"""Localized short label for a business activity."""
	normalized = _normalize_company_activity(activity)
	en, ar = ACTIVITY_I18N.get(normalized, (normalized, normalized))
	active = (lang or getattr(frappe.local, "lang", None) or "en").lower()
	return ar if _is_arabic(active) else en


def resolve_company_activity_raw(company: str | None) -> str:
	if not company or not frappe.db.exists("Company", company):
		return "General"
	row = frappe.db.get_value(
		"Company",
		company,
		["business_activity", "industry_sector", "production_demo_activity"],
		as_dict=True,
	)
	if not row:
		return "General"
	for key in ("business_activity", "industry_sector", "production_demo_activity"):
		val = (row.get(key) or "").strip()
		if val and val.lower() not in ("", "general"):
			return val
	return "General"


def get_company_activity_info(company: str | None, lang: str | None = None) -> dict:
	raw = resolve_company_activity_raw(company)
	normalized = _normalize_company_activity(raw)
	return {
		"company": company,
		"activity": normalized,
		"activity_raw": raw,
		"label": get_activity_display_label(raw, lang),
	}


def get_companies_activity_map(lang: str | None = None) -> dict[str, dict]:
	out: dict[str, dict] = {}
	for company in frappe.get_all("Company", pluck="name", order_by="name asc"):
		out[company] = get_company_activity_info(company, lang)
	return out


@frappe.whitelist()
def get_company_activity_info_api(company: str | None = None) -> dict:
	return get_company_activity_info(company)
