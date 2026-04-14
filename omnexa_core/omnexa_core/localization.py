# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt
"""Bilingual print labels plus MVP currency/date formatting (system locale)."""

import frappe
from frappe.utils import fmt_money, formatdate


PRINT_LABELS = {
	"invoice_number": {"en": "Invoice Number", "ar": "رقم الفاتورة"},
	"invoice_date": {"en": "Invoice Date", "ar": "تاريخ الفاتورة"},
	"customer": {"en": "Customer", "ar": "العميل"},
	"supplier": {"en": "Supplier", "ar": "المورد"},
	"total": {"en": "Total", "ar": "الإجمالي"},
	"tax_amount": {"en": "Tax Amount", "ar": "قيمة الضريبة"},
	"grand_total": {"en": "Grand Total", "ar": "الإجمالي النهائي"},
}


def _is_arabic_language(lang: str | None) -> bool:
	return (lang or "").lower().startswith("ar")


def get_current_language() -> str:
	return (getattr(frappe.local, "lang", None) or "en").lower()


def format_bilingual_text(arabic: str, english: str, lang: str | None = None, separator: str = " / ") -> str:
	arabic = (arabic or "").strip()
	english = (english or "").strip()

	if arabic and not english:
		return arabic
	if english and not arabic:
		return english
	if not arabic and not english:
		return ""

	active_lang = (lang or get_current_language()).lower()
	if _is_arabic_language(active_lang):
		return f"{arabic}{separator}{english}"
	return f"{english}{separator}{arabic}"


def get_print_label(label_key: str, lang: str | None = None, separator: str = " / ") -> str:
	entry = PRINT_LABELS.get((label_key or "").strip().lower())
	if not entry:
		fallback = (label_key or "").replace("_", " ").strip().title()
		return fallback

	return format_bilingual_text(
		arabic=entry.get("ar", ""),
		english=entry.get("en", ""),
		lang=lang,
		separator=separator,
	)


def format_currency_for_display(
	amount: float | int | str | None,
	currency: str | None = None,
	precision: int | None = None,
) -> str:
	"""
	Format money using site/System Settings (number format, currency symbol).

	MVP locale surface for statutory print and web; extends with explicit
	``currency`` when the document row differs from company default.
	"""
	return fmt_money(amount, currency=currency, precision=precision)


def format_date_for_locale(value) -> str:
	"""Format a date-like value using Frappe user/system date format."""
	return formatdate(value)
