# Copyright (c) 2026, ErpGenEx

import frappe
from frappe.model.document import Document

from omnexa_core.omnexa_core.app_visibility import clear_desk_visibility_cache


class OmnexaMarketplaceSettings(Document):
	def on_update(self):
		clear_desk_visibility_cache()
