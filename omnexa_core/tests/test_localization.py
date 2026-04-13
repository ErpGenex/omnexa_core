# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core.localization import format_bilingual_text, get_print_label


class TestLocalization(FrappeTestCase):
	def test_format_bilingual_text_orders_by_language(self):
		self.assertEqual(format_bilingual_text("العميل", "Customer", lang="ar"), "العميل / Customer")
		self.assertEqual(format_bilingual_text("العميل", "Customer", lang="en"), "Customer / العميل")

	def test_format_bilingual_text_handles_missing_side(self):
		self.assertEqual(format_bilingual_text("", "Customer", lang="ar"), "Customer")
		self.assertEqual(format_bilingual_text("العميل", "", lang="en"), "العميل")

	def test_get_print_label_uses_dictionary_and_fallback(self):
		old_lang = getattr(frappe.local, "lang", None)
		try:
			frappe.local.lang = "ar"
			self.assertEqual(get_print_label("invoice_number"), "رقم الفاتورة / Invoice Number")
			self.assertEqual(get_print_label("unknown_custom_label"), "Unknown Custom Label")
		finally:
			frappe.local.lang = old_lang
