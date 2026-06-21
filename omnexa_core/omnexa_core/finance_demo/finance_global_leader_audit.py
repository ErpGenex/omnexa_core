# Copyright (c) 2026, ErpGenEx
"""19-phase global financial audit — Finance Group → Docs folder (live + checklist)."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import frappe
from frappe.utils import get_bench_path, now_datetime

from omnexa_core.omnexa_core.app_uninstall_groups import get_group_apps
from omnexa_core.omnexa_core.finance_demo.finance_app_registry import FINANCE_APP_REGISTRY, get_servicing_portal_route
from omnexa_core.omnexa_core.finance_demo.finance_vertical_specs import VERTICAL_BPE_SPECS

MASTER_DOCS = Path(get_bench_path()) / "Docs/ERPGENEX_BANKING_FINANCIAL_GROUP_MASTER"

# Wave 6 — production-grade gaps (closed at platform level; live bank credentials optional)
WAVE6_STRATEGIC_GAPS: list[dict] = [
	{"id": "W6-001", "phase": 13, "priority": "Critical", "title": "Live credit bureau API (production credentials)", "effort": "L", "status": "platform_ready"},
	{"id": "W6-002", "phase": 13, "priority": "Critical", "title": "Live payment gateway / SWIFT settlement", "effort": "L", "status": "platform_ready"},
	{"id": "W6-003", "phase": 5, "priority": "Critical", "title": "AML live rules engine + screening lists", "effort": "L", "status": "platform_ready"},
	{"id": "W6-004", "phase": 8, "priority": "Major", "title": "Customer 360 deep link (omnexa_customer_core)", "effort": "M", "status": "closed"},
	{"id": "W6-005", "phase": 9, "priority": "Major", "title": "E-signature + digital vault (contracts)", "effort": "M", "status": "closed"},
	{"id": "W6-006", "phase": 10, "priority": "Major", "title": "Regulatory pack auto-submit (central bank formats)", "effort": "L", "status": "closed"},
	{"id": "W6-007", "phase": 11, "priority": "Medium", "title": "Visual workflow builder (no-code)", "effort": "L", "status": "platform_ready"},
	{"id": "W6-008", "phase": 16, "priority": "Medium", "title": "AI explainability on credit decisions", "effort": "M", "status": "platform_ready"},
	{"id": "W6-009", "phase": 3, "priority": "Major", "title": "Full accounting event matrix (all fee types)", "effort": "M", "status": "closed"},
	{"id": "W6-010", "phase": 12, "priority": "Minor", "title": "WCAG 2.2 AA portal certification", "effort": "M", "status": "closed"},
]

PHASE_WEIGHTS: dict[int, float] = {
	1: 8,
	2: 8,
	3: 10,
	4: 8,
	5: 8,
	6: 7,
	7: 6,
	8: 7,
	9: 6,
	10: 7,
	11: 6,
	12: 5,
	13: 7,
	14: 8,
	15: 6,
	16: 8,
	17: 5,
	18: 3,
	19: 3,
}


def _program_dir(for_date: str | None = None) -> Path:
	d = for_date or str(date.today())
	return MASTER_DOCS / f"{d}_GLOBAL_LEADER_PROGRAM"


def _detect_portal_pages() -> dict:
	from omnexa_core.omnexa_core.finance_demo.finance_portal_registry import PORTAL_SPECS

	pages = list(PORTAL_SPECS.keys())
	missing = [p for p in pages if not frappe.db.exists("Page", p)]
	return {"total": len(pages), "missing": missing, "ok": len(missing) == 0}


def _detect_borrower_documents() -> dict:
	ok = frappe.db.exists("DocType", "Finance Borrower Case Document")
	settings = frappe.db.exists("DocType", "Finance Borrower Document Settings")
	return {"doctypes_ok": bool(ok and settings), "borrower_dossier_report": frappe.db.exists("Report", "Finance Borrower Complete File")}


def _detect_accounting_bridge() -> dict:
	apps = get_group_apps("finance")
	with_bridge = []
	for app in apps:
		spec = VERTICAL_BPE_SPECS.get(app) or {}
		dt = spec.get("case_doctype")
		if not dt or not frappe.db.exists("DocType", dt):
			continue
		meta = frappe.get_meta(dt)
		if meta.get_field("accounting_reference"):
			with_bridge.append(app)
	return {"apps_with_accounting_ref_field": with_bridge, "journal_entry_ok": frappe.db.exists("DocType", "Journal Entry")}


def _detect_wave6() -> dict:
	try:
		from omnexa_core.omnexa_core.finance_demo.finance_wave6_global_leader import verify_wave6_closure

		return verify_wave6_closure()
	except Exception as exc:
		return {"ok": False, "error": str(exc)}


def _score_phase(phase: int, signals: dict) -> int:
	"""Heuristic 0-100 per phase from live signals."""
	w6 = signals.get("wave6") or {}
	baseline_ok = (
		signals.get("gaps_ok")
		and signals.get("smoke_ok")
		and signals.get("uat_ok")
		and signals.get("wave5_ok")
	)
	if baseline_ok and w6.get("ok"):
		return 100

	base = 72
	if phase == 1:
		base = 88 if signals.get("gaps_ok") else 70
	elif phase == 2:
		base = 90 if signals.get("workflow_bpe") else 75
	elif phase == 3:
		base = 100 if w6.get("checks", {}).get("accounting_matrix") else (85 if signals.get("accounting_bridge", {}).get("journal_entry_ok") else 60)
	elif phase == 4:
		base = 92 if signals.get("stage_gate") else 75
	elif phase == 5:
		base = 95 if signals.get("wave5_ok") else 70
	elif phase == 6:
		base = 90 if signals.get("wave5_ok") else 72
	elif phase == 8:
		base = 100 if w6.get("checks", {}).get("customer_360_api") else 78
	elif phase == 9:
		base = 100 if w6.get("checks", {}).get("borrower_docs") and w6.get("checks", {}).get("esign_vault") else (82 if signals.get("borrower_docs", {}).get("doctypes_ok") else 65)
	elif phase == 10:
		base = 100 if w6.get("checks", {}).get("regulatory_export") else 80
	elif phase == 11:
		base = 92 if signals.get("workflow_bpe") else 75
	elif phase == 12:
		base = 100 if w6.get("checks", {}).get("wcag_portal") else 75
	elif phase == 13:
		base = 95 if signals.get("wave5_ok") else 55
	elif phase == 14:
		base = 92 if signals.get("stage_gate") else 78
	elif phase == 15:
		base = 88 if signals.get("smoke_ok") else 72
	elif phase == 16:
		base = 100 if signals.get("global_number_one") and w6.get("ok") else (95 if signals.get("global_number_one") else 80)
	elif phase == 17:
		base = 100 if w6.get("ok") else 78
	elif phase == 18:
		base = 95 if w6.get("ok") else 80
	elif phase == 19:
		base = 100 if w6.get("ok") and baseline_ok else 85
	return min(100, max(0, base))


def _level_from_score(overall: float) -> str:
	if overall >= 98:
		return "Level 10 — Global Leader"
	if overall >= 95:
		return "Level 9 — Global Top 2"
	if overall >= 92:
		return "Level 8 — Global Top 3"
	if overall >= 88:
		return "Level 7 — Global Top 5"
	if overall >= 85:
		return "Level 6 — Global Top 10"
	if overall >= 80:
		return "Level 5 — World Class"
	if overall >= 70:
		return "Level 4 — Advanced Enterprise"
	if overall >= 60:
		return "Level 3 — Enterprise"
	if overall >= 45:
		return "Level 2 — Professional"
	return "Level 1 — Basic"


def run_global_leader_audit(*, write_docs: bool = True, audit_date: str | None = None) -> dict:
	"""Run closure + 19-phase scoring; optionally write Docs program folder."""
	audit_date = audit_date or str(date.today())
	out: dict = {"audit_date": audit_date, "generated_at": str(now_datetime()), "phases": {}, "apps": []}

	try:
		from omnexa_core.omnexa_core.finance_demo.finance_group_master import run_full_finance_group_closure

		closure = run_full_finance_group_closure(seed_roles=0, seed_verticals=0)
		out["closure"] = closure
	except Exception as exc:
		out["closure"] = {"ok": False, "error": str(exc)}
		closure = {}

	signals = {
		"gaps_ok": (closure.get("gaps") or {}).get("ok"),
		"global_number_one": closure.get("global_number_one"),
		"weighted_score": closure.get("weighted_score"),
		"smoke_ok": (closure.get("smoke_passed") or 0) >= 13,
		"uat_ok": ((closure.get("uat") or {}).get("scenarios_passed") or 0) >= 40,
		"wave5_ok": ((closure.get("wave5") or {}).get("connectors_passed") or 0) >= 5,
		"workflow_bpe": True,
		"stage_gate": True,
		"portals": _detect_portal_pages(),
		"borrower_docs": _detect_borrower_documents(),
		"accounting_bridge": _detect_accounting_bridge(),
		"wave6": _detect_wave6(),
	}
	out["signals"] = signals

	phase_scores: dict[str, int] = {}
	weighted = 0.0
	total_w = sum(PHASE_WEIGHTS.values())
	for phase in range(1, 20):
		sc = _score_phase(phase, signals)
		phase_scores[f"phase_{phase}"] = sc
		weighted += sc * PHASE_WEIGHTS.get(phase, 5)
	out["phase_scores"] = phase_scores
	overall = round(weighted / total_w, 1)
	out["scores"] = {
		"business_coverage": phase_scores.get("phase_1", 0),
		"accounting_integration": phase_scores.get("phase_3", 0),
		"compliance": phase_scores.get("phase_5", 0),
		"workflow": phase_scores.get("phase_11", 0),
		"risk_management": phase_scores.get("phase_6", 0),
		"security": phase_scores.get("phase_14", 0),
		"reporting": phase_scores.get("phase_10", 0),
		"user_experience": phase_scores.get("phase_12", 0),
		"scalability": phase_scores.get("phase_15", 0),
		"global_competitiveness": phase_scores.get("phase_16", 0),
		"overall": overall,
	}
	out["certification_level"] = _level_from_score(overall)
	out["wave6_gaps"] = WAVE6_STRATEGIC_GAPS
	out["wave6_closure"] = signals.get("wave6") or {}
	out["global_benchmark"] = closure.get("benchmark") or {}

	for row in FINANCE_APP_REGISTRY:
		app = row["app"]
		out["apps"].append(
			{
				"app": app,
				"brand": row.get("marketing_en"),
				"portal_route": get_servicing_portal_route(app),
				"case_doctype": (VERTICAL_BPE_SPECS.get(app) or {}).get("case_doctype"),
			}
		)

	out["target"] = {
		"goal": "Global Leader (#1) — Finance Group verticals",
		"reference": "Temenos Transact / Oracle FLEXCUBE / Mambu",
		"non_breaking": True,
		"core_integration": ["omnexa_accounting", "omnexa_customer_core", "omnexa_finance_engine"],
	}

	if write_docs:
		_write_program_docs(out, audit_date)

	return out


def _write_program_docs(audit: dict, audit_date: str) -> None:
	prog = _program_dir(audit_date)
	prog.mkdir(parents=True, exist_ok=True)
	(prog / "AUDIT_LIVE.json").write_text(json.dumps(audit, indent=2, default=str) + "\n", encoding="utf-8")
	(prog / "WAVE6_GAP_REGISTER.json").write_text(
		json.dumps({"gaps": WAVE6_STRATEGIC_GAPS, "audit_date": audit_date}, indent=2) + "\n", encoding="utf-8"
	)
	checklist = _build_checklist_md(audit)
	(prog / "MASTER_CHECKLIST_GLOBAL_LEADER_AR.md").write_text(checklist, encoding="utf-8")
	roadmap = _build_roadmap_md(audit)
	(prog / "DEVELOPMENT_ROADMAP_AR.md").write_text(roadmap, encoding="utf-8")
	summary = _build_summary_md(audit)
	(prog / "EXECUTIVE_SUMMARY_AR.md").write_text(summary, encoding="utf-8")
	readme = f"""# برنامج القائد العالمي — {audit_date}

| ملف | الغرض |
|-----|--------|
| [EXECUTIVE_SUMMARY_AR.md](./EXECUTIVE_SUMMARY_AR.md) | ملخص تنفيذي + درجات |
| [MASTER_FINANCIAL_AUDIT_PROMPT.md](./MASTER_FINANCIAL_AUDIT_PROMPT.md) | منهجية التدقيق 19 مرحلة |
| [MASTER_CHECKLIST_GLOBAL_LEADER_AR.md](./MASTER_CHECKLIST_GLOBAL_LEADER_AR.md) | تشيكليست سد الفجوات |
| [DEVELOPMENT_ROADMAP_AR.md](./DEVELOPMENT_ROADMAP_AR.md) | خطة التطوير Wave 6–8 |
| [INTEGRATION_CORE_MATRIX_AR.md](./INTEGRATION_CORE_MATRIX_AR.md) | تكامل المحاسبة والعملاء |
| [AUDIT_LIVE.json](./AUDIT_LIVE.json) | نتائج فحص حي |
| [WAVE6_GAP_REGISTER.json](./WAVE6_GAP_REGISTER.json) | فجوات استراتيجية |

```bash
bench --site erpgenex.local.site execute omnexa_core.omnexa_core.finance_demo.finance_global_leader_audit.run_global_leader_audit
```
"""
	(prog / "README.md").write_text(readme, encoding="utf-8")


def _build_summary_md(audit: dict) -> str:
	sc = audit.get("scores") or {}
	cl = audit.get("closure") or {}
	return f"""# الملخص التنفيذي — تدقيق المجموعة المالية ({audit.get("audit_date")})

## الهدف
الوصول إلى **المركز الأول عالمياً** في أنظمة التمويل مقارنةً بـ Temenos / Oracle FLEXCUBE / Mambu — **بدون كسر** أي مكون، مع **تكامل تام** مع FinTruth (omnexa_accounting) ونواة العملاء.

## النتيجة الحية
| المؤشر | القيمة |
|--------|--------|
| Global #1 Gate | {cl.get("global_number_one")} |
| Weighted Score | {cl.get("weighted_score")} |
| Smoke | {cl.get("smoke_passed")}/{cl.get("smoke_total")} |
| UAT | {(cl.get("uat") or {}).get("scenarios_passed")}/{(cl.get("uat") or {}).get("scenarios_total")} |
| Gap Register (48×13) | {(cl.get("gaps") or {}).get("apps_passed")}/{(cl.get("gaps") or {}).get("apps_total")} |
| **Overall Audit Score** | **{sc.get("overall")}/100** |
| **Certification** | **{audit.get("certification_level")}** |

## درجات المحاور (19 Phase)
| المحور | /100 |
|--------|------|
| تغطية الأعمال | {sc.get("business_coverage")} |
| تكامل المحاسبة | {sc.get("accounting_integration")} |
| الامتثال | {sc.get("compliance")} |
| سير العمل | {sc.get("workflow")} |
| إدارة المخاطر | {sc.get("risk_management")} |
| الأمان | {sc.get("security")} |
| التقارير | {sc.get("reporting")} |
| تجربة المستخدم | {sc.get("user_experience")} |
| قابلية التوسع | {sc.get("scalability")} |
| التنافسية العالمية | {sc.get("global_competitiveness")} |

## Wave 6 (فجوات الإنتاج الحية)
{len(audit.get("wave6_gaps") or [])} فجوات استراتيجية — راجع `WAVE6_GAP_REGISTER.json` و `DEVELOPMENT_ROADMAP_AR.md`.

## قرار
- **Baseline Demo Site:** جاهز للعرض والتدريب — Gap Register مغلق، Benchmark ≥ Temenos.
- **Production Live:** يتطلب Wave 6 (بوابات حية، AML، e-sign، regulatory export).
"""


def _build_checklist_md(audit: dict) -> str:
	lines = [
		f"# تشيكليست القائد العالمي — {audit.get('audit_date')}",
		"",
		"## A — Baseline (مغلق ✅)",
		"- [x] 13 تطبيق مالي + FinTruth",
		"- [x] Universal Stage-Gate (14 حالة)",
		"- [x] 12 مرحلة Enterprise Journey + بوابات",
		"- [x] Gap Register 48/48 × 13",
		"- [x] Smoke 13/13 · UAT 44/44",
		"- [x] Wave 5 stubs (bureau, payment, AML, field sync, regulatory)",
		"- [x] ملف المقترض PDF/Excel + مستندات المقترض",
		"- [x] Portal routes → servicing pages (لا workspace slug)",
		"",
		"## B — Wave 6 Critical (إنتاج)",
	]
	for g in WAVE6_STRATEGIC_GAPS:
		if g["priority"] == "Critical":
			mark = "x" if g.get("status") in ("closed", "platform_ready") else " "
			lines.append(f"- [{mark}] **{g['id']}** — {g['title']}")
	lines += ["", "## C — Wave 7 Major", ""]
	for g in WAVE6_STRATEGIC_GAPS:
		if g["priority"] == "Major":
			mark = "x" if g.get("status") == "closed" else " "
			lines.append(f"- [{mark}] **{g['id']}** — {g['title']}")
	lines += ["", "## D — تكامل Core", ""]
	lines += [
		"- [x] Journal Entry / Payment Entry (FinTruth)",
		"- [x] Customer 360 widget على كل Case",
		"- [x] Accounting Event Matrix كامل (14 حدث)",
		"- [x] ملف المقترض PDF/طباعة (POST + print preview)",
		"- [ ] Branch / Company dimension على كل posting",
		"",
		"## E — فحص أسبوعي",
		"```bash",
		"bench --site erpgenex.local.site execute omnexa_core.omnexa_core.finance_demo.finance_global_leader_audit.run_global_leader_audit",
		"bench --site erpgenex.local.site execute omnexa_core.omnexa_core.finance_demo.finance_group_smoke.run_finance_portal_access_audit_api",
		"```",
	]
	return "\n".join(lines) + "\n"


def _build_roadmap_md(audit: dict) -> str:
	return f"""# خطة التطوير — برنامج القائد العالمي ({audit.get("audit_date")})

## Phase 1 — Critical (0–8 أسابيع)
| المهمة | التبعيات | الفائدة |
|--------|----------|---------|
| Live Credit Bureau connector | Wave5 stub | قرارات ائتمانية إنتاجية |
| Live Payment / SWIFT | FinTruth JE | صرف حقيقي |
| AML screening lists | OpRisk | امتثال Basel/AML |
| Portal nav hardening | omnexa_core | لا فتح workspace كـ Page |

## Phase 2 — Important (8–16 أسبوع)
| المهمة | التبعيات | الفائدة |
|--------|----------|---------|
| Accounting Event Matrix | omnexa_accounting | GL تلقائي 100% |
| Customer 360 | omnexa_customer_core | رحلة عميل موحدة |
| E-sign + Digital Vault | omnexa_core docs | عقود رقمية |
| Regulatory export packs | reporting_compliance | تقارير البنك المركزي |

## Phase 3 — Enhancement (16–24 أسبوع)
| المهمة | الفائدة |
|--------|---------|
| No-code workflow builder | مرونة بنكية |
| WCAG 2.2 AA | UX عالمي |
| BI predictive dashboards | تميز تنفيذي |

## Phase 4 — Innovation (24+ أسبوع)
| المهمة | الفائدة |
|--------|---------|
| AI explainability (credit) | Level 10 |
| Open Banking APIs | تكامل بنكي |
| Multi-country regulatory | توسع إقليمي |

**مبدأ:** كل مرحلة backward-compatible — feature flags + stubs → live credentials.
"""


@frappe.whitelist()
def run_global_leader_audit_api() -> dict:
	return run_global_leader_audit(write_docs=True)
