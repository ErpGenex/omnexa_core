#!/usr/bin/env python3
"""Generate ERPGENEX Global Reports & Dashboards audit deliverable (Phases 1–10)."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

BENCH = Path(__file__).resolve().parents[5]
CHECKLIST = (
	Path(__file__).resolve().parents[2]
	/ "docs"
	/ "global_reports_audit"
	/ "REPORTS_PRINT_AUDIT_CHECKLIST.json"
)
OUT_MD = CHECKLIST.parent / "GLOBAL_REPORTS_AUDIT_DELIVERABLE_AR.md"
OUT_JSON = CHECKLIST.parent / "GLOBAL_REPORTS_AUDIT_SUMMARY.json"

KPI_BY_VERTICAL = {
	"omnexa_accounting": ["Revenue", "Expenses", "Net Profit", "Cash Flow", "Liquidity Ratio"],
	"omnexa_trading": ["Sales Volume", "Conversion Rate", "Top Customers", "Top Products"],
	"omnexa_hr": ["Attendance Rate", "Productivity", "Overtime Cost", "Turnover Rate"],
	"omnexa_education": ["Enrollment", "Graduation Rate", "Attendance", "Academic Performance"],
	"omnexa_healthcare": ["Patient Count", "Appointment Utilization", "Revenue Per Patient"],
	"omnexa_tourism": ["Bookings", "Occupancy", "Revenue", "Tourist Satisfaction"],
	"erpgenex_property_mgmt": ["Occupancy Rate", "Rent Collection", "Property ROI"],
}

EXPORT_FORMATS = ["PDF", "Excel", "CSV", "JSON", "HTML", "Print"]
PRINT_FORMATS = ["A4 Portrait", "A4 Landscape", "A3", "Thermal", "Label", "Barcode", "QR"]


def _score_report(r: dict) -> dict:
	signals = r.get("signals") or {}
	gaps = r.get("gaps") or []
	business = 70
	usability = 75
	if signals.get("has_currency_columns"):
		business += 10
	if signals.get("has_totals_or_summary"):
		business += 5
	if signals.get("has_date_filter") and signals.get("has_company_filter"):
		business += 10
	if "FIELD-08" in gaps:
		business = 10
		usability = 20
	if "PRINT-01" in gaps:
		usability -= 15
	if r.get("json_filters", 0) >= 3:
		usability += 10
	business = min(100, max(0, business))
	usability = min(100, max(0, usability))
	mgmt = []
	if business >= 60:
		mgmt.append("Manager")
	if business >= 75:
		mgmt.append("Executive")
	if business >= 85:
		mgmt.append("Board")
	if usability >= 70:
		mgmt.append("Supervisor")
	mgmt.append("Staff")
	return {
		"business_value": business,
		"usability": usability,
		"management_levels": sorted(set(mgmt)),
	}


def _has_chart(py_path: Path) -> bool:
	if not py_path.exists():
		return False
	return "chart" in py_path.read_text(encoding="utf-8", errors="replace").lower()


def build() -> dict:
	data = json.loads(CHECKLIST.read_text(encoding="utf-8"))
	apps = data.get("apps") or {}
	inventory = []
	gap_counter = Counter()
	pending = []
	passed = 0
	missing_kpis: dict[str, list[str]] = defaultdict(list)

	for app, block in sorted(apps.items()):
		reports = block.get("reports") or {}
		for name, r in sorted(reports.items()):
			scores = _score_report(r)
			path = r.get("path") or ""
			py_path = BENCH / path.replace(".json", ".py") if path else Path()
			has_chart = _has_chart(py_path)
			entry = {
				"app": app,
				"module": r.get("module"),
				"report": name,
				"category": r.get("category"),
				"purpose": r.get("ref_doctype") or name,
				"existing_reports": name,
				"filters_count": r.get("json_filters", 0),
				"has_chart": has_chart,
				"gaps": r.get("gaps") or [],
				"audit_status": r.get("audit_status"),
				**scores,
			}
			inventory.append(entry)
			for g in entry["gaps"]:
				gap_counter[g] += 1
			if entry["audit_status"] == "passed":
				passed += 1
			else:
				pending.append(f"{app}::{name}")

		expected = KPI_BY_VERTICAL.get(app, [])
		if expected and reports:
			missing_kpis[app] = [k for k in expected if not any(k.lower().split()[0] in n.lower() for n in reports)]

	roadmap = {
		"critical": [g for g, c in gap_counter.items() if g.startswith("FIELD-0") and c > 0],
		"high": [g for g, c in gap_counter.items() if g.startswith("PRINT") and c > 0],
		"medium": [g for g, c in gap_counter.items() if g.startswith("STD") and c > 0],
		"low": [g for g, c in gap_counter.items() if g.startswith("FIELD-07")],
	}

	return {
		"generated_on": date.today().isoformat(),
		"total_reports": len(inventory),
		"passed": passed,
		"pending": len(pending),
		"pending_list": pending[:50],
		"gap_counts": dict(gap_counter),
		"export_formats": EXPORT_FORMATS,
		"print_formats": PRINT_FORMATS,
		"inventory_sample": inventory[:30],
		"inventory": inventory,
		"missing_kpis": dict(missing_kpis),
		"roadmap": roadmap,
		"missing_reports_catalog": data.get("missing_reports_catalog") or [],
	}


def write_markdown(summary: dict) -> None:
	lines = [
		"# ERPGENEX — تقرير التدقيق الشامل للتقارير ولوحات المعلومات",
		"",
		f"**تاريخ التوليد:** {summary['generated_on']}",
		"",
		"## الملخص التنفيذي",
		"",
		f"- إجمالي التقارير: **{summary['total_reports']}**",
		f"- اجتازت التدقيق: **{summary['passed']}**",
		f"- قيد المعالجة: **{summary['pending']}**",
		"",
		"## التصدير والطباعة (منصة Omnexa Core)",
		"",
		"- أزرار Desk: Print, PDF, Export, Excel, CSV, JSON, HTML",
		"- قوالب طباعة موحدة: ERPGENEX Global Unified + Letter Head",
		"- اختصارات الفترة: اليوم، أمس، هذا الأسبوع، الشهر، الربع، السنة",
		"",
		"## الفجوات حسب الأولوية",
		"",
	]
	for level, items in summary["roadmap"].items():
		lines.append(f"### {level.upper()}")
		lines.append("")
		if items:
			for item in items:
				lines.append(f"- {item} ({summary['gap_counts'].get(item, 0)} تقرير)")
		else:
			lines.append("- لا توجد فجوات")
		lines.append("")

	lines.extend(
		[
			"## مؤشرات الأداء الناقصة (حسب التطبيق)",
			"",
		]
	)
	if summary["missing_kpis"]:
		for app, kpis in summary["missing_kpis"].items():
			lines.append(f"- **{app}**: {', '.join(kpis)}")
	else:
		lines.append("- لا توجد فجوات KPI حرجة في العينة المحللة")

	lines.extend(["", "## قائمة التنفيذ", "", "| التطبيق | التقرير | قيمة الأعمال | سهولة الاستخدام | الحالة |", "|---|---|---:|---:|---|"])
	for row in summary["inventory"]:
		if row["audit_status"] != "passed":
			lines.append(
				f"| {row['app']} | {row['report']} | {row['business_value']} | {row['usability']} | {row['audit_status']} |"
			)
	if summary["pending"] == 0:
		lines.append("| — | جميع التقارير | — | — | passed |")

	OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
	summary = build()
	OUT_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
	write_markdown(summary)
	print(f"Wrote {OUT_MD}")
	print(f"Wrote {OUT_JSON}")
	print(f"passed={summary['passed']} pending={summary['pending']} total={summary['total_reports']}")


if __name__ == "__main__":
	main()
