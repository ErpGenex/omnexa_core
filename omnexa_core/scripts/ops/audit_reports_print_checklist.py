#!/usr/bin/env python3
# Copyright (c) 2026, Omnexa / ErpGenEx
"""Scan ErpGenEx apps and maintain REPORTS_PRINT_AUDIT_CHECKLIST.json.

Usage (from bench root):
  python3 apps/omnexa_core/omnexa_core/scripts/ops/audit_reports_print_checklist.py
  python3 apps/omnexa_core/omnexa_core/scripts/ops/audit_reports_print_checklist.py --merge
"""

from __future__ import annotations

import argparse
import ast
import json
import re
from datetime import date
from pathlib import Path

def _find_bench_root() -> Path:
	p = Path(__file__).resolve().parent
	for _ in range(12):
		if (p / "sites" / "apps.txt").is_file():
			return p
		if p.parent == p:
			break
		p = p.parent
	raise SystemExit("Cannot find frappe-bench root (missing sites/apps.txt)")


BENCH_ROOT = _find_bench_root()
APPS_FILE = BENCH_ROOT / "sites" / "apps.txt"
OUT_DIR = BENCH_ROOT / "Docs" / "2026-05-20_GLOBAL_REPORTS_AUDIT"
OUT_JSON = OUT_DIR / "REPORTS_PRINT_AUDIT_CHECKLIST.json"

FINANCIAL_KEYWORDS = (
	"trial_balance",
	"balance_sheet",
	"income_statement",
	"cash_flow",
	"ledger",
	"aging",
	"receivable",
	"payable",
	"gl_",
	"general_ledger",
	"financial",
	"lease_liability",
	"rent_roll",
	"payroll",
	"vat",
	"tax",
	"financial_summary",
)
AUDIT_KEYWORDS = ("audit", "compliance", "governance", "control", "remediation", "evidence")
ASSET_KEYWORDS = ("asset", "depreciation", "insurance", "maintenance", "work_order")

STANDARDS_BY_CATEGORY = {
	"financial": ["IAS-1", "IAS-7", "IAS-21", "IFRS-7", "IFRS-16"],
	"audit": ["ISA-230", "ISA-700", "ISA-705"],
	"regulatory": ["CBE-ALM", "BCBS-239", "IOSCO"],
	"operational": ["ISO-55000", "RICS", "IPMS"],
	"governance": ["COSO", "ISO-27001"],
}

WAVE_BY_APP = {
	"omnexa_accounting": "W1",
	"omnexa_statutory_audit": "W1",
	"omnexa_reporting_compliance": "W1",
	"omnexa_fixed_assets": "W2",
	"erpgenex_property_mgmt": "W2",
	"omnexa_alm": "W2",
	"omnexa_hr": "W3",
	"omnexa_einvoice": "W3",
}


def _load_apps() -> list[str]:
	lines = APPS_FILE.read_text(encoding="utf-8").splitlines()
	return [
		a.strip()
		for a in lines
		if a.strip() and a.strip() != "frappe" and (a.startswith("omnexa_") or a.startswith("erpgenex_"))
	]


def _keyword_in_blob(blob: str, keyword: str) -> bool:
	"""Avoid false positives (e.g. 'vat' inside 'observation')."""
	if keyword.endswith("_"):
		return keyword in blob
	if len(keyword) <= 4:
		return bool(re.search(rf"(^|[\s_/]){re.escape(keyword)}($|[\s_/])", blob))
	return keyword in blob


def _category(name: str, ref: str) -> str:
	n = (name or "").lower()
	r = (ref or "").lower()
	blob = f"{n} {r}"
	if any(_keyword_in_blob(blob, k) for k in AUDIT_KEYWORDS):
		return "audit"
	if any(_keyword_in_blob(blob, k) for k in FINANCIAL_KEYWORDS):
		return "financial"
	if any(_keyword_in_blob(blob, k) for k in ASSET_KEYWORDS):
		return "operational"
	return "operational"


def _wave(app: str, category: str) -> str:
	if app in WAVE_BY_APP:
		return WAVE_BY_APP[app]
	if category == "financial":
		return "W2"
	if category == "audit":
		return "W1"
	return "W4"


def _read_py_signals(py_path: Path) -> dict:
	if not py_path.exists():
		return {}
	text = py_path.read_text(encoding="utf-8", errors="replace")
	has_company = bool(re.search(r'["\']company["\']|filters\.get\(["\']company', text))
	has_dates = bool(
		re.search(
			r'from_date|to_date|as_of_date|posting_date|period_start|period_end|fiscal_year|valid_from|valid_to|log_date',
			text,
		)
	)
	has_currency = bool(re.search(r'fieldtype["\']\s*:\s*["\']Currency["\']|["\']Currency["\']', text))
	has_branch = bool(re.search(r"branch|get_allowed_branches", text))
	has_i18n = "__(" in text or "_(" in text or "report_query_filters" in text
	has_bilingual_cols = bool(re.search(r"_en|_ar|Name \(EN\)|Name \(AR\)", text))
	is_stub = bool(re.search(r"return\s+\[\]\s*,\s*\[\]", text)) and "def execute" in text
	has_totals = bool(re.search(r"total|grand_total|report_summary", text, re.I))
	return {
		"has_company_filter": has_company,
		"has_date_filter": has_dates,
		"has_currency_columns": has_currency,
		"has_branch_dimension": has_branch,
		"has_i18n_labels": has_i18n,
		"has_bilingual_columns": has_bilingual_cols,
		"is_stub_execute": is_stub,
		"has_totals_or_summary": has_totals,
	}


def _auto_gaps(signals: dict, meta: dict, report_name: str = "") -> list[str]:
	gaps = []
	html_ok = False
	if meta.get("path"):
		folder = BENCH_ROOT / Path(meta["path"]).parent
		for html in folder.glob("*.html"):
			try:
				if "ERPGENEX report print template" in html.read_text(encoding="utf-8"):
					html_ok = True
					break
			except OSError:
				continue
	if not html_ok:
		gaps.append("PRINT-01")
		gaps.append("PRINT-02")
	if meta["category"] == "financial" and not signals.get("has_company_filter"):
		gaps.append("FIELD-01")
	if meta["category"] == "financial" and not signals.get("has_date_filter"):
		gaps.append("FIELD-02")
	if meta["category"] == "financial" and not signals.get("has_currency_columns"):
		gaps.append("FIELD-03")
	if not signals.get("has_i18n_labels") and not signals.get("has_bilingual_columns"):
		gaps.append("FIELD-06")
	if meta["json_filters"] == 0 and (
		signals.get("has_company_filter") or signals.get("has_date_filter")
	):
		gaps.append("FIELD-07")
	if signals.get("is_stub_execute"):
		gaps.append("FIELD-08")
	if meta["category"] == "audit" and not html_ok:
		gaps.append("STD-02")
	return gaps


def _scan_reports(app: str) -> dict[str, dict]:
	app_dir = BENCH_ROOT / "apps" / app
	found: dict[str, dict] = {}
	if not app_dir.exists():
		return found
	for json_path in app_dir.rglob("*.json"):
		if "/report/" not in str(json_path).replace("\\", "/"):
			continue
		try:
			data = json.loads(json_path.read_text(encoding="utf-8"))
		except Exception:
			continue
		if data.get("doctype") != "Report":
			continue
		name = data.get("name") or json_path.parent.name
		if name in found:
			continue
		py_path = json_path.with_suffix(".py")
		js_path = json_path.with_suffix(".js")
		ref = data.get("ref_doctype") or ""
		cat = _category(name, ref)
		signals = _read_py_signals(py_path)
		meta = {
			"module": data.get("module"),
			"ref_doctype": ref,
			"report_type": data.get("report_type") or "Script Report",
			"category": cat,
			"priority_wave": _wave(app, cat),
			"standards": STANDARDS_BY_CATEGORY.get(cat, []),
			"has_client_js": js_path.exists(),
			"json_filters": len(data.get("filters") or []),
			"json_columns": len(data.get("columns") or []),
			"path": str(json_path.relative_to(BENCH_ROOT)),
		}
		json_filter_fields = {f.get("fieldname") for f in (data.get("filters") or []) if f.get("fieldname")}
		if json_filter_fields & {"from_date", "to_date", "as_of_date", "posting_date", "fiscal_year"}:
			signals["has_date_filter"] = True
		if "company" in json_filter_fields:
			signals["has_company_filter"] = True
		if meta["json_filters"] and not signals.get("has_i18n_labels"):
			signals["has_i18n_labels"] = True
		gaps = _auto_gaps(signals, meta, name)
		audit_status = "passed" if not gaps and meta["report_type"] == "Script Report" else "pending"
		found[name] = {
			**meta,
			"signals": signals,
			"print": {
				"global_print_style": "ERPGENEX Global Unified",
				"report_print_format_linked": False,
				"letter_head_on_report_json": data.get("letter_head"),
				"a4_rtl_ready": "pending",
			},
			"audit_status": audit_status,
			"gaps": gaps,
			"notes": "",
		}
	return found


MISSING_REPORTS_CATALOG = [
	{
		"id": "MISS-PMC-01",
		"app": "erpgenex_property_mgmt",
		"report_name": "PMC Rent Aging",
		"standard": "IPMS / IAS 21",
		"priority_wave": "W2",
		"status": "implemented",
		"notes": "Added 2026-05-20 — summary buckets from PMC Rent Roll.",
	},
	{
		"id": "MISS-PMC-02",
		"app": "erpgenex_property_mgmt",
		"report_name": "PMC Owner Statement Register",
		"standard": "RICS",
		"priority_wave": "W2",
		"status": "implemented",
		"notes": "PMC Owner Statement Register report 2026-05-21.",
	},
	{
		"id": "MISS-ALM-01",
		"app": "omnexa_alm",
		"report_name": "ALM Gap Report",
		"standard": "CBE-ALM / BCBS",
		"priority_wave": "W2",
		"status": "implemented",
		"notes": "Existing report ALM Gap Report (liquidity ladder).",
	},
	{
		"id": "MISS-ALM-02",
		"app": "omnexa_alm",
		"report_name": "ALM NII EVE Sensitivity",
		"standard": "BCBS-239",
		"priority_wave": "W2",
		"status": "implemented",
		"notes": "Existing report ALM NII EVE Sensitivity.",
	},
	{
		"id": "MISS-AUD-01",
		"app": "omnexa_statutory_audit",
		"report_name": "Audit Working Paper Pack",
		"standard": "ISA-230",
		"priority_wave": "W1",
		"status": "implemented",
		"notes": "ISA disclaimer in audit print template + pack report.",
	},
	{
		"id": "MISS-ACC-01",
		"app": "omnexa_accounting",
		"report_name": "Notes to Financial Statements",
		"standard": "IAS-1",
		"priority_wave": "W1",
		"status": "implemented",
		"notes": "IAS 1 notes pack MVP 2026-05-20.",
	},
	{
		"id": "MISS-ACC-02",
		"app": "omnexa_accounting",
		"report_name": "Consolidated Financial Statements",
		"standard": "IFRS-10",
		"priority_wave": "W1",
		"status": "implemented",
		"notes": "Multi-company BS + P&L pack 2026-05-21.",
	},
	{
		"id": "MISS-FA-01",
		"app": "omnexa_fixed_assets",
		"report_name": "IAS 16 Disclosure Schedule",
		"standard": "IAS-16",
		"priority_wave": "W2",
		"status": "implemented",
	},
	{
		"id": "MISS-HR-01",
		"app": "omnexa_hr",
		"report_name": "HR Payroll Statutory Deductions Register",
		"standard": "Local payroll",
		"priority_wave": "W3",
		"status": "implemented",
	},
	{
		"id": "MISS-TRD-01",
		"app": "omnexa_trading",
		"report_name": "POS Z Report Reconciliation",
		"standard": "Trading POS MVP",
		"priority_wave": "W3",
		"status": "implemented",
	},
]


APPS_WAIVED_NO_REPORTS = [
	"omnexa_setup_intelligence",
	"omnexa_theme_manager",
	"omnexa_backup",
	"omnexa_eng_document_control",
	"omnexa_eng_workflow_engine",
	"omnexa_n8n_bridge",
	"omnexa_intelligence_core",
	"omnexa_eng_platform_integrations",
	"erpgenex_theme_0426",
	"omnexa_user_academy",
]

AUDIT_DIMENSIONS = [
	{"id": "PRINT-01", "area": "print", "label": "Report print format linked (Jinja/HTML)", "weight": "high"},
	{"id": "PRINT-02", "area": "print", "label": "Letter head: company + ERPGENEX global footer", "weight": "high"},
	{"id": "PRINT-03", "area": "print", "label": "A4 portrait, margins 12–20mm, print-color-adjust", "weight": "medium"},
	{"id": "PRINT-04", "area": "print", "label": "Page x of y + printed timestamp in footer", "weight": "medium"},
	{"id": "PRINT-05", "area": "print", "label": "RTL/LTR + bilingual header where AR enabled", "weight": "high"},
	{"id": "FIELD-01", "area": "fields", "label": "Mandatory company filter + validation", "weight": "critical"},
	{"id": "FIELD-02", "area": "fields", "label": "Period filters (from/to or as-of)", "weight": "critical"},
	{"id": "FIELD-03", "area": "fields", "label": "Currency columns with company precision", "weight": "high"},
	{"id": "FIELD-04", "area": "fields", "label": "Totals / subtotals / report_summary", "weight": "medium"},
	{"id": "FIELD-05", "area": "fields", "label": "Branch / consolidation dimension", "weight": "high"},
	{"id": "FIELD-06", "area": "fields", "label": "Bilingual labels (_() or EN/AR columns)", "weight": "medium"},
	{"id": "FIELD-07", "area": "fields", "label": "Filters declared in report JSON for Desk UX", "weight": "low"},
	{"id": "FIELD-08", "area": "fields", "label": "Non-stub execute() with real data", "weight": "critical"},
	{"id": "STD-01", "area": "standards", "label": "IAS/IFRS mapping documented for financial reports", "weight": "high"},
	{"id": "STD-02", "area": "standards", "label": "ISA disclaimer on audit outputs", "weight": "critical"},
	{"id": "STD-03", "area": "standards", "label": "Regulatory template (CBE/ALM) where applicable", "weight": "high"},
	{"id": "STD-04", "area": "standards", "label": "Sector KPI completeness (RICS/IPMS/ISO55000)", "weight": "medium"},
]


def build_checklist(merge_existing: bool) -> dict:
	apps = _load_apps()
	old: dict = {}
	if merge_existing and OUT_JSON.exists():
		old = json.loads(OUT_JSON.read_text(encoding="utf-8"))

	old_reports = (old.get("apps") or {}) if old else {}

	apps_out = {}
	total = 0
	for app in apps:
		reports = _scan_reports(app)
		total += len(reports)
		merged_reports = {}
		prev_app = old_reports.get(app, {}).get("reports", {})
		for rname, rdata in sorted(reports.items()):
			prev = prev_app.get(rname, {})
			entry = {**rdata}
			if merge_existing and prev:
				for key in ("notes", "assigned_to", "reviewed_at"):
					if prev.get(key):
						entry[key] = prev[key]
				# Keep explicit QA outcomes; do not let stale "pending" block auto-pass.
				if prev.get("audit_status") not in (None, "pending"):
					entry["audit_status"] = prev["audit_status"]
				if prev.get("gaps_manual"):
					entry["gaps"] = prev["gaps_manual"]
			merged_reports[rname] = entry
		apps_out[app] = {
			"report_count": len(merged_reports),
			"reports": merged_reports,
		}

	# Merge catalog: keep manual notes; script "implemented" wins over stale "missing".
	missing = list(MISSING_REPORTS_CATALOG)
	old_missing = {m["id"]: m for m in (old.get("missing_reports_catalog") or [])}
	for item in missing:
		prev = old_missing.get(item["id"])
		if not prev:
			continue
		for k in ("status", "notes", "audit_status"):
			old_val = prev.get(k)
			if not old_val:
				continue
			if k == "status" and item.get("status") == "implemented" and old_val == "missing":
				continue
			item[k] = old_val

	summary = {
		"total_reports": total,
		"apps_with_reports": sum(1 for a in apps_out.values() if a["report_count"]),
		"apps_zero_reports": [a for a, v in apps_out.items() if v["report_count"] == 0],
		"pending": sum(
			1
			for a in apps_out.values()
			for r in a["reports"].values()
			if r.get("audit_status") == "pending"
		),
		"missing_catalog_count": len(missing),
		"apps_waived_no_reports": list(APPS_WAIVED_NO_REPORTS),
	}

	return {
		"meta": {
			"title": "ErpGenEx Reports Print & Fields Audit Checklist",
			"version": "1.0.0",
			"generated_on": date.today().isoformat(),
			"bench_root": str(BENCH_ROOT),
			"generator": "scripts/ops/audit_reports_print_checklist.py",
		},
		"global_print_system": {
			"module": "omnexa_core.global_print_design",
			"print_style": "ERPGENEX Global Unified",
			"letter_head": "ERPGENEX Global Letter Head",
			"default_format_prefix": "ERPGENEX Default -",
			"report_level_wiring": "implemented",
		},
		"audit_dimensions": AUDIT_DIMENSIONS,
		"standards_reference": {
			"financial": "IAS 1/7/21, IFRS 7/10/16 — Docs/OLDDOC/Accounting_International_Reporting_Standards_MVP.md",
			"audit": "ISA 230/700/705 — Docs/OLDDOC/Statutory_Audit_Legal_Review_Report_Output_Disclaimer_MVP.md",
			"regulatory": "CBE ALM — Docs/OLDDOC/Fintech_ALM_Liquidity_IRRBB_Stress_and_CBE_Reports_MVP.md",
			"operational": "RICS, IPMS, ISO 55000 — vertical gap checklists",
		},
		"summary": summary,
		"apps": apps_out,
		"missing_reports_catalog": missing,
		"apps_waived_no_reports": APPS_WAIVED_NO_REPORTS,
		"update_waves": {
			"W1": {
				"label": "Financial & audit core",
				"apps": ["omnexa_accounting", "omnexa_statutory_audit", "omnexa_reporting_compliance"],
				"target_date": "2026-06-15",
			},
			"W2": {
				"label": "Assets, RE, ALM",
				"apps": ["omnexa_fixed_assets", "erpgenex_property_mgmt", "omnexa_alm"],
				"target_date": "2026-07-01",
			},
			"W3": {
				"label": "HR, e-invoice, trading, finance verticals",
				"apps": ["omnexa_hr", "omnexa_einvoice", "omnexa_trading", "omnexa_leasing_finance"],
				"target_date": "2026-07-15",
			},
			"W4": {
				"label": "Remaining sector apps + governance reports",
				"apps": "all_remaining",
				"target_date": "2026-08-15",
			},
		},
	}


def main() -> None:
	parser = argparse.ArgumentParser()
	parser.add_argument("--merge", action="store_true", help="Preserve manual audit_status/notes")
	args = parser.parse_args()
	OUT_DIR.mkdir(parents=True, exist_ok=True)
	payload = build_checklist(merge_existing=args.merge)
	OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
	print(f"Wrote {OUT_JSON}")
	print(f"Total reports: {payload['summary']['total_reports']}")
	print(f"Missing catalog: {payload['summary']['missing_catalog_count']}")


if __name__ == "__main__":
	main()
