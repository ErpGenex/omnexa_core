# Copyright (c) 2026, ErpGenEx
"""Finance Group portal catalog — single source of truth for finance-demo-hub."""

from __future__ import annotations

import frappe
from frappe.utils import cint

from omnexa_core.omnexa_core.finance_demo.finance_app_registry import FINANCE_APP_REGISTRY, get_logo_url

_PAGE_APP: dict[str, str] = {}
for _row in FINANCE_APP_REGISTRY:
	_PAGE_APP[_row["exec_page"]] = _row["app"]
	_PAGE_APP[_row["serv_page"]] = _row["app"]

PORTAL_CATALOG: list[dict] = [
	{
		"id": "demo-hub",
		"route": "/app/finance-demo-hub",
		"page": "finance-demo-hub",
		"icon": "🎯",
		"category": "admin",
		"roles": ["System Manager"],
		"label_ar": "مركز تجربة المجموعة المالية",
		"label_en": "Finance Demo Hub",
	},
	{
		"id": "finance-group",
		"route": "/app/finance_group",
		"page": "Finance Group",
		"page_type": "Workspace",
		"icon": "🏦",
		"category": "admin",
		"roles": ["System Manager"],
		"label_ar": "المجموعة المالية البنكية",
		"label_en": "Finance Group Home",
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
		"app": "omnexa_finance_engine",
		"icon": "📊",
		"category": "engine",
		"roles": ["Finance Group Executive"],
		"label_ar": "FinanceCore — لوحة تنفيذية",
		"label_en": "FinanceCore Executive",
	},
	{
		"id": "fe-servicing",
		"route": "/app/fe-servicing-portal",
		"page": "fe-servicing-portal",
		"app": "omnexa_finance_engine",
		"icon": "⚙️",
		"category": "engine",
		"roles": ["Finance Group Executive"],
		"label_ar": "FinanceCore — بوابة الخدمة",
		"label_en": "FinanceCore Servicing",
	},
	{
		"id": "ce-exec",
		"route": "/app/ce-executive-dashboard",
		"page": "ce-executive-dashboard",
		"app": "omnexa_credit_engine",
		"icon": "📊",
		"category": "credit",
		"roles": ["Finance Credit Officer"],
		"label_ar": "CreditPulse — لوحة تنفيذية",
		"label_en": "CreditPulse Executive",
	},
	{
		"id": "ce-servicing",
		"route": "/app/ce-servicing-portal",
		"page": "ce-servicing-portal",
		"app": "omnexa_credit_engine",
		"icon": "🛡️",
		"category": "credit",
		"roles": ["Finance Credit Officer"],
		"label_ar": "CreditPulse — منشأة ائتمان",
		"label_en": "Credit Origination",
	},
	{
		"id": "rk-exec",
		"route": "/app/rk-executive-dashboard",
		"page": "rk-executive-dashboard",
		"app": "omnexa_credit_risk",
		"icon": "📊",
		"category": "credit",
		"roles": ["Finance Risk Analyst"],
		"label_ar": "RiskGuard — لوحة تنفيذية",
		"label_en": "RiskGuard Executive",
	},
	{
		"id": "rk-servicing",
		"route": "/app/rk-servicing-portal",
		"page": "rk-servicing-portal",
		"app": "omnexa_credit_risk",
		"icon": "📈",
		"category": "credit",
		"roles": ["Finance Risk Analyst"],
		"label_ar": "RiskGuard — تحليل مخاطر",
		"label_en": "Credit Risk Analyst",
	},
	{
		"id": "al-exec",
		"route": "/app/al-executive-dashboard",
		"page": "al-executive-dashboard",
		"app": "omnexa_alm",
		"icon": "📊",
		"category": "treasury",
		"roles": ["Finance Treasury Officer"],
		"label_ar": "TreasuryALM — لوحة تنفيذية",
		"label_en": "TreasuryALM Executive",
	},
	{
		"id": "al-servicing",
		"route": "/app/al-servicing-portal",
		"page": "al-servicing-portal",
		"app": "omnexa_alm",
		"icon": "💹",
		"category": "treasury",
		"roles": ["Finance Treasury Officer"],
		"label_ar": "TreasuryALM — خزينة",
		"label_en": "ALM Treasury",
	},
	{
		"id": "cf-exec",
		"route": "/app/cf-executive-dashboard",
		"page": "cf-executive-dashboard",
		"app": "omnexa_consumer_finance",
		"icon": "📊",
		"category": "retail",
		"roles": ["Finance Consumer Officer"],
		"label_ar": "RetailLend — لوحة تنفيذية",
		"label_en": "RetailLend Executive",
	},
	{
		"id": "cf-servicing",
		"route": "/app/cf-servicing-portal",
		"page": "cf-servicing-portal",
		"app": "omnexa_consumer_finance",
		"icon": "🛒",
		"category": "retail",
		"roles": ["Finance Consumer Officer"],
		"label_ar": "RetailLend — تمويل استهلاكي",
		"label_en": "Consumer Finance",
	},
	{
		"id": "vf-exec",
		"route": "/app/vf-executive-dashboard",
		"page": "vf-executive-dashboard",
		"app": "omnexa_vehicle_finance",
		"icon": "📊",
		"category": "retail",
		"roles": ["Finance Auto Officer"],
		"label_ar": "AutoLend — لوحة تنفيذية",
		"label_en": "AutoLend Executive",
	},
	{
		"id": "vf-servicing",
		"route": "/app/vf-servicing-portal",
		"page": "vf-servicing-portal",
		"app": "omnexa_vehicle_finance",
		"icon": "🚗",
		"category": "retail",
		"roles": ["Finance Auto Officer"],
		"label_ar": "AutoLend — تمويل مركبات",
		"label_en": "Auto Finance",
	},
	{
		"id": "mg-exec",
		"route": "/app/mg-executive-dashboard",
		"page": "mg-executive-dashboard",
		"app": "omnexa_mortgage_finance",
		"icon": "📊",
		"category": "retail",
		"roles": ["Finance Mortgage Officer"],
		"label_ar": "HomeLend — لوحة تنفيذية",
		"label_en": "HomeLend Executive",
	},
	{
		"id": "mg-servicing",
		"route": "/app/mg-servicing-portal",
		"page": "mg-servicing-portal",
		"app": "omnexa_mortgage_finance",
		"icon": "🏠",
		"category": "retail",
		"roles": ["Finance Mortgage Officer"],
		"label_ar": "HomeLend — رهن عقاري",
		"label_en": "Mortgage Finance",
	},
	{
		"id": "fc-exec",
		"route": "/app/fc-executive-dashboard",
		"page": "fc-executive-dashboard",
		"app": "omnexa_factoring",
		"icon": "📊",
		"category": "wholesale",
		"roles": ["Finance Factoring Officer"],
		"label_ar": "FactorFlow — لوحة تنفيذية",
		"label_en": "FactorFlow Executive",
	},
	{
		"id": "fc-servicing",
		"route": "/app/fc-servicing-portal",
		"page": "fc-servicing-portal",
		"app": "omnexa_factoring",
		"icon": "📄",
		"category": "wholesale",
		"roles": ["Finance Factoring Officer"],
		"label_ar": "FactorFlow — تخصيم",
		"label_en": "Factoring",
	},
	{
		"id": "lf-exec",
		"route": "/app/lf-executive-dashboard",
		"page": "lf-executive-dashboard",
		"app": "omnexa_leasing_finance",
		"icon": "📊",
		"category": "wholesale",
		"roles": ["Finance Leasing Officer"],
		"label_ar": "LeaseMaster — لوحة تنفيذية",
		"label_en": "LeaseMaster Executive",
	},
	{
		"id": "lf-servicing",
		"route": "/app/lf-servicing-portal",
		"page": "lf-servicing-portal",
		"app": "omnexa_leasing_finance",
		"icon": "📦",
		"category": "wholesale",
		"roles": ["Finance Leasing Officer"],
		"label_ar": "LeaseMaster — تمويل تأجيري",
		"label_en": "Leasing Finance",
	},
	{
		"id": "sr-exec",
		"route": "/app/sr-executive-dashboard",
		"page": "sr-executive-dashboard",
		"app": "omnexa_sme_retail_finance",
		"icon": "📊",
		"category": "sme",
		"roles": ["Finance SME Officer"],
		"label_ar": "SMECapital — لوحة تنفيذية",
		"label_en": "SMECapital Executive",
	},
	{
		"id": "sr-servicing",
		"route": "/app/sr-servicing-portal",
		"page": "sr-servicing-portal",
		"app": "omnexa_sme_retail_finance",
		"icon": "🏪",
		"category": "sme",
		"roles": ["Finance SME Officer"],
		"label_ar": "SMECapital — تمويل منشآت",
		"label_en": "SME Finance",
	},
	{
		"id": "mf-exec",
		"route": "/app/mf-executive-dashboard",
		"page": "mf-executive-dashboard",
		"app": "omnexa_sme_microfinance",
		"icon": "📊",
		"category": "sme",
		"roles": ["Finance Microfinance Officer"],
		"label_ar": "MicroCapital — لوحة تنفيذية",
		"label_en": "MicroCapital Executive",
	},
	{
		"id": "mf-servicing",
		"route": "/app/mf-servicing-portal",
		"page": "mf-servicing-portal",
		"app": "omnexa_sme_microfinance",
		"icon": "🤝",
		"category": "sme",
		"roles": ["Finance Microfinance Officer"],
		"label_ar": "MicroCapital — ميداني",
		"label_en": "Microfinance Field",
	},
	{
		"id": "or-exec",
		"route": "/app/or-executive-dashboard",
		"page": "or-executive-dashboard",
		"app": "omnexa_operational_risk",
		"icon": "📊",
		"category": "grc",
		"roles": ["Finance GRC Officer"],
		"label_ar": "OpRisk — لوحة تنفيذية",
		"label_en": "OpRisk Executive",
	},
	{
		"id": "or-grc",
		"route": "/app/or-grc-portal",
		"page": "or-grc-portal",
		"app": "omnexa_operational_risk",
		"icon": "🛡️",
		"category": "grc",
		"roles": ["Finance GRC Officer"],
		"label_ar": "OpRisk — حوكمة GRC",
		"label_en": "Operational Risk GRC",
	},
	{
		"id": "acct-exec",
		"route": "/app/acct-executive-dashboard",
		"page": "acct-executive-dashboard",
		"app": "omnexa_accounting",
		"icon": "📒",
		"category": "platform",
		"roles": ["Finance Accounting Controller"],
		"label_ar": "FinTruth — لوحة تنفيذية",
		"label_en": "FinTruth Executive",
	},
	{
		"id": "acct-close",
		"route": "/app/accounting-close-dashboard",
		"page": "accounting-close-dashboard",
		"app": "omnexa_accounting",
		"icon": "🔒",
		"category": "platform",
		"roles": ["Finance Accounting Controller"],
		"label_ar": "FinTruth — إغلاق محاسبي",
		"label_en": "Accounting Close",
	},
]

CATEGORY_LABELS = {
	"admin": {"ar": "الإدارة والتحكم", "en": "Admin & Control"},
	"engine": {"ar": "FinanceCore — محرك التمويل", "en": "Finance Engine"},
	"credit": {"ar": "CreditPulse & RiskGuard", "en": "Credit & Risk"},
	"treasury": {"ar": "TreasuryALM — الخزينة", "en": "Treasury & ALM"},
	"retail": {"ar": "تمويل التجزئة", "en": "Retail Lending"},
	"wholesale": {"ar": "الجملة والتخصيم", "en": "Wholesale"},
	"sme": {"ar": "SMECapital & MicroCapital", "en": "SME & Micro"},
	"grc": {"ar": "OpRisk — حوكمة", "en": "GRC"},
	"platform": {"ar": "FinTruth — المحاسبة", "en": "Accounting Platform"},
}


def _page_exists(page_name: str, page_type: str = "Page") -> bool:
	if page_type == "Workspace":
		return bool(frappe.db.exists("Workspace", page_name))
	return bool(frappe.db.exists("Page", page_name))


def _enrich_portal(row: dict) -> dict:
	item = dict(row)
	app = item.get("app") or _PAGE_APP.get(item.get("page") or "")
	if app:
		item["app"] = app
		item["logo_url"] = get_logo_url(app)
	page_type = item.get("page_type") or "Page"
	item["exists"] = _page_exists(item["page"], page_type)
	return item


@frappe.whitelist()
def get_portal_catalog(include_missing: int = 0) -> list[dict]:
	out = []
	for row in PORTAL_CATALOG:
		item = _enrich_portal(row)
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
