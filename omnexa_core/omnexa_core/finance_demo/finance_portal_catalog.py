# Copyright (c) 2026, ErpGenEx
"""Finance Group portal catalog — single source of truth for finance-demo-hub."""

from __future__ import annotations

import frappe
from frappe.utils import cint

PORTAL_CATALOG: list[dict] = [
	{
		"id": "demo-hub",
		"route": "/app/finance-demo-hub",
		"page": "finance-demo-hub",
		"icon": "🎯",
		"category": "admin",
		"roles": ["System Manager"],
		"label_ar": "مركز الديمو المالي",
		"label_en": "Finance Demo Hub",
	},
	{
		"id": "control-center",
		"route": "/app/finance-control-center",
		"page": "finance-control-center",
		"icon": "🏦",
		"category": "admin",
		"roles": ["System Manager", "Accounts Manager"],
		"label_ar": "مركز التحكم المالي",
		"label_en": "Finance Control Center",
	},
	{
		"id": "fe-exec",
		"route": "/app/fe-executive-dashboard",
		"page": "fe-executive-dashboard",
		"icon": "📊",
		"category": "engine",
		"roles": ["Finance Group Executive"],
		"label_ar": "Finance Engine — تنفيذي",
		"label_en": "Finance Engine Executive",
	},
	{
		"id": "fe-servicing",
		"route": "/app/fe-servicing-portal",
		"page": "fe-servicing-portal",
		"icon": "⚙️",
		"category": "engine",
		"roles": ["Finance Group Executive"],
		"label_ar": "Finance Engine — خدمة",
		"label_en": "Finance Engine Servicing",
	},
	{
		"id": "ce-servicing",
		"route": "/app/ce-servicing-portal",
		"page": "ce-servicing-portal",
		"icon": "🛡️",
		"category": "credit",
		"roles": ["Finance Credit Officer"],
		"label_ar": "Credit Engine — origination",
		"label_en": "Credit Origination",
	},
	{
		"id": "ce-exec",
		"route": "/app/ce-executive-dashboard",
		"page": "ce-executive-dashboard",
		"icon": "📊",
		"category": "credit",
		"roles": ["Finance Credit Officer"],
		"label_ar": "Credit Engine — تنفيذي",
		"label_en": "Credit Engine Executive",
	},
	{
		"id": "rk-servicing",
		"route": "/app/rk-servicing-portal",
		"page": "rk-servicing-portal",
		"icon": "📈",
		"category": "credit",
		"roles": ["Finance Risk Analyst"],
		"label_ar": "Credit Risk — تحليل",
		"label_en": "Credit Risk Analyst",
	},
	{
		"id": "al-servicing",
		"route": "/app/al-servicing-portal",
		"page": "al-servicing-portal",
		"icon": "💹",
		"category": "treasury",
		"roles": ["Finance Treasury Officer"],
		"label_ar": "ALM — خزينة",
		"label_en": "ALM Treasury",
	},
	{
		"id": "cf-servicing",
		"route": "/app/cf-servicing-portal",
		"page": "cf-servicing-portal",
		"icon": "🛒",
		"category": "retail",
		"roles": ["Finance Consumer Officer"],
		"label_ar": "تمويل استهلاكي",
		"label_en": "Consumer Finance",
	},
	{
		"id": "vf-servicing",
		"route": "/app/vf-servicing-portal",
		"page": "vf-servicing-portal",
		"icon": "🚗",
		"category": "retail",
		"roles": ["Finance Auto Officer"],
		"label_ar": "تمويل مركبات",
		"label_en": "Auto Finance",
	},
	{
		"id": "mg-servicing",
		"route": "/app/mg-servicing-portal",
		"page": "mg-servicing-portal",
		"icon": "🏠",
		"category": "retail",
		"roles": ["Finance Mortgage Officer"],
		"label_ar": "رهن عقاري",
		"label_en": "Mortgage Finance",
	},
	{
		"id": "fc-servicing",
		"route": "/app/fc-servicing-portal",
		"page": "fc-servicing-portal",
		"icon": "📄",
		"category": "wholesale",
		"roles": ["Finance Factoring Officer"],
		"label_ar": "تخصيم",
		"label_en": "Factoring",
	},
	{
		"id": "lf-servicing",
		"route": "/app/lf-servicing-portal",
		"page": "lf-servicing-portal",
		"icon": "📦",
		"category": "wholesale",
		"roles": ["Finance Leasing Officer"],
		"label_ar": "تمويل تأجيري",
		"label_en": "Leasing Finance",
	},
	{
		"id": "sr-servicing",
		"route": "/app/sr-servicing-portal",
		"page": "sr-servicing-portal",
		"icon": "🏪",
		"category": "sme",
		"roles": ["Finance SME Officer"],
		"label_ar": "تمويل منشآت",
		"label_en": "SME Finance",
	},
	{
		"id": "mf-servicing",
		"route": "/app/mf-servicing-portal",
		"page": "mf-servicing-portal",
		"icon": "🤝",
		"category": "sme",
		"roles": ["Finance Microfinance Officer"],
		"label_ar": "تمويل متناهي الصغر",
		"label_en": "Microfinance Field",
	},
	{
		"id": "or-grc",
		"route": "/app/or-grc-portal",
		"page": "or-grc-portal",
		"icon": "🛡️",
		"category": "grc",
		"roles": ["Finance GRC Officer"],
		"label_ar": "مخاطر تشغيلية GRC",
		"label_en": "Operational Risk GRC",
	},
	{
		"id": "acct-exec",
		"route": "/app/acct-executive-dashboard",
		"page": "acct-executive-dashboard",
		"icon": "📒",
		"category": "platform",
		"roles": ["Finance Accounting Controller"],
		"label_ar": "محاسبة — تنفيذي",
		"label_en": "Accounting Executive",
	},
	{
		"id": "acct-close",
		"route": "/app/accounting-close-dashboard",
		"page": "accounting-close-dashboard",
		"icon": "🔒",
		"category": "platform",
		"roles": ["Finance Accounting Controller"],
		"label_ar": "إغلاق محاسبي",
		"label_en": "Accounting Close",
	},
]

CATEGORY_LABELS = {
	"admin": {"ar": "الإدارة والتحكم", "en": "Admin & Control"},
	"engine": {"ar": "محرك التمويل", "en": "Finance Engine"},
	"credit": {"ar": "الائتمان والمخاطر", "en": "Credit & Risk"},
	"treasury": {"ar": "الخزينة و ALM", "en": "Treasury & ALM"},
	"retail": {"ar": "تمويل تجزئة", "en": "Retail Lending"},
	"wholesale": {"ar": "جملة وتخصيم", "en": "Wholesale"},
	"sme": {"ar": "منشآت ومتناهي الصغر", "en": "SME & Micro"},
	"grc": {"ar": "حوكمة ومخاطر", "en": "GRC"},
	"platform": {"ar": "منصة المحاسبة", "en": "Accounting Platform"},
}


def _page_exists(page_name: str) -> bool:
	return bool(frappe.db.exists("Page", page_name))


@frappe.whitelist()
def get_portal_catalog(include_missing: int = 0) -> list[dict]:
	out = []
	for row in PORTAL_CATALOG:
		item = dict(row)
		item["exists"] = _page_exists(item["page"])
		if item["exists"] or cint(include_missing):
			out.append(item)
	return out


@frappe.whitelist()
def get_grouped_portal_catalog(include_missing: int = 0) -> list[dict]:
	groups: dict[str, list] = {}
	for row in get_portal_catalog(include_missing=cint(include_missing)):
		groups.setdefault(row["category"], []).append(row)
	result = []
	for cat, portals in groups.items():
		labels = CATEGORY_LABELS.get(cat, {"ar": cat, "en": cat})
		result.append({"category": cat, "label_ar": labels["ar"], "label_en": labels["en"], "portals": portals})
	return result
