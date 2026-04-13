# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import hashlib
import hmac
import json

import frappe
from frappe import _


class WebhookRejectedError(frappe.ValidationError):
	pass


def verify_signature(raw_body: str, received_signature: str, secret: str) -> bool:
	if not secret:
		raise WebhookRejectedError(_("Webhook secret is required for signature verification."))
	expected = hmac.new(secret.encode(), raw_body.encode(), hashlib.sha256).hexdigest()
	return hmac.compare_digest(expected, (received_signature or "").strip())


def process_webhook_event(provider: str, event_id: str, payload: dict, processor, received_signature: str = "", secret: str = ""):
	if not provider or not event_id:
		raise WebhookRejectedError(_("provider and event_id are required."))

	raw_body = json.dumps(payload, sort_keys=True)
	payload_hash = hashlib.sha256(raw_body.encode()).hexdigest()

	if secret and not verify_signature(raw_body, received_signature, secret):
		_log_event(provider, event_id, payload_hash, "Rejected", 401, "Invalid signature")
		raise WebhookRejectedError(_("Invalid webhook signature."))

	existing = frappe.db.get_value(
		"Webhook Event Log",
		{"provider": provider, "event_id": event_id},
		["name", "processing_status"],
		as_dict=True,
	)
	if existing:
		if existing.processing_status == "Processed":
			return {"status": "duplicate", "http_status_code": 200}
		frappe.db.set_value("Webhook Event Log", existing.name, "processing_status", "Duplicate")
		return {"status": "duplicate", "http_status_code": 202}

	log = _log_event(provider, event_id, payload_hash, "Received", 202, "")
	try:
		processor(payload)
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
		return {"status": "processed", "http_status_code": 200}
	except Exception as e:
		frappe.db.set_value(
			"Webhook Event Log",
			log.name,
			{
				"processing_status": "Error",
				"http_status_code": 500,
				"error_message": str(e),
			},
			update_modified=False,
		)
		raise


def _log_event(provider: str, event_id: str, payload_hash: str, status: str, http_status_code: int, error_message: str):
	doc = frappe.new_doc("Webhook Event Log")
	doc.provider = provider
	doc.event_id = event_id
	doc.payload_hash = payload_hash
	doc.processing_status = status
	doc.http_status_code = http_status_code
	doc.error_message = error_message
	doc.insert(ignore_permissions=True)
	return doc
