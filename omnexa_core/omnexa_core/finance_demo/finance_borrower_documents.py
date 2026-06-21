# Copyright (c) 2026, ErpGenEx
"""Borrower document upload, metadata, e/paper approval, and print across Finance Group."""

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.utils import cstr, format_datetime, get_url, now_datetime

from omnexa_core.omnexa_core.finance_demo.finance_vertical_specs import VERTICAL_BPE_SPECS

CASE_DOC_DT = "Finance Borrower Case Document"
TYPE_DT = "Finance Borrower Document Type"
SETTINGS_DT = "Finance Borrower Document Settings"

DEFAULT_DOCUMENT_TYPES = [
	{
		"document_code": "NATIONAL_ID",
		"document_name_en": "National ID",
		"document_name_ar": "الهوية الوطنية",
		"capture_national_id": 1,
		"capture_expiry_date": 1,
		"sort_order": 10,
	},
	{
		"document_code": "COMMERCIAL_REGISTRATION",
		"document_name_en": "Commercial Registration",
		"document_name_ar": "السجل التجاري",
		"capture_commercial_registration": 1,
		"capture_issue_date": 1,
		"capture_expiry_date": 1,
		"sort_order": 20,
	},
	{
		"document_code": "TAX_CARD",
		"document_name_en": "Tax Card",
		"document_name_ar": "البطاقة الضريبية",
		"capture_tax_card": 1,
		"capture_issue_date": 1,
		"sort_order": 30,
	},
	{
		"document_code": "BANK_STATEMENT",
		"document_name_en": "Bank Statement",
		"document_name_ar": "كشف حساب بنكي",
		"capture_bank_account": 1,
		"capture_iban": 1,
		"sort_order": 40,
	},
	{
		"document_code": "INCOME_CERTIFICATE",
		"document_name_en": "Income Certificate",
		"document_name_ar": "شهادة الدخل",
		"sort_order": 50,
	},
	{
		"document_code": "FIELD_VISIT_PHOTOS",
		"document_name_en": "Field Visit Photos",
		"document_name_ar": "صور الزيارة الميدانية",
		"sort_order": 60,
	},
	{
		"document_code": "PROMISSORY_NOTE",
		"document_name_en": "Promissory Note",
		"document_name_ar": "سند لأمر",
		"sort_order": 70,
	},
]

DEFAULT_MANDATORY_BY_APP: dict[str, list[str]] = {
	"omnexa_sme_microfinance": ["NATIONAL_ID", "COMMERCIAL_REGISTRATION", "BANK_STATEMENT", "INCOME_CERTIFICATE"],
	"omnexa_consumer_finance": ["NATIONAL_ID", "INCOME_CERTIFICATE", "BANK_STATEMENT"],
	"omnexa_sme_retail_finance": ["NATIONAL_ID", "COMMERCIAL_REGISTRATION", "TAX_CARD", "BANK_STATEMENT"],
	"omnexa_vehicle_finance": ["NATIONAL_ID", "BANK_STATEMENT"],
	"omnexa_mortgage_finance": ["NATIONAL_ID", "COMMERCIAL_REGISTRATION", "TAX_CARD", "BANK_STATEMENT"],
	"omnexa_factoring": ["COMMERCIAL_REGISTRATION", "TAX_CARD", "BANK_STATEMENT"],
	"omnexa_leasing_finance": ["NATIONAL_ID", "COMMERCIAL_REGISTRATION", "BANK_STATEMENT"],
	"omnexa_finance_engine": ["NATIONAL_ID", "BANK_STATEMENT"],
	"omnexa_credit_engine": ["NATIONAL_ID", "INCOME_CERTIFICATE"],
}


def _app_for_case(case_doctype: str) -> str | None:
	for app, spec in VERTICAL_BPE_SPECS.items():
		if spec.get("case_doctype") == case_doctype:
			return app
	return None


def _type_row(doc_type_name: str) -> dict:
	dt = frappe.get_doc(TYPE_DT, doc_type_name)
	return {
		"document_type": dt.name,
		"document_code": dt.document_code,
		"label_en": dt.document_name_en,
		"label_ar": dt.document_name_ar,
		"capture_national_id": bool(dt.capture_national_id),
		"capture_commercial_registration": bool(dt.capture_commercial_registration),
		"capture_tax_card": bool(dt.capture_tax_card),
		"capture_bank_account": bool(dt.capture_bank_account),
		"capture_iban": bool(dt.capture_iban),
		"capture_issue_date": bool(dt.capture_issue_date),
		"capture_expiry_date": bool(dt.capture_expiry_date),
	}


def get_document_policies(finance_app: str) -> list[dict]:
	if not frappe.db.exists("DocType", SETTINGS_DT):
		return []
	settings = frappe.get_single(SETTINGS_DT)
	rows = []
	for line in settings.get("document_policies") or []:
		if line.finance_app != finance_app or not line.is_active:
			continue
		if not frappe.db.exists(TYPE_DT, line.document_type):
			continue
		type_meta = _type_row(line.document_type)
		rows.append(
			{
				**type_meta,
				"is_mandatory": bool(line.is_mandatory),
				"sort_order": line.sort_order or type_meta.get("sort_order") or 0,
			}
		)
	rows.sort(key=lambda r: (r.get("sort_order") or 0, r.get("document_code") or ""))
	return rows


def ensure_case_document_slots(case_doctype: str, case_name: str, finance_app: str | None = None) -> list[str]:
	"""Create pending document rows from policy if missing."""
	finance_app = finance_app or _app_for_case(case_doctype)
	if not finance_app:
		return []
	created: list[str] = []
	for policy in get_document_policies(finance_app):
		exists = frappe.db.exists(
			CASE_DOC_DT,
			{"case_doctype": case_doctype, "case_name": case_name, "document_type": policy["document_type"]},
		)
		if exists:
			continue
		doc = frappe.get_doc(
			{
				"doctype": CASE_DOC_DT,
				"case_doctype": case_doctype,
				"case_name": case_name,
				"finance_app": finance_app,
				"document_type": policy["document_type"],
				"is_mandatory": policy.get("is_mandatory"),
				"verification_status": "Pending Upload",
			}
		)
		doc.insert(ignore_permissions=True)
		created.append(doc.name)
	if created:
		frappe.db.commit()
	return created


def _serialize_case_document(row: dict) -> dict:
	doc_type = row.get("document_type")
	type_meta = _type_row(doc_type) if doc_type and frappe.db.exists(TYPE_DT, doc_type) else {}
	return {
		"name": row.get("name"),
		"document_type": doc_type,
		"document_code": type_meta.get("document_code"),
		"label_en": type_meta.get("label_en") or doc_type,
		"label_ar": type_meta.get("label_ar") or doc_type,
		"is_mandatory": bool(row.get("is_mandatory")),
		"verification_status": row.get("verification_status") or "Pending Upload",
		"attachment": row.get("attachment"),
		"attachment_url": get_url(row.get("attachment")) if row.get("attachment") else "",
		"national_id": row.get("national_id") or "",
		"commercial_registration": row.get("commercial_registration") or "",
		"tax_card_number": row.get("tax_card_number") or "",
		"bank_account": row.get("bank_account") or "",
		"iban": row.get("iban") or "",
		"issue_date": row.get("issue_date"),
		"expiry_date": row.get("expiry_date"),
		"electronic_approved_by": row.get("electronic_approved_by"),
		"electronic_approved_on": row.get("electronic_approved_on"),
		"paper_approved_by": row.get("paper_approved_by"),
		"paper_approved_on": row.get("paper_approved_on"),
		"rejection_reason": row.get("rejection_reason") or "",
		"notes": row.get("notes") or "",
		"uploaded_by": row.get("uploaded_by"),
		"uploaded_on": row.get("uploaded_on"),
		"capture": type_meta,
	}


@frappe.whitelist()
def get_case_documents(case_doctype: str, case_name: str, finance_app: str | None = None) -> dict:
	if not case_doctype or not case_name:
		frappe.throw(_("Case DocType and Case are required."))
	finance_app = finance_app or _app_for_case(case_doctype)
	if case_name != "new" and frappe.db.exists(case_doctype, case_name):
		ensure_case_document_slots(case_doctype, case_name, finance_app)
	rows = frappe.get_all(
		CASE_DOC_DT,
		filters={"case_doctype": case_doctype, "case_name": case_name},
		fields=[
			"name",
			"document_type",
			"is_mandatory",
			"verification_status",
			"attachment",
			"national_id",
			"commercial_registration",
			"tax_card_number",
			"bank_account",
			"iban",
			"issue_date",
			"expiry_date",
			"electronic_approved_by",
			"electronic_approved_on",
			"paper_approved_by",
			"paper_approved_on",
			"rejection_reason",
			"notes",
			"uploaded_by",
			"uploaded_on",
		],
		order_by="modified asc",
	)
	docs = [_serialize_case_document(r) for r in rows]
	mandatory_total = sum(1 for d in docs if d.get("is_mandatory"))
	mandatory_uploaded = sum(
		1
		for d in docs
		if d.get("is_mandatory") and d.get("attachment") and d.get("verification_status") not in ("Pending Upload", "Rejected")
	)
	approved = sum(1 for d in docs if d.get("verification_status") in ("E-Approved", "Paper Approved"))
	return {
		"case_doctype": case_doctype,
		"case_name": case_name,
		"finance_app": finance_app,
		"documents": docs,
		"summary": {
			"total": len(docs),
			"mandatory_total": mandatory_total,
			"mandatory_uploaded": mandatory_uploaded,
			"approved": approved,
			"complete": mandatory_total > 0 and mandatory_uploaded >= mandatory_total,
		},
	}


@frappe.whitelist()
def save_case_document(data: str | dict) -> dict:
	payload = json.loads(data) if isinstance(data, str) else dict(data or {})
	name = payload.get("name")
	if name and frappe.db.exists(CASE_DOC_DT, name):
		doc = frappe.get_doc(CASE_DOC_DT, name)
	else:
		doc = frappe.new_doc(CASE_DOC_DT)
	for fn in (
		"case_doctype",
		"case_name",
		"finance_app",
		"document_type",
		"is_mandatory",
		"attachment",
		"national_id",
		"commercial_registration",
		"tax_card_number",
		"bank_account",
		"iban",
		"issue_date",
		"expiry_date",
		"notes",
	):
		if fn in payload and payload[fn] not in (None, ""):
			doc.set(fn, payload[fn])
	if payload.get("attachment"):
		doc.verification_status = "Pending Review"
		doc.uploaded_by = frappe.session.user
		doc.uploaded_on = now_datetime()
	elif doc.verification_status == "Pending Upload" and not doc.attachment:
		pass
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return _serialize_case_document(doc.as_dict())


@frappe.whitelist()
def approve_document_electronic(name: str) -> dict:
	doc = frappe.get_doc(CASE_DOC_DT, name)
	if not doc.attachment:
		frappe.throw(_("Upload the document before electronic approval."))
	doc.verification_status = "E-Approved"
	doc.electronic_approved_by = frappe.session.user
	doc.electronic_approved_on = now_datetime()
	doc.rejection_reason = ""
	try:
		from omnexa_core.omnexa_core.finance_demo.finance_wave6_global_leader import record_esign_vault_entry

		record_esign_vault_entry(
			case_doctype=doc.case_doctype,
			case_name=doc.case_name,
			document_name=doc.name,
			document_type=doc.document_type,
			attachment=doc.attachment,
			action="E-Approved",
		)
	except Exception:
		pass
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return _serialize_case_document(doc.as_dict())


@frappe.whitelist()
def approve_document_paper(name: str) -> dict:
	doc = frappe.get_doc(CASE_DOC_DT, name)
	if not doc.attachment:
		frappe.throw(_("Upload the document before paper approval."))
	doc.verification_status = "Paper Approved"
	doc.paper_approved_by = frappe.session.user
	doc.paper_approved_on = now_datetime()
	doc.rejection_reason = ""
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return _serialize_case_document(doc.as_dict())


@frappe.whitelist()
def reject_case_document(name: str, reason: str | None = None) -> dict:
	doc = frappe.get_doc(CASE_DOC_DT, name)
	doc.verification_status = "Rejected"
	doc.rejection_reason = reason or _("Rejected")
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return _serialize_case_document(doc.as_dict())


def render_document_print_html(doc_name: str) -> str:
	doc = frappe.get_doc(CASE_DOC_DT, doc_name)
	type_meta = _type_row(doc.document_type)
	meta_rows = []
	for label_en, label_ar, val in (
		("National ID", "الرقم القومي", doc.national_id),
		("Commercial Registration", "السجل التجاري", doc.commercial_registration),
		("Tax Card", "البطاقة الضريبية", doc.tax_card_number),
		("Bank Account", "حساب بنكي", doc.bank_account),
		("IBAN", "IBAN", doc.iban),
		("Issue Date", "تاريخ الإصدار", doc.issue_date),
		("Expiry Date", "تاريخ الانتهاء", doc.expiry_date),
	):
		if val:
			meta_rows.append(
				f"<tr><td>{frappe.utils.escape_html(label_ar)} / {frappe.utils.escape_html(label_en)}</td>"
				f"<td>{frappe.utils.escape_html(cstr(val))}</td></tr>"
			)
	status_ar = {
		"Pending Upload": "بانتظار الرفع",
		"Uploaded": "مرفوع",
		"Pending Review": "بانتظار المراجعة",
		"E-Approved": "معتمد إلكترونياً",
		"Paper Approved": "معتمد ورقياً",
		"Rejected": "مرفوض",
	}.get(doc.verification_status, doc.verification_status)
	return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar"><head><meta charset="utf-8"/>
<style>
body {{ font-family: Tajawal, Arial, sans-serif; font-size: 11px; color: #1a2b3c; }}
.header {{ background:#003366; color:#fff; padding:16px; border-radius:8px; margin-bottom:12px; }}
table {{ width:100%; border-collapse:collapse; margin:10px 0; }}
td {{ border:1px solid #d9e1ec; padding:8px; }}
td:first-child {{ width:38%; background:#f8fafc; font-weight:600; }}
.status {{ display:inline-block; padding:4px 10px; border-radius:12px; background:#e6f0f9; }}
</style></head><body>
<div class="header">
<h2>{frappe.utils.escape_html(type_meta.get('label_ar') or doc.document_type)}</h2>
<p>{frappe.utils.escape_html(type_meta.get('label_en') or '')} · Case {frappe.utils.escape_html(doc.case_name)}</p>
<p class="status">{frappe.utils.escape_html(status_ar)} / {frappe.utils.escape_html(doc.verification_status)}</p>
</div>
<table><tbody>
<tr><td>الحالة / Case</td><td>{frappe.utils.escape_html(doc.case_name)} ({frappe.utils.escape_html(doc.case_doctype)})</td></tr>
{''.join(meta_rows)}
<tr><td>رفع / Uploaded</td><td>{frappe.utils.escape_html(doc.uploaded_by or '—')} · {frappe.utils.escape_html(format_datetime(doc.uploaded_on) if doc.uploaded_on else '—')}</td></tr>
<tr><td>اعتماد إلكتروني</td><td>{frappe.utils.escape_html(doc.electronic_approved_by or '—')} · {frappe.utils.escape_html(format_datetime(doc.electronic_approved_on) if doc.electronic_approved_on else '—')}</td></tr>
<tr><td>اعتماد ورقي</td><td>{frappe.utils.escape_html(doc.paper_approved_by or '—')} · {frappe.utils.escape_html(format_datetime(doc.paper_approved_on) if doc.paper_approved_on else '—')}</td></tr>
</tbody></table>
<p><strong>ملاحظات:</strong> {frappe.utils.escape_html(doc.notes or '—')}</p>
<p style="font-size:9px;color:#5c6b7a;text-align:center;">ErpGenEx Finance Group · Borrower Document Print</p>
</body></html>"""


@frappe.whitelist()
def get_document_print_html(name: str) -> str:
	"""HTML for browser print preview."""
	return render_document_print_html(name)


@frappe.whitelist()
def print_case_document(name: str):
	from frappe.utils.pdf import get_pdf

	html = render_document_print_html(name)
	pdf = get_pdf(html)
	doc = frappe.get_doc(CASE_DOC_DT, name)
	frappe.local.response.filename = f"Document_{frappe.scrub(doc.document_type)}_{frappe.scrub(doc.case_name)}.pdf"
	frappe.local.response.filecontent = pdf
	frappe.local.response.type = "download"


def get_dossier_document_rows(case_doctype: str, case_name: str) -> list[dict]:
	if not frappe.db.exists("DocType", CASE_DOC_DT):
		return []
	try:
		payload = get_case_documents(case_doctype, case_name)
	except Exception:
		return []
	rows = []
	for d in payload.get("documents") or []:
		meta_bits = []
		for key, ar, en in (
			("national_id", "الرقم القومي", "National ID"),
			("commercial_registration", "السجل التجاري", "CR"),
			("tax_card_number", "البطاقة الضريبية", "Tax Card"),
			("bank_account", "حساب بنكي", "Bank"),
			("iban", "IBAN", "IBAN"),
		):
			if d.get(key):
				meta_bits.append(f"{ar}: {d[key]}")
		rows.append(
			{
				"section_en": "Borrower Documents",
				"section_ar": "مستندات المقترض",
				"label_en": d.get("label_en"),
				"label_ar": d.get("label_ar"),
				"fieldname": d.get("document_code") or d.get("document_type"),
				"value": f"{d.get('verification_status')} · {' | '.join(meta_bits) if meta_bits else ('Uploaded' if d.get('attachment') else 'Missing')}",
				"row_type": "document",
				"indent": 0,
				"document_name": d.get("name"),
				"attachment": d.get("attachment"),
			}
		)
	return rows


def bootstrap_finance_borrower_documents() -> dict:
	"""Seed document types and per-app policy (idempotent)."""
	if not frappe.db.exists("DocType", TYPE_DT):
		return {"ok": False, "reason": "DocTypes not migrated yet"}

	types_created = 0
	for spec in DEFAULT_DOCUMENT_TYPES:
		if frappe.db.exists(TYPE_DT, spec["document_code"]):
			doc = frappe.get_doc(TYPE_DT, spec["document_code"])
			for k, v in spec.items():
				if doc.get(k) != v:
					doc.set(k, v)
			doc.is_active = 1
			doc.save(ignore_permissions=True)
		else:
			doc = frappe.get_doc({"doctype": TYPE_DT, **spec, "is_active": 1})
			doc.insert(ignore_permissions=True)
			types_created += 1

	settings = frappe.get_single(SETTINGS_DT)
	existing = {(r.finance_app, r.document_type) for r in (settings.document_policies or [])}
	policies_added = 0
	for app, codes in DEFAULT_MANDATORY_BY_APP.items():
		for idx, code in enumerate(codes):
			if not frappe.db.exists(TYPE_DT, code):
				continue
			key = (app, code)
			if key in existing:
				continue
			settings.append(
				"document_policies",
				{
					"finance_app": app,
					"document_type": code,
					"is_mandatory": 1,
					"is_active": 1,
					"sort_order": (idx + 1) * 10,
				},
			)
			policies_added += 1
	# Optional docs for all lending apps
	for app in DEFAULT_MANDATORY_BY_APP:
		for code, mandatory in (("FIELD_VISIT_PHOTOS", 0), ("PROMISSORY_NOTE", 0)):
			if not frappe.db.exists(TYPE_DT, code):
				continue
			key = (app, code)
			if key in existing:
				continue
			settings.append(
				"document_policies",
				{"finance_app": app, "document_type": code, "is_mandatory": mandatory, "is_active": 1, "sort_order": 90},
			)
			policies_added += 1
			existing.add(key)

	settings.save(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": True, "types_created": types_created, "policies_added": policies_added}
