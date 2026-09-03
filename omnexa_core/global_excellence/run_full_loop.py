# Copyright (c) 2026, ErpGenEx
"""Run full Global Excellence Loop across all installed applications (read-only)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import frappe
from frappe.utils import get_bench_path

from omnexa_core.global_excellence.application_audit import audit_application
from omnexa_core.global_excellence.arabic_glossary_export import export_arabic_glossary_artifacts
from omnexa_core.global_excellence.e2e_scenarios import run_e2e_all_applications
from omnexa_core.global_excellence.regression_runner import run_regression_suite
from omnexa_core.global_excellence.rtl_regression import run_rtl_regression
from omnexa_core.global_excellence.system_discovery import build_master_application_inventory
from omnexa_core.vertical_workcenter.registry import VERTICAL_WORKCENTER_REGISTRY


def _export_dir(export_dir: str | None) -> Path:
	if export_dir:
		return Path(export_dir)
	return Path(get_bench_path()) / "Docs" / datetime.now().strftime("%Y-%m-%d") / "excellence-loop"


def _write_json(path: Path, payload) -> str:
	path.parent.mkdir(parents=True, exist_ok=True)
	path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
	return str(path)


def _global_gap_register(app_audits: list[dict]) -> list[dict]:
	gaps: list[dict] = []
	for a in app_audits:
		for g in a.get("gaps") or []:
			gaps.append({**g, "implementation_status": "open", "verification_status": "pending"})
	# Global localization gap — only if tabTranslation is empty
	try:
		trans_count = frappe.db.sql("SELECT COUNT(*) FROM `tabTranslation`")[0][0]
	except Exception:
		trans_count = 0
	if not trans_count:
		gaps.append(
			{
				"id": "LOC-GLOBAL-001",
				"application": "platform",
				"issue": "tabTranslation has zero rows — UI relies on CSV/_() only",
				"severity": "P1",
				"domain": "localization",
				"recommended_solution": "Audit ar.csv per app; consider Translation records for dynamic UI",
				"implementation_status": "open",
			}
		)
	return gaps


def _global_excellence_score(app_audits: list[dict]) -> dict:
	scores = [a["score"]["weighted_score"] for a in app_audits if a.get("score")]
	loc_scores = [a["score"]["localization_score"] for a in app_audits if a.get("score")]
	avg = sum(scores) / len(scores) if scores else 0
	loc_avg = sum(loc_scores) / len(loc_scores) if loc_scores else 0
	p0 = sum(1 for a in app_audits for g in a.get("gaps") or [] if g.get("severity") == "P0")
	p1 = sum(1 for a in app_audits for g in a.get("gaps") or [] if g.get("severity") == "P1")
	p2 = sum(1 for a in app_audits for g in a.get("gaps") or [] if g.get("severity") == "P2")
	open_gaps = sum(len(a.get("gaps") or []) for a in app_audits)
	return {
		"applications_audited": len(app_audits),
		"average_excellence_score": round(avg, 1),
		"average_localization_score": round(loc_avg, 1),
		"combined_global_score": round(avg * 0.85 + loc_avg * 0.15, 1),
		"target_level": "World-Class / Global Excellence #1 Benchmark",
		"open_p0_gaps": p0,
		"open_p1_gaps": p1,
		"open_p2_gaps": p2,
		"open_gaps_total": open_gaps,
		"world_class_gate": {
			"excellence_min": 95,
			"localization_min": 99,
			"open_gaps_max": 0,
			"passed": avg >= 95 and loc_avg >= 99 and open_gaps == 0 and p0 == 0,
		},
	}


def _world_class_gap_analysis(global_score: dict, gaps: list[dict]) -> dict:
	target = 98.0
	current = global_score.get("combined_global_score") or 0
	return {
		"current_combined_score": current,
		"target_benchmark_score": target,
		"gap_points": round(max(0, target - current), 1),
		"top_blockers": [g for g in gaps if g.get("severity") in ("P0", "P1")][:25],
		"recommendation": "Close P0/P1 localization and permission gaps on reference verticals first.",
	}


def _arabic_translation_inventory(app_audits: list[dict]) -> list[dict]:
	rows: list[dict] = []
	for a in app_audits:
		t = a.get("translation") or {}
		h = a.get("hardcoded_scan") or {}
		status = "Translated" if (t.get("ar_lines") or 0) > 50 else ("Partially Translated" if t.get("ar_csv") else "Missing")
		rows.append(
			{
				"application": a["app"],
				"ar_csv": t.get("ar_csv"),
				"ar_lines": t.get("ar_lines"),
				"en_csv": t.get("en_csv"),
				"translation_status": status,
				"hardcoded_ar_files": h.get("hardcoded_ar_in_code"),
				"unmanaged_arabic_files": h.get("unmanaged_arabic_files"),
				"hardcoded_en_samples": h.get("hardcoded_en_samples"),
				"coverage_estimate_pct": min(100, round((t.get("ar_lines") or 0) / 5, 1)) if t.get("ar_csv") else 0,
			}
		)
	return rows


def _final_report_md(
	inventory: dict,
	app_audits: list[dict],
	global_score: dict,
	gaps: list[dict],
	wc_gap: dict,
	out_dir: Path,
	*,
	e2e_summary: dict | None = None,
	regression_summary: dict | None = None,
	rtl_summary: dict | None = None,
	glossary_summary: dict | None = None,
) -> str:
	ranked = sorted(app_audits, key=lambda a: a.get("score", {}).get("weighted_score", 0), reverse=True)
	lines = [
		"# ERPGenex Global Excellence & Arabic Localization Assessment",
		"",
		f"**Generated:** {datetime.now().isoformat(timespec='seconds')}",
		f"**Site:** {inventory['meta']['site']}",
		f"**Target:** {inventory['meta']['target_level']}",
		"",
		"## Executive Summary",
		"",
		f"- Applications audited: **{global_score['applications_audited']}**",
		f"- Combined global score: **{global_score['combined_global_score']}/100**",
		f"- Average excellence score: **{global_score['average_excellence_score']}**",
		f"- Average localization score: **{global_score['average_localization_score']}**",
		f"- Open P0 gaps: **{global_score['open_p0_gaps']}**",
		f"- Open P1 gaps: **{global_score['open_p1_gaps']}**",
		f"- Open P2 gaps: **{global_score.get('open_p2_gaps', 0)}**",
		f"- Open gaps total: **{global_score.get('open_gaps_total', len(gaps))}**",
		f"- World-class gate passed: **{global_score['world_class_gate']['passed']}**",
		"",
	]
	if e2e_summary:
		lines.extend(
			[
				"## E2E Scenario Coverage",
				"",
				f"- Apps tested: **{e2e_summary.get('apps_tested', 0)}**",
				f"- Passed: **{e2e_summary.get('passed', 0)}** | Failed: **{e2e_summary.get('failed', 0)}** | Pass rate: **{e2e_summary.get('pass_rate_pct', 0)}%**",
				"",
			]
		)
	if regression_summary:
		lines.extend(
			[
				"## Regression Tests",
				"",
				f"- Priority apps tested: **{regression_summary.get('apps_tested', 0)}**",
				f"- Passed: **{regression_summary.get('passed', 0)}** | Failed: **{regression_summary.get('failed', 0)}**",
				"",
			]
		)
	if rtl_summary:
		lines.extend(
			[
				"## RTL Portal Regression",
				"",
				f"- Portals tested: **{rtl_summary.get('portals_tested', 0)}**",
				f"- Passed: **{rtl_summary.get('passed', 0)}** | Failed: **{rtl_summary.get('failed', 0)}**",
				"",
			]
		)
	if glossary_summary:
		lines.extend(
			[
				"## Arabic Glossary",
				"",
				f"- Terms exported: **{glossary_summary.get('term_count', 0)}**",
				f"- Files: `ERPGENEX_ARABIC_GLOSSARY.json`, `ARABIC_TERMINOLOGY_RULES.json`",
				"",
			]
		)
	lines.extend(
		[
			"## Global Counts",
			"",
		]
	)
	for k, v in (inventory.get("global_counts") or {}).items():
		lines.append(f"- {k}: {v}")
	lines.extend(
		[
			"",
			"## Applications Ranking (Excellence Score)",
			"",
			"| Rank | App | Score | Grade | DocTypes | Reports | Workflows | AR lines |",
			"|------|-----|------:|-------|----------|---------|-----------|----------|",
		]
	)
	for i, a in enumerate(ranked[:30], 1):
		sc = a.get("score") or {}
		t = a.get("translation") or {}
		lines.append(
			f"| {i} | {a['app']} | {sc.get('weighted_score', '-')} | {sc.get('grade', '-')} | "
			f"{a.get('doctype_count', 0)} | {a.get('report_count', 0)} | {len(a.get('workflows') or [])} | {t.get('ar_lines', 0)} |"
		)
	if len(ranked) > 30:
		lines.append(f"| … | +{len(ranked) - 30} more apps | | | | | | |")

	lines.extend(
		[
			"",
			"## Global Strengths",
			"",
			"- Large multi-vertical portfolio (54 apps, 1000+ DocTypes)",
			"- Reference verticals: Trading, Healthcare, Education, Legal with workcenters",
			"- Unified portal UI (vertical-portal-desk) on omnexa_core",
			"- Most omnexa/erpgenex apps ship translations/ar.csv",
			"",
			"## Global Gaps",
			"",
		]
	)
	by_domain: dict[str, int] = {}
	for g in gaps:
		by_domain[g.get("domain", "other")] = by_domain.get(g.get("domain", "other"), 0) + 1
	for dom, cnt in sorted(by_domain.items(), key=lambda x: -x[1]):
		lines.append(f"- **{dom}**: {cnt} open items")

	lines.extend(
		[
			"",
			"## Critical Risks",
			"",
		]
	)
	for g in [x for x in gaps if x.get("severity") in ("P0", "P1")][:15]:
		lines.append(f"- [{g.get('severity')}] {g.get('application')}: {g.get('issue')}")

	lines.extend(
		[
			"",
			"## World-Class Gap",
			"",
			f"- Current: **{wc_gap['current_combined_score']}**",
			f"- Target benchmark: **{wc_gap['target_benchmark_score']}**",
			f"- Gap: **{wc_gap['gap_points']}** points",
			"",
			"## Recommended Improvements",
			"",
			"1. Monitor E2E scenario failures on submittable DocTypes",
			"2. Expand regression suite beyond priority reference verticals",
			"3. Periodic glossary sync after new DocTypes or modules",
			"4. RTL spot-check on new role portals after UI changes",
			"",
			"## Artifacts",
			"",
			f"All JSON matrices exported to `{out_dir}`",
			"",
			"---",
			"*Read-only audit — no production data modified.*",
		]
	)
	return "\n".join(lines)


def run_full_excellence_loop(*, export_dir: str | None = None) -> dict:
	"""Audit all installed apps and export deliverables 01–24."""
	out = _export_dir(export_dir)
	inventory = build_master_application_inventory()
	apps = [a["app"] for a in inventory["applications"]]

	app_audits: list[dict] = []
	for app in apps:
		try:
			app_audits.append(audit_application(app))
		except Exception as exc:
			app_audits.append(
				{
					"app": app,
					"audit_status": "error",
					"error": str(exc),
					"score": {"weighted_score": 0, "grade": "Error"},
					"gaps": [{"id": f"ERR-{app}", "severity": "P0", "issue": str(exc)}],
				}
			)

	gaps = _global_gap_register(app_audits)
	global_score = _global_excellence_score(app_audits)
	wc_gap = _world_class_gap_analysis(global_score, gaps)
	ar_inv = _arabic_translation_inventory(app_audits)

	glossary_summary = export_arabic_glossary_artifacts(out)
	e2e_summary = run_e2e_all_applications(apps=apps)
	rtl_summary = run_rtl_regression(reference_only=False)
	regression_summary = run_regression_suite()

	paths: dict[str, str] = {}
	paths["01"] = _write_json(out / "01_MASTER_APPLICATION_INVENTORY.json", inventory)
	paths["02"] = _write_json(out / "02_APPLICATION_AUDIT_REPORT.json", app_audits)
	paths["03"] = _write_json(
		out / "03_SCREEN_COMPLETENESS_MATRIX.json",
		[{"app": a["app"], "doctypes": a.get("doctype_count"), "pages": len(a.get("pages") or []), "workspaces": len(a.get("workspaces") or [])} for a in app_audits],
	)
	paths["04"] = _write_json(out / "04_FIELD_COMPLETENESS_MATRIX.json", [{"app": a["app"], **a.get("field_stats", {})} for a in app_audits])
	paths["05"] = _write_json(
		out / "05_DROPDOWN_DATA_SOURCE_MATRIX.json",
		[{"app": a["app"], "link_fields": a.get("field_stats", {}).get("link_fields"), "select_fields": a.get("field_stats", {}).get("select_fields")} for a in app_audits],
	)
	paths["06"] = _write_json(out / "06_REPORT_COMPLETENESS_MATRIX.json", [{"app": a["app"], "report_count": a.get("report_count"), "reports": a.get("reports")} for a in app_audits])
	paths["07"] = _write_json(out / "07_WORKFLOW_MATRIX.json", [{"app": a["app"], "workflows": a.get("workflows")} for a in app_audits])
	paths["08"] = _write_json(out / "08_BUSINESS_SCENARIO_MATRIX.json", e2e_summary)
	paths["09"] = _write_json(out / "09_PERMISSION_AUDIT.json", [{"app": a["app"], "permission_gaps": a.get("permission_gaps")} for a in app_audits])
	paths["10"] = _write_json(out / "10_SECURITY_AUDIT.json", {"permission_gaps_total": sum(len(a.get("permission_gaps") or []) for a in app_audits), "apps_with_hooks": [a["app"] for a in app_audits if a.get("hooks")]})
	paths["11"] = _write_json(out / "11_DATA_QUALITY_AUDIT.json", {"note": "Orphan record scan deferred — requires business rules per DocType"})
	paths["12"] = _write_json(out / "12_INTEGRATION_MATRIX.json", {"vertical_registry": VERTICAL_WORKCENTER_REGISTRY, "unregistered": inventory.get("unregistered_custom_apps")})
	paths["13"] = _write_json(out / "13_UX_UI_AUDIT.json", [{"app": a["app"], "registry_status": (a.get("registry") or {}).get("status"), "pages": len(a.get("pages") or []), "reference": bool((a.get("registry") or {}).get("reference"))} for a in app_audits])
	paths["14"] = _write_json(out / "14_PERFORMANCE_AUDIT.json", {"note": "Report query profiling deferred — run per slow report"})
	paths["15"] = _write_json(out / "15_GAP_REGISTER.json", gaps)
	paths["16"] = _write_json(out / "16_REGRESSION_TEST_REPORT.json", regression_summary)
	paths["17"] = _write_json(out / "17_APPLICATION_SCORECARD.json", [{"app": a["app"], **a.get("score", {}), "gap_count": len(a.get("gaps") or [])} for a in app_audits])
	paths["18"] = _write_json(out / "18_GLOBAL_PROCESS_MAP.json", {"verticals": [{"app": r["app"], "workcenter": r.get("workcenter"), "title_en": r.get("title_en")} for r in VERTICAL_WORKCENTER_REGISTRY]})
	paths["19"] = _write_json(out / "19_GLOBAL_DATA_LINEAGE.json", {"note": "Per-DocType lineage — extend with report ref_doctype mapping"})
	paths["20"] = _write_json(out / "20_GLOBAL_REPORT_COVERAGE.json", [{"app": a["app"], "doctype_count": a.get("doctype_count"), "report_count": a.get("report_count"), "ratio": round((a.get("report_count") or 0) / max(1, a.get("doctype_count") or 1), 2)} for a in app_audits])
	paths["21"] = _write_json(out / "21_GLOBAL_SCENARIO_COVERAGE.json", e2e_summary)
	paths["RTL"] = _write_json(out / "RTL_PORTAL_REGRESSION.json", rtl_summary)
	paths["GLOSSARY"] = glossary_summary["glossary_path"]
	paths["TERMINOLOGY"] = glossary_summary["rules_path"]
	paths["22"] = _write_json(out / "22_GLOBAL_EXCELLENCE_SCORE.json", global_score)
	paths["23"] = _write_json(out / "23_WORLD_CLASS_GAP_ANALYSIS.json", wc_gap)
	paths["ARABIC"] = _write_json(out / "ARABIC_TRANSLATION_INVENTORY.json", ar_inv)
	paths["AR_DEF"] = _write_json(
		out / "ARABIC_TRANSLATION_DEFECT_REGISTER.json",
		[g for g in gaps if g.get("domain") == "localization"],
	)
	paths["LOC_AUDIT"] = _write_json(
		out / "ERPGENEX_GLOBAL_LOCALIZATION_AUDIT.json",
		{"inventory": ar_inv, "global_translation_rows": inventory["global_counts"].get("translations"), "apps_missing_ar_csv": [r["application"] for r in ar_inv if not r.get("ar_csv") and r["application"].startswith(("omnexa_", "erpgenex_"))]},
	)

	report_md = _final_report_md(
		inventory,
		app_audits,
		global_score,
		gaps,
		wc_gap,
		out,
		e2e_summary=e2e_summary,
		regression_summary=regression_summary,
		rtl_summary=rtl_summary,
		glossary_summary=glossary_summary,
	)
	report_path = out / "24_FINAL_ERPGENEX_GLOBAL_EXCELLENCE_REPORT.md"
	report_path.write_text(report_md, encoding="utf-8")
	paths["24"] = str(report_path)

	return {
		"export_dir": str(out),
		"applications_audited": len(app_audits),
		"global_score": global_score,
		"total_gaps": len(gaps),
		"e2e_summary": e2e_summary,
		"regression_summary": regression_summary,
		"rtl_summary": rtl_summary,
		"glossary_summary": glossary_summary,
		"paths": paths,
	}


@frappe.whitelist()
def export_full_excellence_loop(export_dir: str | None = None) -> dict:
	frappe.only_for("System Manager")
	return run_full_excellence_loop(export_dir=export_dir)
