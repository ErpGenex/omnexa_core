# Copyright (c) 2026, ErpGenEx
"""Finance role portal registry — Journey desk config per page."""

from __future__ import annotations

import json
from pathlib import Path

from omnexa_core.omnexa_core.finance_demo.finance_app_registry import FINANCE_APP_REGISTRY, get_logo_url

# Vertical operational metadata (servicing + executive journeys)
VERTICAL_META: dict[str, dict] = {
	"omnexa_finance_engine": {
		"sidebarRole": "executive",
		"serv_title_ar": "FinanceCore — رحلة الخدمة",
		"serv_title_en": "FinanceCore — Servicing Journey",
		"serv_role_ar": "مسؤول المحرك",
		"serv_role_en": "Engine Officer",
		"exec_title_ar": "FinanceCore — لوحة تنفيذية",
		"exec_title_en": "FinanceCore Executive",
		"exec_role_ar": "مدير تنفيذي",
		"exec_role_en": "Group Executive",
		"kpis_serv": [
			("Finance Product", "منتجات", "Products"),
			("Finance Contract Account", "حسابات عقود", "Contract Accounts"),
			("Finance Calc Run", "تشغيلات حساب", "Calc Runs"),
			("Finance Scenario Run", "سيناريوهات", "Scenarios"),
		],
		"kpis_exec": [
			("Finance Product", "منتجات نشطة", "Active Products"),
			("Finance Contract Account", "محفظة عقود", "Contract Portfolio"),
			("Finance Audit Snapshot", "لقطات تدقيق", "Audit Snapshots"),
			("Finance Event Outbox", "أحداث معلقة", "Pending Events"),
		],
		"table": "Finance Calc Run",
		"table_fields": ["name", "run_status", "run_type", "modified"],
		"table_cols": [
			("name", "التشغيل", "Run"),
			("run_status", "الحالة", "Status"),
			("run_type", "النوع", "Type"),
			("modified", "آخر تحديث", "Updated"),
		],
		"links": [
			("Finance Product", "List/Finance Product"),
			("Finance Rate Plan", "List/Finance Rate Plan"),
			("Finance Contract Account", "List/Finance Contract Account"),
			("Finance Calc Run", "List/Finance Calc Run"),
			("Finance Scenario Run", "List/Finance Scenario Run"),
		],
	},
	"omnexa_credit_engine": {
		"sidebarRole": "credit",
		"serv_title_ar": "CreditPulse — منشأة ائتمان",
		"serv_title_en": "Credit Origination Journey",
		"serv_role_ar": "مسؤول ائتمان",
		"serv_role_en": "Credit Officer",
		"exec_title_ar": "CreditPulse — تنفيذي",
		"exec_title_en": "CreditPulse Executive",
		"exec_role_ar": "مدير ائتمان",
		"exec_role_en": "Credit Executive",
		"kpis_serv": [
			("Credit Decision Case", "حالات قرار", "Decision Cases"),
			("Credit Scorecard", "بطاقات نقاط", "Scorecards"),
			("Credit Strategy Route", "مسارات", "Strategy Routes"),
			("Credit Policy Version", "سياسات", "Policies"),
		],
		"kpis_exec": [
			("Credit Decision Case", "إجمالي الحالات", "Total Cases"),
			("Credit Decision Override", "استثناءات", "Overrides"),
			("Credit Audit Snapshot", "تدقيق", "Audit"),
			("Credit Connector Request", "طلبات ربط", "Connector Requests"),
		],
		"table": "Credit Decision Case",
		"table_fields": ["name", "customer_name", "decision_status", "modified"],
		"table_cols": [
			("name", "الحالة", "Case"),
			("customer_name", "العميل", "Customer"),
			("decision_status", "القرار", "Decision"),
			("modified", "آخر تحديث", "Updated"),
		],
		"links": [
			("Credit Decision Case", "List/Credit Decision Case"),
			("Credit Scorecard", "List/Credit Scorecard"),
			("Credit Strategy Route", "List/Credit Strategy Route"),
			("Credit Policy Version", "List/Credit Policy Version"),
		],
	},
	"omnexa_credit_risk": {
		"sidebarRole": "risk",
		"serv_title_ar": "RiskGuard — تحليل مخاطر",
		"serv_title_en": "Credit Risk Analyst Journey",
		"serv_role_ar": "محلل مخاطر",
		"serv_role_en": "Risk Analyst",
		"exec_title_ar": "RiskGuard — تنفيذي",
		"exec_title_en": "RiskGuard Executive",
		"exec_role_ar": "مدير مخاطر",
		"exec_role_en": "Risk Executive",
		"kpis_serv": [
			("Credit Risk Portfolio Stress Run", "اختبارات إجهاد", "Stress Runs"),
			("Credit Risk Model Validation Run", "تحقق نماذج", "Validations"),
			("Credit Risk ECL Movement", "ECL", "ECL Movements"),
			("Credit Risk Policy Version", "سياسات", "Policies"),
		],
		"kpis_exec": [
			("Credit Risk Account Snapshot", "لقطات حساب", "Account Snapshots"),
			("Credit Risk Backtest Dataset", "اختبارات رجعية", "Backtests"),
			("Credit Risk Calibration Run", "معايرة", "Calibrations"),
			("Credit Risk Audit Snapshot", "تدقيق", "Audit"),
		],
		"table": "Credit Risk Portfolio Stress Run",
		"table_fields": ["name", "status", "modified"],
		"table_cols": [
			("name", "الاختبار", "Run"),
			("status", "الحالة", "Status"),
			("modified", "آخر تحديث", "Updated"),
		],
		"links": [
			("Credit Risk Portfolio Stress Run", "List/Credit Risk Portfolio Stress Run"),
			("Credit Risk Model Validation Run", "List/Credit Risk Model Validation Run"),
			("Credit Risk ECL Movement", "List/Credit Risk ECL Movement"),
			("Credit Risk Policy Version", "List/Credit Risk Policy Version"),
		],
	},
	"omnexa_alm": {
		"sidebarRole": "treasury",
		"serv_title_ar": "TreasuryALM — خزينة",
		"serv_title_en": "Treasury ALM Journey",
		"serv_role_ar": "مسؤول خزينة",
		"serv_role_en": "Treasury Officer",
		"exec_title_ar": "TreasuryALM — تنفيذي",
		"exec_title_en": "TreasuryALM Executive",
		"exec_role_ar": "مدير خزينة",
		"exec_role_en": "Treasury Executive",
		"kpis_serv": [
			("ALM Daily Run", "تشغيل يومي", "Daily Runs"),
			("ALM Position Snapshot", "مراكز", "Positions"),
			("ALM FTP Curve", "منحنيات FTP", "FTP Curves"),
			("ALM Contingency Playbook", "خطط طوارئ", "Playbooks"),
		],
		"kpis_exec": [
			("ALM Daily Run", "تشغيلات", "Runs"),
			("ALM IRRBB Outlier Assessment", "IRRBB", "IRRBB Assessments"),
			("ALM Behavioral Assumption Set", "افتراضات", "Assumptions"),
			("ALM Audit Snapshot", "تدقيق", "Audit"),
		],
		"table": "ALM Daily Run",
		"table_fields": ["name", "status", "modified"],
		"table_cols": [
			("name", "التشغيل", "Run"),
			("status", "الحالة", "Status"),
			("modified", "آخر تحديث", "Updated"),
		],
		"links": [
			("ALM Daily Run", "List/ALM Daily Run"),
			("ALM Position Snapshot", "List/ALM Position Snapshot"),
			("ALM FTP Curve", "List/ALM FTP Curve"),
			("ALM Contingency Playbook", "List/ALM Contingency Playbook"),
		],
	},
	"omnexa_consumer_finance": {
		"sidebarRole": "consumer",
		"serv_title_ar": "RetailLend — تمويل استهلاكي",
		"serv_title_en": "Consumer Lending Journey",
		"serv_role_ar": "مسؤول تمويل استهلاكي",
		"serv_role_en": "Consumer Officer",
		"exec_title_ar": "RetailLend — تنفيذي",
		"exec_title_en": "RetailLend Executive",
		"exec_role_ar": "مدير تجزئة",
		"exec_role_en": "Retail Executive",
		"kpis_serv": [
			("Consumer Loan Application", "طلبات", "Applications"),
			("Consumer Finance Case", "حالات", "Cases"),
			("Consumer Repayment Schedule", "جداول سداد", "Schedules"),
			("Consumer Collections Action", "تحصيل", "Collections"),
		],
		"kpis_exec": [
			("Consumer Finance Case", "محفظة", "Portfolio"),
			("Consumer Loan Application", "طلبات نشطة", "Active Apps"),
			("Consumer Finance Audit Snapshot", "تدقيق", "Audit"),
			("Consumer Collections Action", "متأخرات", "Delinquency Actions"),
		],
		"table": "Consumer Loan Application",
		"table_fields": ["name", "status", "modified"],
		"table_cols": [
			("name", "الطلب", "Application"),
			("status", "الحالة", "Status"),
			("modified", "آخر تحديث", "Updated"),
		],
		"links": [
			("Consumer Loan Application", "List/Consumer Loan Application"),
			("Consumer Finance Case", "List/Consumer Finance Case"),
			("Consumer Repayment Schedule", "List/Consumer Repayment Schedule"),
			("Consumer Collections Action", "List/Consumer Collections Action"),
		],
	},
	"omnexa_vehicle_finance": {
		"sidebarRole": "auto",
		"serv_title_ar": "AutoLend — تمويل مركبات",
		"serv_title_en": "Auto Finance Journey",
		"serv_role_ar": "مسؤول مركبات",
		"serv_role_en": "Auto Officer",
		"exec_title_ar": "AutoLend — تنفيذي",
		"exec_title_en": "AutoLend Executive",
		"exec_role_ar": "مدير مركبات",
		"exec_role_en": "Auto Executive",
		"kpis_serv": [
			("Vehicle Finance Case", "حالات", "Cases"),
			("Vehicle Finance Fleet Contract", "عقود أسطول", "Fleet Contracts"),
			("Vehicle Finance Insurance Policy", "تأمين", "Insurance"),
			("Vehicle Asset Registry", "أصول", "Assets"),
		],
		"kpis_exec": [
			("Vehicle Finance Case", "محفظة", "Portfolio"),
			("Vehicle Finance Audit Snapshot", "تدقيق", "Audit"),
			("Vehicle Finance Fleet Contract", "أساطيل", "Fleets"),
			("Vehicle Finance Insurance Policy", "وثائق", "Policies"),
		],
		"table": "Vehicle Finance Case",
		"table_fields": ["name", "status", "modified"],
		"table_cols": [
			("name", "الحالة", "Case"),
			("status", "الحالة", "Status"),
			("modified", "آخر تحديث", "Updated"),
		],
		"links": [
			("Vehicle Finance Case", "List/Vehicle Finance Case"),
			("Vehicle Finance Fleet Contract", "List/Vehicle Finance Fleet Contract"),
			("Vehicle Finance Insurance Policy", "List/Vehicle Finance Insurance Policy"),
			("Vehicle Asset Registry", "List/Vehicle Asset Registry"),
		],
	},
	"omnexa_mortgage_finance": {
		"sidebarRole": "mortgage",
		"serv_title_ar": "HomeLend — رهن عقاري",
		"serv_title_en": "Mortgage Journey",
		"serv_role_ar": "مسؤول رهن",
		"serv_role_en": "Mortgage Officer",
		"exec_title_ar": "HomeLend — تنفيذي",
		"exec_title_en": "HomeLend Executive",
		"exec_role_ar": "مدير رهن",
		"exec_role_en": "Mortgage Executive",
		"kpis_serv": [
			("Mortgage Finance Case", "حالات", "Cases"),
			("Mortgage Finance Property Registry", "عقارات", "Properties"),
			("Mortgage Finance Legal Case", "قانوني", "Legal Cases"),
			("Mortgage Finance Repayment Schedule", "سداد", "Schedules"),
		],
		"kpis_exec": [
			("Mortgage Finance Case", "محفظة", "Portfolio"),
			("Mortgage Finance Audit Snapshot", "تدقيق", "Audit"),
			("Mortgage Finance Insurance Policy", "تأمين", "Insurance"),
			("Mortgage Finance Legal Case", "قضايا", "Legal"),
		],
		"table": "Mortgage Finance Case",
		"table_fields": ["name", "status", "modified"],
		"table_cols": [
			("name", "الحالة", "Case"),
			("status", "الحالة", "Status"),
			("modified", "آخر تحديث", "Updated"),
		],
		"links": [
			("Mortgage Finance Case", "List/Mortgage Finance Case"),
			("Mortgage Finance Property Registry", "List/Mortgage Finance Property Registry"),
			("Mortgage Finance Legal Case", "List/Mortgage Finance Legal Case"),
			("Mortgage Finance Repayment Schedule", "List/Mortgage Finance Repayment Schedule"),
		],
	},
	"omnexa_factoring": {
		"sidebarRole": "factoring",
		"serv_title_ar": "FactorFlow — تخصيم",
		"serv_title_en": "Factoring Journey",
		"serv_role_ar": "مسؤول تخصيم",
		"serv_role_en": "Factoring Officer",
		"exec_title_ar": "FactorFlow — تنفيذي",
		"exec_title_en": "FactorFlow Executive",
		"exec_role_ar": "مدير تخصيم",
		"exec_role_en": "Factoring Executive",
		"kpis_serv": [
			("Factoring Case", "حالات", "Cases"),
			("Factoring Invoice", "فواتير", "Invoices"),
			("Factoring Debtor Exposure", "مدينون", "Debtors"),
			("Factoring Collection Event", "تحصيل", "Collections"),
		],
		"kpis_exec": [
			("Factoring Case", "محفظة", "Portfolio"),
			("Factoring Settlement Run", "تسويات", "Settlements"),
			("Factoring Audit Snapshot", "تدقيق", "Audit"),
			("Factoring Invoice", "فواتير نشطة", "Active Invoices"),
		],
		"table": "Factoring Case",
		"table_fields": ["name", "status", "modified"],
		"table_cols": [
			("name", "الحالة", "Case"),
			("status", "الحالة", "Status"),
			("modified", "آخر تحديث", "Updated"),
		],
		"links": [
			("Factoring Case", "List/Factoring Case"),
			("Factoring Invoice", "List/Factoring Invoice"),
			("Factoring Debtor Exposure", "List/Factoring Debtor Exposure"),
			("Factoring Settlement Run", "List/Factoring Settlement Run"),
		],
	},
	"omnexa_sme_retail_finance": {
		"sidebarRole": "sme",
		"serv_title_ar": "SMECapital — تمويل منشآت",
		"serv_title_en": "SME Finance Journey",
		"serv_role_ar": "مسؤول منشآت",
		"serv_role_en": "SME Officer",
		"exec_title_ar": "SMECapital — تنفيذي",
		"exec_title_en": "SMECapital Executive",
		"exec_role_ar": "مدير منشآت",
		"exec_role_en": "SME Executive",
		"kpis_serv": [
			("SME Retail Finance Case", "حالات", "Cases"),
			("SME Portfolio Cluster", "مجموعات", "Clusters"),
			("SME Cashflow Projection", "تدفقات", "Cashflows"),
			("SME Financial Statement Snapshot", "قوائم", "Statements"),
		],
		"kpis_exec": [
			("SME Retail Finance Case", "محفظة", "Portfolio"),
			("SME Portfolio Watchlist Event", "مراقبة", "Watchlist"),
			("SME Retail Finance Audit Snapshot", "تدقيق", "Audit"),
			("SME Portfolio Cluster", "تجميع", "Clusters"),
		],
		"table": "SME Retail Finance Case",
		"table_fields": ["name", "status", "modified"],
		"table_cols": [
			("name", "الحالة", "Case"),
			("status", "الحالة", "Status"),
			("modified", "آخر تحديث", "Updated"),
		],
		"links": [
			("SME Retail Finance Case", "List/SME Retail Finance Case"),
			("SME Portfolio Cluster", "List/SME Portfolio Cluster"),
			("SME Cashflow Projection", "List/SME Cashflow Projection"),
			("SME Financial Statement Snapshot", "List/SME Financial Statement Snapshot"),
		],
	},
	"omnexa_sme_microfinance": {
		"sidebarRole": "micro",
		"serv_title_ar": "MicroCapital — ميداني",
		"serv_title_en": "Microfinance Field Journey",
		"serv_role_ar": "مسؤول ميداني",
		"serv_role_en": "Field Officer",
		"exec_title_ar": "MicroCapital — تنفيذي",
		"exec_title_en": "MicroCapital Executive",
		"exec_role_ar": "مدير مicrofinance",
		"exec_role_en": "Micro Executive",
		"kpis_serv": [],
		"kpis_exec": [
			("Microfinance Case", "حالات", "Cases"),
			("Microfinance Case", "محفظة", "Portfolio"),
			("Microfinance Case", "نشطة", "Active"),
			("Microfinance Case", "مغلقة", "Closed"),
		],
		"table": "Microfinance Case",
		"table_fields": ["name", "group_name", "lifecycle_stage", "risk_band", "modified"],
		"table_cols": [
			("name", "الحالة", "Case"),
			("group_name", "المجموعة", "Group"),
			("lifecycle_stage", "المرحلة", "Stage"),
			("risk_band", "المخاطر", "Risk"),
			("modified", "آخر تحديث", "Updated"),
		],
		"links": [
			("Microfinance Case", "List/Microfinance Case"),
			("Microfinance Case", "Form/Microfinance Case/new"),
			("SME Microfinance Workspace", "Workspaces/SME Microfinance"),
		],
	},
	"omnexa_leasing_finance": {
		"sidebarRole": "leasing",
		"serv_title_ar": "LeaseMaster — تأجير",
		"serv_title_en": "Leasing Journey",
		"serv_role_ar": "مسؤول تأجير",
		"serv_role_en": "Leasing Officer",
		"exec_title_ar": "LeaseMaster — تنفيذي",
		"exec_title_en": "LeaseMaster Executive",
		"exec_role_ar": "مدير تأجير",
		"exec_role_en": "Leasing Executive",
		"kpis_serv": [
			("Leasing Finance Contract", "عقود", "Contracts"),
			("Leasing Finance Asset", "أصول", "Assets"),
			("Leasing Finance Payment", "مدفوعات", "Payments"),
			("Leasing Finance Modification Log", "تعديلات", "Modifications"),
		],
		"kpis_exec": [
			("Leasing Finance Contract", "محفظة", "Portfolio"),
			("Leasing Finance Audit Snapshot", "تدقيق", "Audit"),
			("Leasing Finance Asset", "أصول نشطة", "Active Assets"),
			("Leasing Finance Payment", "تحصيل", "Collections"),
		],
		"table": "Leasing Finance Contract",
		"table_fields": ["name", "status", "modified"],
		"table_cols": [
			("name", "العقد", "Contract"),
			("status", "الحالة", "Status"),
			("modified", "آخر تحديث", "Updated"),
		],
		"links": [
			("Leasing Finance Contract", "List/Leasing Finance Contract"),
			("Leasing Finance Asset", "List/Leasing Finance Asset"),
			("Leasing Finance Payment", "List/Leasing Finance Payment"),
			("Leasing Finance Modification Log", "List/Leasing Finance Modification Log"),
		],
	},
	"omnexa_operational_risk": {
		"sidebarRole": "grc",
		"serv_title_ar": "OpRisk — حوكمة GRC",
		"serv_title_en": "Operational Risk GRC Journey",
		"serv_role_ar": "مسؤول GRC",
		"serv_role_en": "GRC Officer",
		"exec_title_ar": "OpRisk — تنفيذي",
		"exec_title_en": "OpRisk Executive",
		"exec_role_ar": "مدير مخاطر تشغيلية",
		"exec_role_en": "OpRisk Executive",
		"kpis_serv": [
			("Operational Loss Event", "خسائر", "Loss Events"),
			("Operational Audit Issue", "مشكلات تدقيق", "Audit Issues"),
			("Operational Compliance Mapping", "امتثال", "Compliance"),
			("Operational Escalation Matrix", "تصعيد", "Escalations"),
		],
		"kpis_exec": [
			("Operational Loss Event", "أحداث", "Events"),
			("Operational Risk Audit Snapshot", "تدقيق", "Audit"),
			("Operational RCA Playbook", "RCA", "Playbooks"),
			("Operational External Ingestion Event", "استيراد", "Ingestion"),
		],
		"table": "Operational Loss Event",
		"table_fields": ["name", "status", "modified"],
		"table_cols": [
			("name", "الحدث", "Event"),
			("status", "الحالة", "Status"),
			("modified", "آخر تحديث", "Updated"),
		],
		"links": [
			("Operational Loss Event", "List/Operational Loss Event"),
			("Operational Audit Issue", "List/Operational Audit Issue"),
			("Operational Compliance Mapping", "List/Operational Compliance Mapping"),
			("Operational Escalation Matrix", "List/Operational Escalation Matrix"),
		],
	},
}

ACCOUNTING_META = {
	"sidebarRole": "accounting",
	"exec_title_ar": "FinTruth — لوحة تنفيذية",
	"exec_title_en": "FinTruth Executive",
	"exec_role_ar": "مراقب محاسبي",
	"exec_role_en": "Accounting Controller",
	"close_title_ar": "FinTruth — إغلاق محاسبي",
	"close_title_en": "Accounting Close Journey",
	"close_role_ar": "مسؤول إغلاق",
	"close_role_en": "Close Officer",
	"kpis_exec": [
		("Journal Entry", "قيود", "Journal Entries"),
		("GL Entry", "حركات GL", "GL Entries"),
		("Payment Entry", "مدفوعات", "Payments"),
		("Sales Invoice", "فواتير", "Invoices"),
	],
	"kpis_close": [
		("Journal Entry", "قيود اليوم", "Today's JEs"),
		("Budget", "موازنات", "Budgets"),
		("Bank Reconciliation", "تسويات بنك", "Bank Recon"),
		("COA Settings", "دليل حسابات", "COA"),
	],
	"table": "Journal Entry",
	"table_fields": ["name", "voucher_type", "posting_date"],
	"table_cols": [
		("name", "القيد", "Entry"),
		("voucher_type", "النوع", "Type"),
		("posting_date", "التاريخ", "Date"),
	],
	"links": [
		("Journal Entry", "List/Journal Entry"),
		("Payment Entry", "List/Payment Entry"),
		("Sales Invoice", "List/Sales Invoice"),
		("Budget", "List/Budget"),
	],
}


def _link_rows(meta_links: list[tuple[str, str]], app: str) -> list[dict]:
	out = []
	seen = set()
	for label_ar_en, route in meta_links:
		key = route
		if key in seen:
			continue
		seen.add(key)
		out.append(
			{
				"label_ar": label_ar_en if isinstance(label_ar_en, str) else label_ar_en[0],
				"label_en": label_ar_en if isinstance(label_ar_en, str) else label_ar_en,
				"route": route,
				"app": app,
				"logo_url": get_logo_url(app),
			}
		)
	# fix labels from tuple (doctype, route)
	fixed = []
	for doctype, route in meta_links:
		fixed.append(
			{
				"label_ar": doctype,
				"label_en": doctype,
				"route": route,
				"app": app,
				"logo_url": get_logo_url(app),
			}
		)
	return fixed


def _build_portal(page: str, app: str, kind: str, meta: dict) -> dict:
	is_exec = kind == "exec"
	return {
		"page": page,
		"app": app,
		"sidebarRole": meta["sidebarRole"],
		"titleAr": meta["exec_title_ar" if is_exec else "serv_title_ar"],
		"titleEn": meta["exec_title_en" if is_exec else "serv_title_en"],
		"roleAr": meta["exec_role_ar" if is_exec else "serv_role_ar"],
		"roleEn": meta["exec_role_en" if is_exec else "serv_role_en"],
		"deskTitle": meta["exec_title_en" if is_exec else "serv_title_en"],
	}


def build_portal_specs() -> dict[str, dict]:
	specs: dict[str, dict] = {}
	for row in FINANCE_APP_REGISTRY:
		app = row["app"]
		meta = VERTICAL_META.get(app)
		if not meta:
			continue
		for kind, page_key in (("serv", "serv_page"), ("exec", "exec_page")):
			page = row[page_key]
			spec = _build_portal(page, app, kind, meta)
			specs[page] = spec
	if "omnexa_operational_risk" in VERTICAL_META:
		meta = VERTICAL_META["omnexa_operational_risk"]
		specs["or-grc-portal"] = {
			"page": "or-grc-portal",
			"app": "omnexa_operational_risk",
			"sidebarRole": "grc",
			"titleAr": meta["serv_title_ar"],
			"titleEn": meta["serv_title_en"],
			"roleAr": meta["serv_role_ar"],
			"roleEn": meta["serv_role_en"],
			"deskTitle": meta["serv_title_en"],
		}
	app = "omnexa_accounting"
	meta = ACCOUNTING_META
	specs["acct-executive-dashboard"] = {
		"page": "acct-executive-dashboard",
		"app": app,
		"sidebarRole": meta["sidebarRole"],
		"titleAr": meta["exec_title_ar"],
		"titleEn": meta["exec_title_en"],
		"roleAr": meta["exec_role_ar"],
		"roleEn": meta["exec_role_en"],
		"deskTitle": meta["exec_title_en"],
	}
	specs["accounting-close-dashboard"] = {
		"page": "accounting-close-dashboard",
		"app": app,
		"sidebarRole": meta["sidebarRole"],
		"titleAr": meta["close_title_ar"],
		"titleEn": meta["close_title_en"],
		"roleAr": meta["close_role_ar"],
		"roleEn": meta["close_role_en"],
		"deskTitle": meta["close_title_en"],
	}
	return specs


PORTAL_SPECS = build_portal_specs()


def get_portal_spec(page: str) -> dict | None:
	return PORTAL_SPECS.get(page)


def get_vertical_meta_for_page(page: str) -> dict | None:
	spec = PORTAL_SPECS.get(page)
	if not spec:
		return None
	app = spec["app"]
	if app == "omnexa_accounting":
		return ACCOUNTING_META
	return VERTICAL_META.get(app)


def export_portal_registry_js() -> Path:
	"""Write finance-portal-registry.js for desk boot."""
	out = Path(__file__).resolve().parents[2] / "public" / "js" / "finance-portal-registry.js"
	payload = json.dumps(PORTAL_SPECS, ensure_ascii=False, indent=2)
	out.write_text(
		f"frappe.provide('omnexa_finance');\nomnexa_finance.PORTAL_REGISTRY = {payload};\n",
		encoding="utf-8",
	)
	return out
