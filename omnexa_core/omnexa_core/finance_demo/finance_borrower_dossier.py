# Copyright (c) 2026, ErpGenEx
"""Unified borrower / finance case complete file — PDF & Excel across Finance Group verticals."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr, format_datetime, formatdate, now_datetime

from omnexa_core.omnexa_core.finance_demo.finance_stage_gate import get_progress_tracker
from omnexa_core.omnexa_core.finance_demo.finance_vertical_specs import VERTICAL_BPE_SPECS, VERTICAL_BPE_DOCTYPES
from omnexa_core.omnexa_core.finance_demo.finance_workflow_journey import ENTERPRISE_WORKFLOW_STEPS

LAYOUT_FIELDTYPES = frozenset({"Section Break", "Column Break", "Tab Break", "Fold", "Heading", "HTML"})
SKIP_FIELDNAMES = frozenset({"amended_from", "amended_from_name"})

DOSSIER_REPORT_NAME = "Finance Borrower Complete File"


def _app_for_doctype(doctype: str) -> dict | None:
	for app, spec in VERTICAL_BPE_SPECS.items():
		if spec.get("case_doctype") == doctype:
			return {"app": app, **spec}
	return None


def get_finance_case_doctypes_boot() -> list[dict]:
	"""Desk boot payload — finance case doctypes for filters and client scripts."""
	out: list[dict] = []
	for app, spec in VERTICAL_BPE_SPECS.items():
		dt = spec.get("case_doctype")
		if not dt or spec.get("skip_seed") and spec.get("standard_doctype"):
			continue
		if not frappe.db.exists("DocType", dt):
			continue
		out.append(
			{
				"doctype": dt,
				"app": app,
				"brand": spec.get("brand") or app,
				"label_en": dt,
				"label_ar": dt,
			}
		)
	return out


def _borrower_title(doc, spec: dict | None) -> str:
	if not doc:
		return ""
	label_field = (spec or {}).get("seed_label_field") or "customer_name"
	for fn in (label_field, "customer_name", "group_name", "business_name", "run_name", "incident_title", "title", "name"):
		val = doc.get(fn) if hasattr(doc, "get") else None
		if val:
			return cstr(val)
	return doc.name if doc else ""


def _format_field_value(doc, field) -> str:
	val = doc.get(field.fieldname)
	if val in (None, ""):
		return "—"
	if field.fieldtype == "Check":
		return _("Yes") if val else _("No")
	if field.fieldtype in ("Date",):
		return formatdate(val) if val else "—"
	if field.fieldtype in ("Datetime",):
		return format_datetime(val) if val else "—"
	if field.fieldtype == "Table":
		rows = doc.get(field.fieldname) or []
		return str(len(rows))
	if field.fieldtype == "Link" and field.options:
		try:
			title = frappe.db.get_value(field.options, val, "title") or frappe.db.get_value(
				field.options, val, field.options.lower().replace(" ", "_") + "_name"
			)
			if title:
				return f"{val} ({title})"
		except Exception:
			pass
	return cstr(val)


def _section_rows_from_doc(doc) -> list[dict]:
	meta = doc.meta
	current_section_en = _("Overview")
	current_section_ar = _("نظرة عامة")
	rows: list[dict] = []

	def add_row(*, section_en, section_ar, label_en, label_ar, fieldname, value, row_type="data", indent=0):
		rows.append(
			{
				"section_en": section_en,
				"section_ar": section_ar,
				"label_en": label_en,
				"label_ar": label_ar,
				"fieldname": fieldname or "",
				"value": value or "—",
				"row_type": row_type,
				"indent": indent,
			}
		)

	for field in meta.fields:
		if field.fieldname in SKIP_FIELDNAMES:
			continue
		if field.fieldtype in LAYOUT_FIELDTYPES:
			if field.label:
				current_section_en = field.label
				current_section_ar = field.label
			elif field.fieldtype == "Tab Break" and field.label:
				current_section_en = field.label
				current_section_ar = field.label
			continue
		if field.fieldtype == "Table":
			child_rows = doc.get(field.fieldname) or []
			add_row(
				section_en=current_section_en,
				section_ar=current_section_ar,
				label_en=field.label,
				label_ar=field.label,
				fieldname=field.fieldname,
				value=_("{0} row(s)").format(len(child_rows)),
				row_type="table_header",
			)
			if child_rows:
				child_meta = frappe.get_meta(field.options)
				col_fields = [f for f in child_meta.fields if f.fieldtype not in LAYOUT_FIELDTYPES and not f.hidden]
				for idx, child in enumerate(child_rows, start=1):
					parts = []
					for cf in col_fields[:8]:
						parts.append(f"{cf.label}: {_format_field_value(child, cf)}")
					add_row(
						section_en=current_section_en,
						section_ar=current_section_ar,
						label_en=_("Row {0}").format(idx),
						label_ar=_("صف {0}").format(idx),
						fieldname=f"{field.fieldname}.{idx}",
						value=" | ".join(parts) if parts else cstr(child.as_dict()),
						row_type="table_row",
						indent=1,
					)
			continue
		if field.hidden and not doc.get(field.fieldname):
			continue
		add_row(
			section_en=current_section_en,
			section_ar=current_section_ar,
			label_en=field.label,
			label_ar=field.label,
			fieldname=field.fieldname,
			value=_format_field_value(doc, field),
		)
	return rows


def _workflow_rows(doc) -> list[dict]:
	rows: list[dict] = []
	try:
		tracker = get_progress_tracker(doc.doctype, doc.name)
	except Exception:
		tracker = {}
	for step in tracker.get("progress") or tracker.get("steps") or []:
		status = step.get("status") or "Waiting"
		rows.append(
			{
				"section_en": _("Workflow Journey"),
				"section_ar": _("مسار التمويل"),
				"label_en": step.get("label_en") or step.get("key"),
				"label_ar": step.get("label_ar") or step.get("key"),
				"fieldname": step.get("key") or "",
				"value": status,
				"row_type": "workflow",
				"indent": 0,
			}
		)
	if not rows:
		for step in ENTERPRISE_WORKFLOW_STEPS:
			rows.append(
				{
					"section_en": _("Workflow Journey"),
					"section_ar": _("مسار التمويل"),
					"label_en": step["label_en"],
					"label_ar": step["label_ar"],
					"fieldname": step["key"],
					"value": "—",
					"row_type": "workflow",
					"indent": 0,
				}
			)
	return rows


def _attachment_rows(doctype: str, name: str) -> list[dict]:
	rows: list[dict] = []
	files = frappe.get_all(
		"File",
		filters={"attached_to_doctype": doctype, "attached_to_name": name},
		fields=["file_name", "file_url", "creation", "file_size"],
		order_by="creation desc",
		limit=50,
	)
	for f in files:
		size_kb = round((f.file_size or 0) / 1024, 1)
		rows.append(
			{
				"section_en": _("Attachments"),
				"section_ar": _("المرفقات"),
				"label_en": f.file_name,
				"label_ar": f.file_name,
				"fieldname": "attachment",
				"value": f"{f.file_url} ({size_kb} KB) · {format_datetime(f.creation)}",
				"row_type": "attachment",
				"indent": 0,
			}
		)
	if not rows:
		rows.append(
			{
				"section_en": _("Attachments"),
				"section_ar": _("المرفقات"),
				"label_en": _("No attachments"),
				"label_ar": _("لا توجد مرفقات"),
				"fieldname": "",
				"value": "—",
				"row_type": "attachment",
				"indent": 0,
			}
		)
	return rows


def _timeline_rows(doctype: str, name: str) -> list[dict]:
	rows: list[dict] = []
	for row in frappe.get_all(
		"Version",
		filters={"ref_doctype": doctype, "docname": name},
		fields=["creation", "owner", "data"],
		order_by="creation desc",
		limit=30,
	):
		rows.append(
			{
				"section_en": _("Audit Timeline"),
				"section_ar": _("سجل التغييرات"),
				"label_en": format_datetime(row.creation),
				"label_ar": format_datetime(row.creation),
				"fieldname": "version",
				"value": f"{row.owner}",
				"row_type": "timeline",
				"indent": 0,
			}
		)
	if not rows:
		rows.append(
			{
				"section_en": _("Audit Timeline"),
				"section_ar": _("سجل التغييرات"),
				"label_en": _("No version history"),
				"label_ar": _("لا يوجد سجل"),
				"fieldname": "",
				"value": "—",
				"row_type": "timeline",
				"indent": 0,
			}
		)
	return rows


def build_borrower_dossier(doctype: str, name: str) -> dict:
	"""Structured borrower complete file payload."""
	if doctype not in VERTICAL_BPE_DOCTYPES and not _app_for_doctype(doctype):
		frappe.throw(_("DocType {0} is not a Finance Group case document.").format(doctype))
	if not frappe.db.exists(doctype, name):
		frappe.throw(_("Document {0} {1} not found.").format(doctype, name))

	doc = frappe.get_doc(doctype, name)
	spec = _app_for_doctype(doctype) or {}
	brand = spec.get("brand") or doctype
	borrower = _borrower_title(doc, spec)

	header = {
		"doctype": doctype,
		"name": name,
		"brand": brand,
		"app": spec.get("app") or "",
		"borrower_en": borrower,
		"borrower_ar": borrower,
		"company": doc.get("company") or frappe.defaults.get_user_default("Company") or "",
		"branch": doc.get("branch") or frappe.defaults.get_user_default("Branch") or "",
		"workflow_state": getattr(doc, "workflow_state", None) or doc.get("lifecycle_stage") or doc.get("status") or "—",
		"lifecycle_stage": doc.get("lifecycle_stage") or doc.get("decision_status") or doc.get("status") or "—",
		"generated_at": format_datetime(now_datetime()),
		"owner": doc.owner,
		"modified": format_datetime(doc.modified),
	}

	summary_metrics = []
	for fn, en, ar in (
		("principal", "Principal / Amount", "مبلغ التمويل"),
		("term_months", "Term (Months)", "المدة (شهر)"),
		("risk_score", "Risk Score", "درجة المخاطر"),
		("risk_band", "Risk Band", "نطاق المخاطر"),
		("credit_score", "Credit Score", "النقاط الائتمانية"),
		("approved_limit", "Approved Limit", "الحد المعتمد"),
		("member_count", "Member Count", "عدد الأعضاء"),
	):
		if doc.meta.get_field(fn) and doc.get(fn) not in (None, ""):
			summary_metrics.append({"label_en": en, "label_ar": ar, "value": cstr(doc.get(fn))})

	rows: list[dict] = []
	rows.append(
		{
			"section_en": _("File Header"),
			"section_ar": _("رأس الملف"),
			"label_en": _("Borrower / Case"),
			"label_ar": _("المقترض / الحالة"),
			"fieldname": "borrower",
			"value": borrower,
			"row_type": "header",
			"indent": 0,
		}
	)
	for k, en, ar in (
		("name", "Case ID", "رقم الحالة"),
		("company", "Company", "الشركة"),
		("branch", "Branch", "الفرع"),
		("workflow_state", "Workflow State", "حالة سير العمل"),
		("lifecycle_stage", "Lifecycle Stage", "مرحلة دورة الحياة"),
	):
		val = header.get(k) or doc.get(k) or "—"
		rows.append(
			{
				"section_en": _("File Header"),
				"section_ar": _("رأس الملف"),
				"label_en": en,
				"label_ar": ar,
				"fieldname": k,
				"value": cstr(val),
				"row_type": "header",
				"indent": 0,
			}
		)

	rows.extend(_section_rows_from_doc(doc))
	try:
		from omnexa_core.omnexa_core.finance_demo.finance_borrower_documents import get_dossier_document_rows

		rows.extend(get_dossier_document_rows(doctype, name))
	except Exception:
		pass
	rows.extend(_workflow_rows(doc))
	rows.extend(_attachment_rows(doctype, name))
	rows.extend(_timeline_rows(doctype, name))

	return {
		"header": header,
		"summary_metrics": summary_metrics,
		"rows": rows,
		"report_name": DOSSIER_REPORT_NAME,
	}


def get_dossier_report_columns() -> list[dict]:
	return [
		{"fieldname": "section_en", "label": _("Section (EN)"), "fieldtype": "Data", "width": 160},
		{"fieldname": "section_ar", "label": _("Section (AR)"), "fieldtype": "Data", "width": 140},
		{"fieldname": "label_en", "label": _("Field (EN)"), "fieldtype": "Data", "width": 180},
		{"fieldname": "label_ar", "label": _("Field (AR)"), "fieldtype": "Data", "width": 160},
		{"fieldname": "fieldname", "label": _("Field Name"), "fieldtype": "Data", "width": 120},
		{"fieldname": "value", "label": _("Value"), "fieldtype": "Small Text", "width": 360},
		{"fieldname": "row_type", "label": _("Row Type"), "fieldtype": "Data", "width": 90, "hidden": 1},
		{"fieldname": "indent", "label": _("Indent"), "fieldtype": "Int", "width": 60, "hidden": 1},
	]


def get_dossier_report_data(filters: dict | None = None) -> tuple[list, list, str | None]:
	filters = frappe._dict(filters or {})
	doctype = filters.get("case_doctype")
	name = filters.get("case_name")
	if not doctype or not name:
		return get_dossier_report_columns(), [], _("Select Case DocType and Case to generate the complete borrower file.")
	dossier = build_borrower_dossier(doctype, name)
	header = dossier["header"]
	msg = _("Complete file for {0} — {1} · Generated {2}").format(
		header.get("borrower_en"), header.get("name"), header.get("generated_at")
	)
	return get_dossier_report_columns(), dossier["rows"], msg


def render_dossier_html(doctype: str, name: str) -> str:
	dossier = build_borrower_dossier(doctype, name)
	header = dossier["header"]
	rows = dossier["rows"]
	metrics = dossier.get("summary_metrics") or []

	sections: dict[tuple[str, str], list[dict]] = {}
	for row in rows:
		key = (row.get("section_en") or "", row.get("section_ar") or "")
		sections.setdefault(key, []).append(row)

	metrics_html = ""
	if metrics:
		cells = "".join(
			f'<td class="metric-cell"><div class="metric-value">{frappe.utils.escape_html(m["value"])}</div>'
			f'<div class="metric-label">{frappe.utils.escape_html(m["label_ar"])} / {frappe.utils.escape_html(m["label_en"])}</div></td>'
			for m in metrics
		)
		metrics_html = f'<table class="metrics-table"><tr>{cells}</tr></table>'

	sections_html = ""
	for (sec_en, sec_ar), sec_rows in sections.items():
		body = ""
		for r in sec_rows:
			indent = int(r.get("indent") or 0)
			pad = indent * 16
			body += f"""
			<tr>
				<td style="padding-left:{pad}px">{frappe.utils.escape_html(r.get("label_ar") or "")}<br/>
					<small>{frappe.utils.escape_html(r.get("label_en") or "")}</small></td>
				<td>{frappe.utils.escape_html(cstr(r.get("value") or "—"))}</td>
			</tr>"""
		sections_html += f"""
		<h3>{frappe.utils.escape_html(sec_ar)} / {frappe.utils.escape_html(sec_en)}</h3>
		<table class="dossier-table"><tbody>{body}</tbody></table>"""

	return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="utf-8"/>
<style>
body {{ font-family: "Tajawal", "Cairo", Arial, sans-serif; font-size: 11px; color: #1a2b3c; margin: 0; padding: 0; }}
.header {{ background: #003366; color: #fff; padding: 18px 20px; border-radius: 8px; margin-bottom: 16px; }}
.header h1 {{ margin: 0 0 6px; font-size: 20px; }}
.header .meta {{ opacity: 0.9; font-size: 10px; }}
.metrics-table {{ width: 100%; margin: 12px 0 18px; border-collapse: collapse; }}
.metric-cell {{ background: #e6f0f9; border: 1px solid #c5d9ef; padding: 10px; text-align: center; width: 25%; }}
.metric-value {{ font-size: 16px; font-weight: 700; color: #003366; }}
.metric-label {{ font-size: 9px; color: #5c6b7a; margin-top: 4px; }}
h3 {{ color: #003366; border-bottom: 2px solid #e6f0f9; padding-bottom: 6px; margin-top: 18px; }}
.dossier-table {{ width: 100%; border-collapse: collapse; margin-bottom: 8px; }}
.dossier-table td {{ border: 1px solid #d9e1ec; padding: 8px 10px; vertical-align: top; }}
.dossier-table tr:nth-child(even) td {{ background: #fbfdff; }}
.dossier-table td:first-child {{ width: 38%; font-weight: 600; background: #f8fafc; }}
.footer {{ margin-top: 20px; font-size: 9px; color: #5c6b7a; text-align: center; }}
</style>
</head>
<body>
<div class="header">
	<h1>ملف المقترض الشامل · Finance Borrower Complete File</h1>
	<div>{frappe.utils.escape_html(header.get("brand") or "")} — {frappe.utils.escape_html(header.get("borrower_ar") or "")}</div>
	<div class="meta">Case: {frappe.utils.escape_html(header.get("name") or "")} · {frappe.utils.escape_html(header.get("doctype") or "")}</div>
	<div class="meta">Company: {frappe.utils.escape_html(cstr(header.get("company") or "—"))} · Branch: {frappe.utils.escape_html(cstr(header.get("branch") or "—"))}</div>
	<div class="meta">Generated: {frappe.utils.escape_html(header.get("generated_at") or "")}</div>
</div>
{metrics_html}
{sections_html}
<div class="footer">ErpGenEx Finance Group · Confidential Borrower File</div>
</body>
</html>"""


@frappe.whitelist()
def get_borrower_dossier(doctype: str, name: str) -> dict:
	return build_borrower_dossier(doctype, name)


@frappe.whitelist()
def get_borrower_dossier_html(doctype: str, name: str) -> str:
	"""HTML payload for browser print preview."""
	return render_dossier_html(doctype, name)


@frappe.whitelist()
def open_borrower_dossier_report(doctype: str, name: str) -> dict:
	return {
		"route": f"/app/query-report/{DOSSIER_REPORT_NAME}",
		"filters": {"case_doctype": doctype, "case_name": name},
	}


@frappe.whitelist()
def download_borrower_dossier_pdf(doctype: str, name: str):
	from frappe.utils.pdf import get_pdf

	html = render_dossier_html(doctype, name)
	pdf = get_pdf(html)
	frappe.local.response.filename = f"Borrower_File_{frappe.scrub(name)}.pdf"
	frappe.local.response.filecontent = pdf
	frappe.local.response.type = "download"


@frappe.whitelist()
def download_borrower_dossier_excel(doctype: str, name: str):
	from frappe.utils.xlsxutils import make_xlsx

	_, rows, _ = get_dossier_report_data({"case_doctype": doctype, "case_name": name})
	columns = get_dossier_report_columns()
	header_row = [c["label"] for c in columns if not c.get("hidden")]
	fieldnames = [c["fieldname"] for c in columns if not c.get("hidden")]
	data = [header_row]
	for row in rows:
		data.append([row.get(fn, "") for fn in fieldnames])
	xlsx = make_xlsx(data, "Borrower_Complete_File")
	frappe.local.response.filename = f"Borrower_File_{frappe.scrub(name)}.xlsx"
	frappe.local.response.filecontent = xlsx.getvalue()
	frappe.local.response.type = "download"


def ensure_finance_borrower_dossier_report() -> dict:
	"""Idempotent — ensure Script Report exists (for sites without migrate sync)."""
	if frappe.db.exists("Report", DOSSIER_REPORT_NAME):
		return {"ok": True, "report": DOSSIER_REPORT_NAME, "created": False}
	report_path = frappe.get_app_path(
		"omnexa_core", "omnexa_core", "report", "finance_borrower_complete_file", "finance_borrower_complete_file.json"
	)
	with open(report_path, encoding="utf-8") as f:
		doc = json.loads(f.read())
	doc["doctype"] = "Report"
	frappe.get_doc(doc).insert(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": True, "report": DOSSIER_REPORT_NAME, "created": True}
