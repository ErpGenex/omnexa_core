from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe
from frappe.utils import now_datetime

from omnexa_core.omnexa_core.event_rules import resolve_rule

EVENT_PROVIDER = "erpgenex_core"


def on_submit_emit(doc, method=None):
	_emit_document_event(doc, "submitted")


def on_cancel_emit(doc, method=None):
	_emit_document_event(doc, "cancelled")


def _event_name(doctype: str, action: str) -> str:
	compact = "".join((doctype or "").split())
	return f"{compact}.{action.capitalize()}"


def _event_id(doctype: str, docname: str, action: str) -> str:
	base = f"{doctype}:{docname}:{action}"
	return hashlib.sha256(base.encode()).hexdigest()


def _payload_hash(payload: dict[str, Any]) -> str:
	raw = json.dumps(payload, sort_keys=True, default=str)
	return hashlib.sha256(raw.encode()).hexdigest()


def _build_payload(doc, action: str) -> dict[str, Any]:
	return {
		"event_name": _event_name(doc.doctype, action),
		"action": action,
		"doctype": doc.doctype,
		"docname": doc.name,
		"company": getattr(doc, "company", None),
		"branch": getattr(doc, "branch", None),
		"posting_date": str(getattr(doc, "posting_date", "") or ""),
		"posting_time": str(getattr(doc, "posting_time", "") or ""),
		"owner": str(getattr(doc, "owner", "") or ""),
		"modified_by": str(getattr(doc, "modified_by", "") or ""),
		"docstatus": int(getattr(doc, "docstatus", 0) or 0),
	}


def _emit_document_event(doc, action: str) -> None:
	"""
	Overlay event emitter (non-breaking):
	- Never blocks live transaction flow.
	- Stores append-only event records in Webhook Event Log.
	- Dispatches optional subscribers via omnexa_core_event_handlers hooks.
	"""
	try:
		payload = _build_payload(doc, action)
		event_id = _event_id(doc.doctype, doc.name, action)
		event_name = payload["event_name"]
		rule = resolve_rule(event_name=event_name, payload=payload)
		payload["rule"] = {
			"enabled": bool(rule.get("enabled", 1)),
			"ledger_domain": str(rule.get("ledger_domain") or "General"),
		}

		if not payload["rule"]["enabled"]:
			return

		exists = frappe.db.get_value(
			"Webhook Event Log",
			{"provider": EVENT_PROVIDER, "event_id": event_id},
			"name",
		)
		if exists:
			return

		log = frappe.new_doc("Webhook Event Log")
		log.provider = EVENT_PROVIDER
		log.event_id = event_id
		log.payload_hash = _payload_hash(payload)
		log.event_reference = f"{doc.doctype}:{doc.name}"
		log.processing_status = "Received"
		log.http_status_code = 202
		log.insert(ignore_permissions=True)
		dispatched_async = _dispatch_handlers(
			event_name=event_name,
			payload=payload,
			doc=doc,
			log_name=log.name,
		)
		if dispatched_async:
			return

		errors = _run_handlers(event_name=event_name, payload=payload, doc=doc)
		if errors:
			_mark_log_error(log.name, "; ".join(errors)[:2000])
		else:
			frappe.db.set_value(
				"Webhook Event Log",
				log.name,
				{
					"processing_status": "Processed",
					"http_status_code": 200,
					"error_message": "",
				},
				update_modified=False,
			)
	except Exception:
		# Hard stop avoided by design: eventing overlay should never break transaction commit.
		frappe.log_error(
			title="Omnexa event emit failed",
			message=f"DocType: {getattr(doc, 'doctype', '')}\nName: {getattr(doc, 'name', '')}\n{frappe.get_traceback()}",
		)


def process_event_handlers_async(
	event_name: str,
	payload: dict[str, Any],
	doctype: str,
	docname: str,
	log_name: str,
	attempt: int = 1,
) -> None:
	"""
	Async event projection processor with bounded retries.
	Enabled only when omnexa_event_async_enabled = 1.
	"""
	doc = frappe.get_doc(doctype, docname)
	errors = _run_handlers(event_name=event_name, payload=payload, doc=doc)
	if not errors:
		frappe.db.set_value(
			"Webhook Event Log",
			log_name,
			{
				"processing_status": "Processed",
				"http_status_code": 200,
				"error_message": "",
			},
			update_modified=False,
		)
		return

	max_attempts = _max_handler_attempts()
	if attempt < max_attempts:
		frappe.enqueue(
			"omnexa_core.omnexa_core.event_dispatcher.process_event_handlers_async",
			queue="short",
			event_name=event_name,
			payload=payload,
			doctype=doctype,
			docname=docname,
			log_name=log_name,
			attempt=attempt + 1,
		)
		frappe.db.set_value(
			"Webhook Event Log",
			log_name,
			{
				"processing_status": "Received",
				"http_status_code": 202,
				"error_message": f"retry_scheduled_attempt_{attempt + 1}: {'; '.join(errors)[:1500]}",
			},
			update_modified=False,
		)
		return

	_insert_dead_letter(
		event_name=event_name,
		payload=payload,
		doctype=doctype,
		docname=docname,
		log_name=log_name,
		attempt=attempt,
		errors=errors,
	)
	_mark_log_error(log_name, "; ".join(errors)[:2000])


def _dispatch_handlers(event_name: str, payload: dict[str, Any], doc, log_name: str) -> bool:
	if not _is_async_enabled():
		return False
	try:
		frappe.enqueue(
			"omnexa_core.omnexa_core.event_dispatcher.process_event_handlers_async",
			queue="short",
			event_name=event_name,
			payload=payload,
			doctype=doc.doctype,
			docname=doc.name,
			log_name=log_name,
			attempt=1,
		)
		return True
	except Exception:
		frappe.log_error(
			title="Omnexa async dispatch failed",
			message=f"Event: {event_name}\n{frappe.get_traceback()}",
		)
		return False


def _run_handlers(event_name: str, payload: dict[str, Any], doc) -> list[str]:
	errors: list[str] = []
	for path in frappe.get_hooks("omnexa_core_event_handlers") or []:
		try:
			frappe.get_attr(path)(event_name=event_name, payload=payload, doc=doc)
		except Exception:
			errors.append(f"handler_failed: {path}")
			frappe.log_error(
				title="Omnexa event handler failed",
				message=f"Event: {event_name}\nHandler: {path}\n{frappe.get_traceback()}",
			)
	return errors


def _is_async_enabled() -> bool:
	return frappe.conf.get("omnexa_event_async_enabled") in (1, True, "1", "true", "True")


def _max_handler_attempts() -> int:
	raw = frappe.conf.get("omnexa_event_handler_max_attempts")
	try:
		val = int(raw)
	except Exception:
		val = 3
	return max(1, min(10, val))


def _mark_log_error(log_name: str, message: str) -> None:
	frappe.db.set_value(
		"Webhook Event Log",
		log_name,
		{
			"processing_status": "Error",
			"http_status_code": 500,
			"error_message": (message or "")[:2000],
		},
		update_modified=False,
	)


def _insert_dead_letter(
	event_name: str,
	payload: dict[str, Any],
	doctype: str,
	docname: str,
	log_name: str,
	attempt: int,
	errors: list[str],
) -> None:
	try:
		doc = frappe.new_doc("Event Dead Letter")
		doc.event_name = event_name
		doc.source_doctype = doctype
		doc.source_docname = docname
		doc.webhook_event_log = log_name
		doc.retry_attempt = int(attempt or 0)
		doc.error_message = "; ".join(errors)[:2000]
		doc.event_payload = json.dumps(payload or {}, sort_keys=True, default=str)
		doc.occurred_at = now_datetime()
		doc.insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(
			title="Omnexa dead letter insert failed",
			message=f"Event: {event_name}\nDoc: {doctype}:{docname}\n{frappe.get_traceback()}",
		)


@frappe.whitelist()
def get_event_pipeline_health(hours: int = 24) -> dict[str, Any]:
	"""
	Operational snapshot for event overlay health.
	Can be used by workspace cards/reports.
	"""
	try:
		h = max(1, min(720, int(hours or 24)))
	except Exception:
		h = 24

	where = "creation >= DATE_SUB(NOW(), INTERVAL %s HOUR)"
	vals = (h,)
	webhook_rows = frappe.db.sql(
		f"""
		SELECT processing_status, COUNT(*) AS c
		FROM `tabWebhook Event Log`
		WHERE provider = %s AND {where}
		GROUP BY processing_status
		""",
		(EVENT_PROVIDER, *vals),
		as_dict=True,
	)
	dlq_count = frappe.db.sql(
		f"SELECT COUNT(*) AS c FROM `tabEvent Dead Letter` WHERE {where}",
		vals,
		as_dict=True,
	)[0]["c"]
	status_counts = {r["processing_status"]: int(r["c"]) for r in (webhook_rows or [])}
	return {
		"window_hours": h,
		"provider": EVENT_PROVIDER,
		"status_counts": status_counts,
		"dead_letter_count": int(dlq_count or 0),
	}


@frappe.whitelist()
def list_dead_letters(limit: int = 50) -> list[dict[str, Any]]:
	try:
		lim = max(1, min(500, int(limit or 50)))
	except Exception:
		lim = 50
	return frappe.get_all(
		"Event Dead Letter",
		fields=[
			"name",
			"event_name",
			"source_doctype",
			"source_docname",
			"webhook_event_log",
			"retry_attempt",
			"occurred_at",
			"error_message",
			"creation",
		],
		order_by="creation desc",
		limit_page_length=lim,
	)


@frappe.whitelist()
def reprocess_dead_letter(name: str, delete_on_success: int = 0) -> dict[str, Any]:
	if not name:
		frappe.throw("Dead letter name is required.")
	dl = frappe.get_doc("Event Dead Letter", name)

	payload = {}
	try:
		payload = json.loads(dl.event_payload or "{}")
	except Exception:
		payload = {}

	event_name = str(dl.event_name or "")
	doctype = str(dl.source_doctype or "")
	docname = str(dl.source_docname or "")
	log_name = str(dl.webhook_event_log or "")

	if not all([event_name, doctype, docname, log_name]):
		frappe.throw("Dead letter is missing required fields for reprocessing.")

	doc = frappe.get_doc(doctype, docname)
	errors = _run_handlers(event_name=event_name, payload=payload, doc=doc)
	if errors:
		_mark_log_error(log_name, "; ".join(errors)[:2000])
		return {
			"ok": False,
			"name": name,
			"event_name": event_name,
			"errors": errors,
		}

	frappe.db.set_value(
		"Webhook Event Log",
		log_name,
		{
			"processing_status": "Processed",
			"http_status_code": 200,
			"error_message": "",
		},
		update_modified=False,
	)

	if int(delete_on_success or 0):
		frappe.delete_doc("Event Dead Letter", name, force=1, ignore_permissions=True)
		return {"ok": True, "name": name, "event_name": event_name, "deleted": True}
	return {"ok": True, "name": name, "event_name": event_name, "deleted": False}


@frappe.whitelist()
def reprocess_dead_letters_batch(limit: int = 20, delete_on_success: int = 0) -> dict[str, Any]:
	try:
		lim = max(1, min(200, int(limit or 20)))
	except Exception:
		lim = 20
	rows = frappe.get_all(
		"Event Dead Letter",
		fields=["name"],
		order_by="creation asc",
		limit_page_length=lim,
	)
	results = []
	ok = 0
	failed = 0
	for row in rows:
		try:
			res = reprocess_dead_letter(row["name"], delete_on_success=delete_on_success)
			results.append(res)
			if res.get("ok"):
				ok += 1
			else:
				failed += 1
		except Exception:
			failed += 1
			results.append(
				{
					"ok": False,
					"name": row.get("name"),
					"errors": [frappe.get_traceback()[-1000:]],
				}
			)
	return {
		"processed": len(rows),
		"ok": ok,
		"failed": failed,
		"results": results,
	}


@frappe.whitelist()
def reprocess_dead_letter_names(names_json: str, delete_on_success: int = 0) -> dict[str, Any]:
	names = []
	try:
		parsed = json.loads(names_json or "[]")
		if isinstance(parsed, list):
			names = [str(x).strip() for x in parsed if str(x).strip()]
	except Exception:
		names = []
	if not names:
		frappe.throw("No dead letter names provided.")

	results = []
	ok = 0
	failed = 0
	for name in names[:200]:
		try:
			res = reprocess_dead_letter(name=name, delete_on_success=delete_on_success)
			results.append(res)
			if res.get("ok"):
				ok += 1
			else:
				failed += 1
		except Exception:
			failed += 1
			results.append(
				{
					"ok": False,
					"name": name,
					"errors": [frappe.get_traceback()[-1000:]],
				}
			)
	return {"selected": len(names[:200]), "ok": ok, "failed": failed, "results": results}


def monitor_event_pipeline() -> None:
	"""
	Hourly guardrail:
	- Logs error when dead-letter count exceeds configured threshold.
	site_config:
	  omnexa_event_dlq_alert_threshold (default 10)
	"""
	try:
		raw = frappe.conf.get("omnexa_event_dlq_alert_threshold")
		threshold = int(raw) if raw is not None else 10
		threshold = max(1, min(10000, threshold))
	except Exception:
		threshold = 10

	health = get_event_pipeline_health(hours=24)
	dlq_count = int(health.get("dead_letter_count") or 0)
	if dlq_count < threshold:
		return

	frappe.log_error(
		title="Omnexa Event Pipeline Alert",
		message=(
			f"DLQ threshold exceeded.\n"
			f"Threshold: {threshold}\n"
			f"Current DLQ (24h): {dlq_count}\n"
			f"Health: {json.dumps(health, default=str)}"
		),
	)
