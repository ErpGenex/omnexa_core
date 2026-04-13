# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe import _

BOUNCE_KEYS = {"hard_bounce", "soft_bounce", "complaint", "invalid_number"}


def normalize_bounce_event(channel: str, provider_payload: dict) -> dict:
	channel = (channel or "").strip().lower()
	if channel not in {"email", "sms"}:
		frappe.throw(_("Unsupported channel for bounce handling."), title=_("Bounce"))
	recipient = (provider_payload.get("recipient") or "").strip().lower()
	if not recipient:
		frappe.throw(_("Bounce event recipient is required."), title=_("Bounce"))
	event_type = (provider_payload.get("event_type") or "").strip().lower()
	if event_type not in BOUNCE_KEYS:
		frappe.throw(_("Unsupported bounce event type."), title=_("Bounce"))
	return {
		"channel": channel,
		"recipient": recipient,
		"event_type": event_type,
		"provider_ref": (provider_payload.get("provider_ref") or "").strip(),
	}


def mark_recipient_bounced(channel: str, provider_payload: dict):
	event = normalize_bounce_event(channel, provider_payload)
	store = frappe.cache().hget("omnexa_bounce_registry", event["recipient"])
	if not store:
		store = {}
	store[event["channel"]] = event["event_type"]
	frappe.cache().hset("omnexa_bounce_registry", event["recipient"], store)
	return event


def should_suppress_recipient(recipient: str, channel: str) -> bool:
	recipient = (recipient or "").strip().lower()
	channel = (channel or "").strip().lower()
	if not recipient or channel not in {"email", "sms"}:
		return False
	store = frappe.cache().hget("omnexa_bounce_registry", recipient) or {}
	if not isinstance(store, dict):
		return False
	return bool(store.get(channel))
