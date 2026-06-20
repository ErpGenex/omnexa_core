# Copyright (c) 2026, ErpGenEx
"""Unified Finance Group closure — sync, seed, smoke, benchmark, UAT, Wave5, snapshot."""

from __future__ import annotations

import json
from pathlib import Path

import frappe
from frappe.utils import get_bench_path, now_datetime

MASTER_DOCS = Path(get_bench_path()) / "Docs/ERPGENEX_BANKING_FINANCIAL_GROUP_MASTER"


def _verify_all_gaps() -> dict:
	from omnexa_core.omnexa_core.app_uninstall_groups import get_group_apps
	from omnexa_core.omnexa_core.finance_demo.finance_group_benchmark import _find_gap_register

	apps = get_group_apps("finance") + ["omnexa_accounting"]
	results = []
	for app in apps:
		mod = _find_gap_register(app)
		if not mod:
			results.append({"app": app, "ok": True, "skipped": True})
			continue
		try:
			st = frappe.get_attr(f"{mod}.get_gap_status")()
			open_gaps = int(st.get("gaps_open") or 0)
			results.append(
				{
					"app": app,
					"ok": open_gaps == 0,
					"gaps_open": open_gaps,
					"gaps_closed": st.get("gaps_closed"),
					"gaps_total": st.get("gaps_total"),
				}
			)
		except Exception as exc:
			results.append({"app": app, "ok": False, "error": str(exc)})
	passed = sum(1 for r in results if r.get("ok"))
	return {"ok": passed == len(results), "apps_passed": passed, "apps_total": len(results), "apps": results}


@frappe.whitelist()
def run_full_finance_group_closure(
	company: str | None = None,
	branch: str | None = None,
	*,
	seed_roles: int = 1,
	seed_verticals: int = 1,
) -> dict:
	"""One-shot final closure: roles → BPE → seed → smoke → gaps → UAT → Wave5 → benchmark."""
	frappe.only_for("System Manager")
	out: dict = {"ok": True, "started_at": str(now_datetime()), "steps": []}

	if seed_roles:
		from omnexa_core.omnexa_core.finance_demo.finance_role_demo import seed_finance_role_demo

		out["steps"].append({"step": "seed_roles", "result": seed_finance_role_demo(company=company, branch=branch)})

	from omnexa_core.omnexa_core.finance_demo.finance_vertical_bpe import sync_all_finance_vertical_bpe

	out["steps"].append({"step": "sync_bpe", "result": sync_all_finance_vertical_bpe()})

	if seed_verticals:
		from omnexa_core.omnexa_core.finance_demo.finance_vertical_bpe import seed_all_finance_vertical_demos

		out["steps"].append(
			{"step": "seed_verticals", "result": seed_all_finance_vertical_demos(company=company, branch=branch)}
		)

	try:
		from omnexa_core.omnexa_core.finance_demo.finance_group_workspace import sync_finance_group_home

		out["steps"].append({"step": "sync_finance_group", "result": sync_finance_group_home()})
	except Exception as exc:
		out["steps"].append({"step": "sync_finance_group", "error": str(exc)})

	gaps = _verify_all_gaps()
	out["gaps"] = gaps

	from omnexa_core.omnexa_core.finance_demo.finance_group_smoke import run_finance_group_smoke_audit

	smoke = run_finance_group_smoke_audit()
	out["smoke"] = smoke
	out["smoke_passed"] = smoke.get("apps_passed")
	out["smoke_total"] = smoke.get("apps_total")

	from omnexa_core.omnexa_core.finance_demo.finance_group_uat import run_automated_uat

	uat = run_automated_uat()
	out["uat"] = uat

	from omnexa_core.omnexa_core.finance_demo.finance_wave5_stubs import verify_wave5_connectors

	wave5 = verify_wave5_connectors()
	out["wave5"] = wave5

	from omnexa_core.omnexa_core.finance_demo.finance_group_benchmark import get_finance_group_global_score

	benchmark = get_finance_group_global_score()
	out["benchmark"] = benchmark

	try:
		if "omnexa_sme_microfinance" in (frappe.get_installed_apps() or []):
			from omnexa_sme_microfinance.mf_maturity import get_maturity_scores

			out["microcapital_maturity"] = get_maturity_scores()
	except Exception:
		pass

	out["global_number_one"] = bool(benchmark.get("global_number_one"))
	out["apps_passed"] = benchmark.get("apps_passed")
	out["weighted_score"] = benchmark.get("weighted_score")
	out["all_closed"] = (
		out["global_number_one"]
		and gaps.get("ok")
		and uat.get("ok")
		and wave5.get("ok")
		and int(smoke.get("apps_passed") or 0) >= int(smoke.get("apps_total") or 13)
		and int(benchmark.get("apps_passed") or 0) >= 13
	)
	out["finished_at"] = str(now_datetime())

	try:
		_write_live_snapshot(out)
		_write_closure_final(out)
		from omnexa_core.omnexa_core.finance_demo.finance_user_accounts import export_finance_user_accounts

		out["user_accounts"] = export_finance_user_accounts()
	except Exception as exc:
		out["snapshot_error"] = str(exc)

	frappe.db.commit()
	return out


def _write_live_snapshot(closure: dict) -> None:
	MASTER_DOCS.mkdir(parents=True, exist_ok=True)
	payload = {
		"generated": str(now_datetime())[:10],
		"closure": {
			"all_closed": closure.get("all_closed"),
			"global_number_one": closure.get("global_number_one"),
			"weighted_score": closure.get("weighted_score"),
			"apps_passed": closure.get("apps_passed"),
			"smoke_passed": closure.get("smoke_passed"),
			"smoke_total": closure.get("smoke_total"),
			"uat_passed": (closure.get("uat") or {}).get("scenarios_passed"),
			"uat_total": (closure.get("uat") or {}).get("scenarios_total"),
			"wave5_passed": (closure.get("wave5") or {}).get("connectors_passed"),
			"gaps_ok": (closure.get("gaps") or {}).get("ok"),
		},
		"benchmark": closure.get("benchmark"),
		"gaps": closure.get("gaps"),
		"uat": {"passed": (closure.get("uat") or {}).get("scenarios_passed"), "total": (closure.get("uat") or {}).get("scenarios_total")},
		"wave5": closure.get("wave5"),
		"smoke": {
			"passed": closure.get("smoke", {}).get("apps_passed"),
			"total": closure.get("smoke", {}).get("apps_total"),
		},
		"microcapital_maturity": closure.get("microcapital_maturity"),
		"master_docs": str(MASTER_DOCS),
	}
	path = MASTER_DOCS / "LIVE_SNAPSHOT.json"
	path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")


def _write_closure_final(closure: dict) -> None:
	report = f"""# تقرير الإغلاق النهائي — المجموعة المالية البنكية

**التاريخ:** {closure.get("finished_at", "")[:10]}
**الموقع:** erpgenex.local.site
**الحالة:** {"✅ ALL CLOSED" if closure.get("all_closed") else "⚠️ Pending"}

| المؤشر | النتيجة |
|--------|---------|
| Benchmark | {closure.get("weighted_score")} · Global #1: {closure.get("global_number_one")} |
| Gap Register | {(closure.get("gaps") or {}).get("apps_passed")}/{(closure.get("gaps") or {}).get("apps_total")} |
| Smoke | {closure.get("smoke_passed")}/{closure.get("smoke_total")} |
| UAT Automated | {(closure.get("uat") or {}).get("scenarios_passed")}/{(closure.get("uat") or {}).get("scenarios_total")} |
| Wave 5 Stubs | {(closure.get("wave5") or {}).get("connectors_passed")}/{(closure.get("wave5") or {}).get("connectors_total")} |
| MicroCapital Maturity | {(closure.get("microcapital_maturity") or {}).get("overall_maturity", "—")}/100 |

## الأمر
```bash
bench --site erpgenex.local.site execute omnexa_core.omnexa_core.finance_demo.finance_group_master.run_full_finance_group_closure
```
"""
	(MASTER_DOCS / "CLOSURE_FINAL_REPORT_AR.md").write_text(report.strip() + "\n", encoding="utf-8")
	(MASTER_DOCS / "CLOSURE_FINAL.json").write_text(
		json.dumps(
			{
				"all_closed": closure.get("all_closed"),
				"global_number_one": closure.get("global_number_one"),
				"weighted_score": closure.get("weighted_score"),
				"gaps": closure.get("gaps"),
				"uat": closure.get("uat"),
				"wave5": closure.get("wave5"),
				"finished_at": closure.get("finished_at"),
			},
			indent=2,
			default=str,
		)
		+ "\n",
		encoding="utf-8",
	)


@frappe.whitelist()
def get_master_docs_path() -> dict:
	return {"path": str(MASTER_DOCS), "checklist": "MASTER_CHECKLIST_AR.md", "plan": "MASTER_PLAN_AR.md"}
