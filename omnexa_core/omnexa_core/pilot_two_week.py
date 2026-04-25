# Copyright (c) 2026, ErpGenEx and contributors
# SPDX-License-Identifier: MIT
"""Pilot أسبوعان — تسجيل لقطات تشغيلية حقيقية من قاعدة البيانات وتقرير انحرافات (E3.1 / G2).

**تسجيل لقطة أسبوع (يُنفَّذ مرة أسبوعياً أو حسب الجدول)::**

    bench --site <site> execute omnexa_core.omnexa_core.pilot_two_week.record_pilot_snapshot \\
        --kwargs '{"pilot_code": "FINANCE_Q2", "week_index": 1}'

**تقرير انحرافات (بعد جمع أسبوعين على الأقل)::**

    bench --site <site> execute omnexa_core.omnexa_core.pilot_two_week.print_pilot_deviation_report \\
        --kwargs '{"pilot_code": "FINANCE_Q2"}'

**رجعي (تجربة): تقسيم من تاريخ إلى «نصفين» (W1 / W2) من بيانات DB الفعلية::**

    bench --site <site> execute omnexa_core.omnexa_core.pilot_two_week.record_retrospective_pilot_snapshots \\
        --kwargs '{"pilot_code": "APR2026_DEMO", "start_date": "2026-04-01"}'

الملفات تُحفظ تحت ``logs/pilot_two_week/<pilot_code>/`` في جذر الـ bench (مع ``get_bench_path()``).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import frappe
from frappe.utils import add_to_date, cint, get_bench_path, get_datetime, now_datetime


def _pilot_dir(pilot_code: str) -> Path:
	safe = "".join(c for c in pilot_code.strip() if c.isalnum() or c in ("-", "_")).strip("_-") or "pilot"
	base = Path(get_bench_path()) / "logs" / "pilot_two_week" / safe
	base.mkdir(parents=True, exist_ok=True)
	return base


def _count_error_log(since) -> int:
	if not frappe.db.has_table("Error Log"):
		return 0
	return cint(
		frappe.db.count(
			"Error Log",
			{"creation": (">", since)},
		)
	)


def _top_error_methods(limit: int = 15) -> list[dict[str, Any]]:
	if not frappe.db.has_table("Error Log"):
		return []
	return (
		frappe.db.sql(
			"""
			SELECT `method` AS method, COUNT(*) AS count
			FROM `tabError Log`
			WHERE `creation` > %(since)s
			GROUP BY `method`
			ORDER BY count DESC
			LIMIT %(limit)s
			""",
			{"since": add_to_date(now_datetime(), days=-14), "limit": limit},
			as_dict=True,
		)
		or []
	)


def _email_queue_status_counts(since) -> dict[str, int]:
	if not frappe.db.has_table("Email Queue"):
		return {}
	out: dict[str, int] = {}
	for row in frappe.db.sql(
		"""
		SELECT status, COUNT(*) AS c
		FROM `tabEmail Queue`
		WHERE modified > %(since)s
		GROUP BY status
		""",
		{"since": since},
		as_dict=True,
	):
		out[row.status] = cint(row.c)
	return out


def _doc_created_count(doctype: str, since) -> int | None:
	if not frappe.db.exists("DocType", doctype):
		return None
	return cint(frappe.db.count(doctype, {"creation": (">", since)}))


def _count_error_log_between(start, end, *, start_exclusive: bool = False) -> int:
	if not frappe.db.has_table("Error Log"):
		return 0
	op = ">" if start_exclusive else ">="
	return cint(
		frappe.db.sql(
			f"SELECT COUNT(*) FROM `tabError Log` WHERE `creation` {op} %s AND `creation` <= %s",
			(start, end),
		)[0][0]
	)


def _top_error_methods_between(start, end, limit: int = 15, *, start_exclusive: bool = False) -> list[dict[str, Any]]:
	if not frappe.db.has_table("Error Log"):
		return []
	op = ">" if start_exclusive else ">="
	return (
		frappe.db.sql(
			f"""
			SELECT `method` AS method, COUNT(*) AS count
			FROM `tabError Log`
			WHERE `creation` {op} %(start)s AND `creation` <= %(end)s
			GROUP BY `method`
			ORDER BY count DESC
			LIMIT %(limit)s
			""",
			{"start": start, "end": end, "limit": limit},
			as_dict=True,
		)
		or []
	)


def _email_queue_status_between(start, end, *, start_exclusive: bool = False) -> dict[str, int]:
	if not frappe.db.has_table("Email Queue"):
		return {}
	out: dict[str, int] = {}
	op = ">" if start_exclusive else ">="
	for row in frappe.db.sql(
		f"""
		SELECT status, COUNT(*) AS c
		FROM `tabEmail Queue`
		WHERE modified {op} %(start)s AND modified <= %(end)s
		GROUP BY status
		""",
		{"start": start, "end": end},
		as_dict=True,
	):
		out[row.status] = cint(row.c)
	return out


def _communication_email_sent_between(start, end, *, start_exclusive: bool = False) -> int:
	if not frappe.db.has_table("Communication"):
		return 0
	op = ">" if start_exclusive else ">="
	return cint(
		frappe.db.sql(
			f"""
			SELECT COUNT(*) FROM `tabCommunication`
			WHERE communication_medium = 'Email' AND sent_or_received = 'Sent'
			AND creation {op} %s AND creation <= %s
			""",
			(start, end),
		)[0][0]
	)


def _doc_created_between(doctype: str, start, end, *, start_exclusive: bool = False) -> int | None:
	if not frappe.db.exists("DocType", doctype):
		return None
	table = f"tab{doctype}"
	op = ">" if start_exclusive else ">="
	return cint(
		frappe.db.sql(
			f"SELECT COUNT(*) FROM `{table}` WHERE `creation` {op} %s AND `creation` <= %s",
			(start, end),
		)[0][0]
	)


def collect_pilot_metrics_for_window(start, end, *, start_exclusive: bool = False) -> dict[str, Any]:
	"""مقاييس مجمّعة داخل نافذة زمنية [start, end] (حدود شاملة).

	يُعاد استخدام مفاتيح ``error_log_7d`` / ``top_error_methods_14d`` إلخ لتتوافق مع ``print_pilot_deviation_report`` دون تغيير المنطق.
	"""
	queues: dict[str, Any] = {}
	try:
		from frappe.utils.background_jobs import get_queue, get_queue_list

		for name in get_queue_list():
			q = get_queue(name)
			queues[name] = {"pending": cint(q.count)}
	except Exception as e:
		queues = {"_error": repr(e)}

	scheduler: Any = None
	try:
		from frappe.utils.scheduler import get_scheduler_status

		scheduler = get_scheduler_status()
	except Exception as e:
		scheduler = {"_error": repr(e)}

	n_err = _count_error_log_between(start, end, start_exclusive=start_exclusive)
	return {
		"retrospective_window": {"start": str(start), "end": str(end), "start_exclusive": start_exclusive},
		"error_log_24h": n_err,
		"error_log_7d": n_err,
		"error_log_14d": n_err,
		"top_error_methods_14d": _top_error_methods_between(start, end, 15, start_exclusive=start_exclusive),
		"queues": queues,
		"scheduler": scheduler,
		"email_queue_by_status_7d": _email_queue_status_between(start, end, start_exclusive=start_exclusive),
		"communication_email_sent_7d": _communication_email_sent_between(start, end, start_exclusive=start_exclusive),
		"sales_invoice_created_14d": _doc_created_between("Sales Invoice", start, end, start_exclusive=start_exclusive),
		"purchase_invoice_created_14d": _doc_created_between("Purchase Invoice", start, end, start_exclusive=start_exclusive),
	}


def collect_pilot_metrics() -> dict[str, Any]:
	"""قراءة فقط — مؤشرات تشغيلية من الموقع الحالي."""
	now = now_datetime()
	since_24h = add_to_date(now, hours=-24, as_datetime=True)
	since_7d = add_to_date(now, days=-7, as_datetime=True)
	since_14d = add_to_date(now, days=-14, as_datetime=True)

	queues: dict[str, Any] = {}
	try:
		from frappe.utils.background_jobs import get_queue, get_queue_list

		for name in get_queue_list():
			q = get_queue(name)
			queues[name] = {"pending": cint(q.count)}
	except Exception as e:
		queues = {"_error": repr(e)}

	scheduler: Any = None
	try:
		from frappe.utils.scheduler import get_scheduler_status

		scheduler = get_scheduler_status()
	except Exception as e:
		scheduler = {"_error": repr(e)}

	return {
		"error_log_24h": _count_error_log(since_24h),
		"error_log_7d": _count_error_log(since_7d),
		"error_log_14d": _count_error_log(since_14d),
		"top_error_methods_14d": _top_error_methods(15),
		"queues": queues,
		"scheduler": scheduler,
		"email_queue_by_status_7d": _email_queue_status_counts(since_7d),
		"communication_email_sent_7d": (
			cint(
				frappe.db.count(
					"Communication",
					{
						"communication_medium": "Email",
						"sent_or_received": "Sent",
						"creation": (">", since_7d),
					},
				)
			)
			if frappe.db.has_table("Communication")
			else 0
		),
		"sales_invoice_created_14d": _doc_created_count("Sales Invoice", since_14d),
		"purchase_invoice_created_14d": _doc_created_count("Purchase Invoice", since_14d),
	}


def _snapshot_path(pilot_dir: Path, week_index: int) -> Path:
	stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
	return pilot_dir / f"W{int(week_index)}_{stamp}.json"


@frappe.whitelist()
def record_pilot_snapshot(pilot_code: str, week_index: int = 1) -> dict[str, Any]:
	"""يحفظ JSON لقطة أسبوعية (بيانات حقيقية من DB). System Manager فقط."""
	frappe.only_for("System Manager")
	pilot_code = (pilot_code or "").strip()
	if not pilot_code:
		frappe.throw(frappe._("pilot_code is required"))

	wi = cint(week_index)
	if wi not in (1, 2):
		frappe.throw(frappe._("week_index must be 1 or 2"))

	payload: dict[str, Any] = {
		"schema": "omnexa_pilot_snapshot_v1",
		"site": frappe.local.site,
		"pilot_code": pilot_code,
		"week_index": wi,
		"collected_at": datetime.now(timezone.utc).isoformat(),
		"frappe_version": getattr(frappe, "__version__", None),
		"metrics": collect_pilot_metrics(),
	}

	pdir = _pilot_dir(pilot_code)
	path = _snapshot_path(pdir, wi)
	path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

	return {"ok": True, "path": str(path), "pilot_code": pilot_code, "week_index": wi}


@frappe.whitelist()
def record_retrospective_pilot_snapshots(pilot_code: str, start_date: str = "2026-04-01") -> dict[str, Any]:
	"""يقسّم الفترة [start_date 00:00:00، الآن] إلى نصفين زمنيين ويحفظ لقطتين W1/W2 من DB (رجعي للتجربة). System Manager فقط."""
	frappe.only_for("System Manager")
	pilot_code = (pilot_code or "").strip()
	if not pilot_code:
		frappe.throw(frappe._("pilot_code is required"))

	start = get_datetime(f"{(start_date or '').strip()} 00:00:00")
	end = now_datetime()
	if start >= end:
		frappe.throw(frappe._("start_date must be before current time"))

	mid = start + (end - start) / 2
	pdir = _pilot_dir(pilot_code)
	out: dict[str, Any] = {
		"ok": True,
		"pilot_code": pilot_code,
		"start": str(start),
		"end": str(end),
		"midpoint": str(mid),
		"retrospective": True,
	}

	for wi, w_start, w_end, start_exclusive in (
		(1, start, mid, False),
		(2, mid, end, True),
	):
		payload: dict[str, Any] = {
			"schema": "omnexa_pilot_snapshot_v1",
			"site": frappe.local.site,
			"pilot_code": pilot_code,
			"week_index": wi,
			"retrospective": True,
			"retrospective_midpoint": str(mid),
			"collected_at": datetime.now(timezone.utc).isoformat(),
			"frappe_version": getattr(frappe, "__version__", None),
			"metrics": collect_pilot_metrics_for_window(w_start, w_end, start_exclusive=start_exclusive),
		}
		path = _snapshot_path(pdir, wi)
		path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
		out[f"w{wi}_path"] = str(path)

	return out


def _load_snapshots(pilot_dir: Path) -> list[dict[str, Any]]:
	files = sorted(pilot_dir.glob("W*.json"))
	out: list[dict[str, Any]] = []
	for p in files:
		try:
			out.append(json.loads(p.read_text(encoding="utf-8")))
		except Exception:
			continue
	return out


def _aggregate_week(snapshots: list[dict[str, Any]], week: int) -> dict[str, Any] | None:
	rows = [s for s in snapshots if cint(s.get("week_index")) == week]
	if not rows:
		return None
	# آخر لقطة للأسبوع تمثل أحدث حالة نهاية الأسبوع
	last = rows[-1]
	m = last.get("metrics") or {}
	return {
		"week_index": week,
		"snapshots_count": len(rows),
		"last_collected_at": last.get("collected_at"),
		"error_log_7d": m.get("error_log_7d"),
		"error_log_14d": m.get("error_log_14d"),
		"top_error_methods_14d": m.get("top_error_methods_14d") or [],
		"queues": m.get("queues") or {},
		"email_queue_by_status_7d": m.get("email_queue_by_status_7d") or {},
		"communication_email_sent_7d": m.get("communication_email_sent_7d"),
		"sales_invoice_created_14d": m.get("sales_invoice_created_14d"),
		"purchase_invoice_created_14d": m.get("purchase_invoice_created_14d"),
	}


def build_pilot_deviation_report(pilot_code: str) -> dict[str, Any]:
	"""يقارن أسبوع 1 مقابل أسبوع 2 من آخر لقطات محفوظة لكل أسبوع."""
	pilot_code = (pilot_code or "").strip()
	if not pilot_code:
		frappe.throw(frappe._("pilot_code is required"))

	pdir = _pilot_dir(pilot_code)
	snapshots = _load_snapshots(pdir)
	w1 = _aggregate_week(snapshots, 1)
	w2 = _aggregate_week(snapshots, 2)

	deviations: list[dict[str, Any]] = []

	def _delta(label: str, a: Any, b: Any) -> None:
		if a is None and b is None:
			return
		try:
			ai, bi = cint(a), cint(b)
			deviations.append(
				{
					"metric": label,
					"week1_end": ai,
					"week2_end": bi,
					"delta": bi - ai,
				}
			)
		except Exception:
			deviations.append({"metric": label, "week1_end": a, "week2_end": b, "delta": None})

	if w1 and w2:
		_delta("error_log_7d", w1.get("error_log_7d"), w2.get("error_log_7d"))
		_delta("error_log_14d", w1.get("error_log_14d"), w2.get("error_log_14d"))
		_delta("communication_email_sent_7d", w1.get("communication_email_sent_7d"), w2.get("communication_email_sent_7d"))
		_delta("sales_invoice_created_14d", w1.get("sales_invoice_created_14d"), w2.get("sales_invoice_created_14d"))
		_delta("purchase_invoice_created_14d", w1.get("purchase_invoice_created_14d"), w2.get("purchase_invoice_created_14d"))

		methods_w1 = {r["method"]: cint(r["count"]) for r in (w1.get("top_error_methods_14d") or []) if r.get("method")}
		methods_w2 = {r["method"]: cint(r["count"]) for r in (w2.get("top_error_methods_14d") or []) if r.get("method")}
		# ظهور جديد فعلي في نافذة 14 يوماً (تجاهل تبديل صفوف بنفس العدد ضمن LIMIT)
		new_hot = sorted(((m, methods_w2[m]) for m in methods_w2 if m not in methods_w1), key=lambda x: -x[1])[:10]
	else:
		new_hot = []

	return {
		"pilot_code": pilot_code,
		"snapshots_total": len(snapshots),
		"week1": w1,
		"week2": w2,
		"deviations_numeric": deviations,
		"top_error_methods_escalated_or_new": [{"method": m, "approx_count_w2": c} for m, c in new_hot],
		"notes": (
			"Compare week1 vs week2 using the last snapshot stored for each week. "
			"Record week 1 end and week 2 end via record_pilot_snapshot with week_index=1 then 2."
		),
	}


@frappe.whitelist()
def print_pilot_deviation_report(pilot_code: str) -> str:
	"""Markdown عربي + JSON مدمج كتعليق HTML — System Manager فقط."""
	frappe.only_for("System Manager")
	rep = build_pilot_deviation_report(pilot_code)
	w1, w2 = rep.get("week1"), rep.get("week2")

	lines = [
		f"# تقرير انحرافات Pilot — `{rep['pilot_code']}`",
		"",
		f"- **عدد اللقطات المحفوظة:** {rep['snapshots_total']}",
		"",
		"## ملخص الأسبوعين",
		"",
	]
	if not w1 or not w2:
		lines.append("> **تنبيه:** يلزم لقطة واحدة على الأقل لكل من `week_index=1` و`week_index=2` لتوليد مقارنة كاملة.")
		lines.append("")
	if w1:
		lines.append(f"### نهاية الأسبوع 1 (آخر لقطة — {w1.get('last_collected_at')})")
		lines.append(f"- Error Log (7d): **{w1.get('error_log_7d')}**")
		lines.append(f"- Communication بريد صادر (7d): **{w1.get('communication_email_sent_7d')}**")
		lines.append("")
	if w2:
		lines.append(f"### نهاية الأسبوع 2 (آخر لقطة — {w2.get('last_collected_at')})")
		lines.append(f"- Error Log (7d): **{w2.get('error_log_7d')}**")
		lines.append(f"- Communication بريد صادر (7d): **{w2.get('communication_email_sent_7d')}**")
		lines.append("")

	lines.append("## انحرافات رقمية (أسبوع 2 − أسبوع 1)")
	lines.append("")
	if rep["deviations_numeric"]:
		lines.append("| المؤشر | نهاية أسبوع 1 | نهاية أسبوع 2 | الفرق |")
		lines.append("|--------|----------------|----------------|-------|")
		for d in rep["deviations_numeric"]:
			lines.append(
				f"| {d['metric']} | {d.get('week1_end')} | {d.get('week2_end')} | {d.get('delta')} |"
			)
	else:
		lines.append("| (لا توجد مقارنة كاملة بعد) |")
	lines.append("")

	if rep["top_error_methods_escalated_or_new"]:
		lines.append("## طرق أخطاء ساخنة أو متصاعدة (مرجع)")
		lines.append("")
		for row in rep["top_error_methods_escalated_or_new"]:
			lines.append(f"- `{row['method']}` — تقريباً **{row['approx_count_w2']}** في نافذة 14 يوماً لأسبوع 2")
		lines.append("")

	lines.append("## JSON خام (للأرشفة)")
	lines.append("")
	lines.append("```json")
	lines.append(json.dumps(rep, ensure_ascii=False, indent=2, default=str))
	lines.append("```")

	return "\n".join(lines)


@frappe.whitelist()
def export_pilot_deviation_report_file(pilot_code: str) -> dict[str, Any]:
	"""يكتب تقرير Markdown إلى ``logs/pilot_two_week/<pilot>/report_<UTC>.md``."""
	frappe.only_for("System Manager")
	body = print_pilot_deviation_report(pilot_code)
	pdir = _pilot_dir((pilot_code or "").strip())
	stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
	out = pdir / f"report_{stamp}.md"
	out.write_text(body, encoding="utf-8")
	return {"ok": True, "path": str(out)}


def _count_enabled_system_users() -> int:
	if not frappe.db.has_table("User"):
		return 0
	return cint(
		frappe.db.count(
			"User",
			{
				"enabled": 1,
				"user_type": "System User",
				"name": ("not in", ["Administrator", "Guest"]),
			},
		)
	)


def _count_doc_between_by_table(table: str, start, end, *, start_exclusive: bool = False) -> int:
	if not frappe.db.has_table(table.replace("tab", "")):
		# best-effort fallback; doctype existence checked elsewhere when needed
		return 0
	op = ">" if start_exclusive else ">="
	return cint(
		frappe.db.sql(
			f"SELECT COUNT(*) FROM `{table}` WHERE `creation` {op} %s AND `creation` <= %s",
			(start, end),
		)[0][0]
	)


def _top_version_ref_doctypes_between(start, end, limit: int = 12) -> list[dict[str, Any]]:
	"""Best-effort activity signal via Version table (audit trail)."""
	if not frappe.db.has_table("Version"):
		return []
	return (
		frappe.db.sql(
			"""
			SELECT ref_doctype, COUNT(*) AS c
			FROM `tabVersion`
			WHERE creation >= %(start)s AND creation <= %(end)s
			GROUP BY ref_doctype
			ORDER BY c DESC
			LIMIT %(limit)s
			""",
			{"start": start, "end": end, "limit": int(limit)},
			as_dict=True,
		)
		or []
	)


_PILOT_ACTIVITY_EXCLUDE: set[str] = {
	"Version",
	"Workspace",
	"Module Onboarding",
	"Custom Field",
	"DocType",
	"Property Setter",
	"System Settings",
	"Global Search Settings",
	"Log Settings",
}


def _suggest_pilot_paths_from_activity(activity_rows: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
	"""Suggest realistic must-pass doctypes from activity, excluding setup-heavy doctypes."""
	out: list[dict[str, Any]] = []
	for row in activity_rows:
		dt = (row.get("ref_doctype") or "").strip()
		c = cint(row.get("c"))
		if not dt or dt in _PILOT_ACTIVITY_EXCLUDE:
			continue
		out.append({"doctype": dt, "count": c})
		if len(out) >= limit:
			break
	return out


@frappe.whitelist()
def export_prefilled_pilot_kit_file(
	pilot_code: str,
	start_date: str = "2026-04-01",
) -> dict[str, Any]:
	"""يولّد ملف Pilot Kit مُعبّأ بأرقام حقيقية من DB تحت logs/pilot_kits/ (System Manager فقط)."""
	frappe.only_for("System Manager")
	pilot_code = (pilot_code or "").strip()
	if not pilot_code:
		frappe.throw(frappe._("pilot_code is required"))

	start = get_datetime(f"{(start_date or '').strip()} 00:00:00")
	end = now_datetime()
	mid = start + (end - start) / 2

	# Reuse our window collector for consistent metrics
	w1 = collect_pilot_metrics_for_window(start, mid, start_exclusive=False)
	w2 = collect_pilot_metrics_for_window(mid, end, start_exclusive=True)

	# Extra business-ish counts since start_date
	sales_since = _doc_created_between("Sales Invoice", start, end) or 0
	purchase_since = _doc_created_between("Purchase Invoice", start, end) or 0

	# These doctypes may not exist on every stack; keep best-effort
	je_since = _doc_created_between("Journal Entry", start, end) or 0
	pe_since = _doc_created_between("Payment Entry", start, end) or 0

	active_users = _count_enabled_system_users()
	error_log_since = _count_error_log_between(start, end)
	top_activity = _top_version_ref_doctypes_between(start, end, 12)
	suggested = _suggest_pilot_paths_from_activity(top_activity, 5)

	lines: list[str] = []
	lines.append("# Pilot Kit — نسخة مُعبّأة (بيانات حقيقية للتجربة)")
	lines.append("")
	lines.append(f"- **الموقع:** `{getattr(frappe.local, 'site', None)}`")
	lines.append(f"- **رمز الـ Pilot:** `{pilot_code}`")
	lines.append(f"- **الفترة:** من `{start}` حتى `{end}` (منتصف: `{mid}`)")
	lines.append("")
	lines.append("## 1) تعريف ICP (تجربة على بيانات حقيقية من الموقع)")
	lines.append("")
	lines.append("| الحقل | القيمة |")
	lines.append("|--------|--------|")
	lines.append(f"| اسم الـ Pilot / الرمز | `{pilot_code}` |")
	lines.append("| القطاع | (تجربة — لم يُحدّد) |")
	lines.append(f"| المستخدمون النشطون (System Users enabled) | **{active_users}** |")
	lines.append(f"| حجم معاملات منذ {start_date} (تقريبي) | SI={sales_since}, PI={purchase_since}, JE={je_since}, PE={pe_since} |")
	lines.append("")
	lines.append("### إشارات نشاط (من سجل Version) — لتحديد مسارات Must-Pass الواقعية")
	lines.append("")
	if top_activity:
		lines.append("| DocType | تعديلات/أحداث (تقريباً) |")
		lines.append("|--------|--------------------------|")
		for row in top_activity:
			dt = row.get("ref_doctype") or ""
			c = cint(row.get("c"))
			if dt:
				lines.append(f"| `{dt}` | **{c}** |")
	else:
		lines.append("> لا توجد بيانات Version أو لا يمكن قراءتها على هذا الموقع.")
	lines.append("")
	lines.append("## 2) قائمة Must-Pass (تجربة — تحتاج تأكيد Product/Finance)")
	lines.append("")
	lines.append("> هذه النسخة تُعبّئ الأرقام فقط. ضعوا ✓/✗ بعد تنفيذ السيناريوهات فعلياً.")
	if suggested:
		lines.append("")
		lines.append("**مسارات مقترحة تلقائياً من النشاط الحقيقي (Version):**")
		for row in suggested:
			lines.append(f"- `{row['doctype']}` — نشاط تقريبي **{row['count']}**")
	lines.append("")
	lines.append("| # | المسار | الوصف المختصر | ✓ | ملاحظات |")
	lines.append("|---|--------|-----------------|---|----------|")
	lines.append("| 1 | تسجيل دخول + صلاحيات فرع/شركة | | | |")
	if suggested:
		for idx, row in enumerate(suggested, start=2):
			lines.append(f"| {idx} | `{row['doctype']}` | سيناريو تشغيل/تعديل/اعتماد على هذا النوع | | |")
		last_idx = len(suggested) + 2
		lines.append(f"| {last_idx} | رقابة: Audit / Alerts | | | |")
	else:
		lines.append("| 2 | مبيعات → فاتورة | | | |")
		lines.append("| 3 | مشتريات / دفعات | | | |")
		lines.append("| 4 | بنوك / تسوية | | | |")
		lines.append("| 5 | إقفال فترة / تقارير حرجة | | | |")
		lines.append("| 6 | رقابة: Audit / Alerts | | | |")
	lines.append("")
	lines.append("## 3) معايير قبول (أرقام حقيقية من DB حيث أمكن)")
	lines.append("")
	lines.append("| المعيار | الهدف | قياس فعلي |")
	lines.append("|---------|--------|-----------|")
	lines.append("| أخطاء Error Log / الفترة | (حددوا هدفاً) | "
			 f"**{error_log_since}** (من {start_date} حتى الآن) |")
	lines.append("| Sev-1 مفتوحة | 0 | (تحتاج تعريف Sev في التشغيل) |")
	lines.append("| فشل migrate | 0 | (يتطلب سجل تشغيل/CI) |")
	lines.append("")
	lines.append("## 4) لقطات الأسبوعين (W1/W2) — ملخص انحرافات")
	lines.append("")
	lines.append("### W1 (start → midpoint)")
	lines.append(f"- Error Log (window): **{w1.get('error_log_14d')}**")
	lines.append(f"- بريد صادر (Communication Sent): **{w1.get('communication_email_sent_7d')}**")
	lines.append("")
	lines.append("### W2 (midpoint → end)")
	lines.append(f"- Error Log (window): **{w2.get('error_log_14d')}**")
	lines.append(f"- بريد صادر (Communication Sent): **{w2.get('communication_email_sent_7d')}**")
	lines.append("")
	lines.append("## 5) روابط الأدلة (Artifacts)")
	lines.append("")
	lines.append(f"- حزمة أدلة G3 (آخر تشغيل): `logs/g3_evidence_bundle/erpgenex.local.site_20260424T010949Z/`")
	lines.append(f"- تقرير Pilot (الرمز نفسه): `logs/pilot_two_week/{pilot_code}/` (لقطات + report_*.md)")
	lines.append("")
	lines.append("## 6) التوقيعات (للاعتماد)")
	lines.append("")
	lines.append("| الدور | الاسم | التاريخ |")
	lines.append("|--------|-------|---------|")
	lines.append("| Product | | |")
	lines.append("| Finance / التشغيل | | |")
	lines.append("| Engineering | | |")

	body = "\n".join(lines) + "\n"

	base = Path(get_bench_path()) / "logs" / "pilot_kits"
	base.mkdir(parents=True, exist_ok=True)
	stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
	site = getattr(frappe.local, "site", "site")
	out = base / f"pilot_kit_prefill_{site}_{pilot_code}_{stamp}.md"
	out.write_text(body, encoding="utf-8")
	return {"ok": True, "path": str(out), "pilot_code": pilot_code, "start": str(start), "end": str(end)}
