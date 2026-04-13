# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class WebhookEventLog(Document):
	def validate(self):
		existing = frappe.db.get_value(
			"Webhook Event Log",
			{"provider": self.provider, "event_id": self.event_id},
			"name",
		)
		if existing and existing != self.name:
			frappe.throw(_("Duplicate webhook event for provider/event_id."), title=_("Webhook"))
