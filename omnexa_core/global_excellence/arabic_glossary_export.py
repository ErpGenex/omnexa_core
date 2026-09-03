# Copyright (c) 2026, ErpGenEx
"""Export ERPGENEX_ARABIC_GLOSSARY and ARABIC_TERMINOLOGY_RULES."""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path

import frappe

from omnexa_core.global_excellence.ar_translation_builder import _COMMON_WORDS, _DOMAIN_GLOSSARY, _translations_dir
from omnexa_core.global_excellence.system_discovery import _app_path, _modules_for_app
from omnexa_core.omnexa_core.i18n.desk_translation_catalog import WORKSPACE_GLOBAL_AR

_DOMAIN_HINTS: dict[str, str] = {
	"Customer": "CRM",
	"Supplier": "Procurement",
	"Sales Invoice": "Accounting",
	"Purchase Order": "Procurement",
	"Journal Entry": "Accounting",
	"Workflow": "Platform",
	"Employee": "HR",
	"Legal Case": "Legal",
	"Patient": "Healthcare",
	"Student": "Education",
}

_FORBIDDEN_ALTERNATIVES: dict[str, list[str]] = {
	"Customer": ["الزبون", "زبون", "عميل تجاري"],
	"Supplier": ["الموردين", "بائع"],
	"Submit": ["إرسال", "ارسال"],
	"Cancel": ["الغاء", "إلغ"],
	"Draft": ["مسوده", "مُسودة"],
	"Warehouse": ["مخزن", "مستودعات"],
	"Invoice": ["فاتورة", "فاتوره"],
}

_TERMINOLOGY_RULES: list[dict] = [
	{
		"rule_id": "TERM-001",
		"english_term": "Customer",
		"standard_arabic": "العميل",
		"forbidden_terms": ["الزبون", "زبون"],
		"domain": "CRM / Sales",
		"rationale": "مصطلح ERP موحّد — Customer = العميل في كل التطبيقات",
	},
	{
		"rule_id": "TERM-002",
		"english_term": "Supplier",
		"standard_arabic": "المورد",
		"forbidden_terms": ["البائع", "مزود"],
		"domain": "Procurement",
		"rationale": "Supplier في سياق الشراء ≠ Vendor عام",
	},
	{
		"rule_id": "TERM-003",
		"english_term": "Submit",
		"standard_arabic": "إرسال للاعتماد",
		"forbidden_terms": ["تقديم", "ارسال"],
		"domain": "Workflow",
		"context": "DocType submittable actions",
		"rationale": "يوضح أن الإجراء يرسل للموافقة",
	},
	{
		"rule_id": "TERM-004",
		"english_term": "Workflow",
		"standard_arabic": "سير العمل",
		"forbidden_terms": ["مسار العمل", "تدفق العمل"],
		"domain": "Platform",
		"rationale": "مصطلح Frappe/ERPNext المعياري",
	},
	{
		"rule_id": "TERM-005",
		"english_term": "Sales Invoice",
		"standard_arabic": "فاتورة مبيعات",
		"forbidden_terms": ["فاتورة البيع", "فاتورة المبيعات"],
		"domain": "Accounting",
		"rationale": "اتساق مع ERPNext Arabic",
	},
	{
		"rule_id": "TERM-006",
		"english_term": "Purchase Order",
		"standard_arabic": "أمر شراء",
		"forbidden_terms": ["طلب شراء", "أمر الشراء"],
		"domain": "Procurement",
		"rationale": "مصطلح محاسبي قياسي",
	},
	{
		"rule_id": "TERM-007",
		"english_term": "Company",
		"standard_arabic": "الشركة",
		"forbidden_terms": ["المؤسسة", "المنشأة"],
		"domain": "Organization",
		"rationale": "Company في Frappe = الشركة",
	},
	{
		"rule_id": "TERM-008",
		"english_term": "Branch",
		"standard_arabic": "الفرع",
		"forbidden_terms": ["فرع", "الفروع"],
		"domain": "Organization",
		"rationale": "مصطلح العزل المؤسسي في ERPGenex",
	},
]


def _collect_from_ar_csv() -> dict[str, set[str]]:
	"""Map English source → set of Arabic translations found across apps."""
	term_map: dict[str, set[str]] = defaultdict(set)
	for app in frappe.get_installed_apps():
		if not app.startswith(("omnexa_", "erpgenex_")):
			continue
		td = _translations_dir(app)
		if not td:
			continue
		ar_path = td / "ar.csv"
		if not ar_path.is_file():
			continue
		try:
			with ar_path.open(encoding="utf-8", newline="") as f:
				for row in csv.reader(f):
					if len(row) >= 2 and row[0] and row[1]:
						term_map[row[0].strip()].add(row[1].strip())
		except Exception:
			continue
	return term_map


def _collect_from_doctypes() -> dict[str, str]:
	terms: dict[str, str] = {}
	for mod in frappe.get_all("Module Def", pluck="name"):
		for dt in frappe.get_all("DocType", filters={"module": mod, "custom": 0, "istable": 0}, pluck="name")[:200]:
			meta = frappe.get_meta(dt)
			terms[dt] = dt
			for f in meta.fields:
				if f.label:
					terms[f.label] = f.label
	return terms


def build_arabic_glossary() -> list[dict]:
	"""Build unified glossary from desk catalog, domain glossary, and ar.csv files."""
	rows: dict[str, dict] = {}
	term_variants = _collect_from_ar_csv()

	def _add(en: str, ar: str, *, domain: str = "Platform", context: str = "UI Label") -> None:
		if not en or not ar or en == ar:
			return
		key = en.strip()
		if key in rows:
			return
		alts = sorted(term_variants.get(key, set()) - {ar})
		forbidden = _FORBIDDEN_ALTERNATIVES.get(key, [])
		rows[key] = {
			"english_term": key,
			"arabic_term": ar,
			"domain": _DOMAIN_HINTS.get(key, domain),
			"context": context,
			"alternative_terms": alts[:5],
			"forbidden_terms": forbidden,
			"example": f'{key} → {ar}',
		}

	for en, ar in WORKSPACE_GLOBAL_AR.items():
		_add(en, ar, domain="Workspace", context="Desk / Portal")
	for en, ar in _DOMAIN_GLOSSARY.items():
		_add(en, ar, domain="Vertical", context="Domain DocType / Field")
	for en, ar in _COMMON_WORDS.items():
		_add(en, ar, domain="Common", context="Shared UI")

	for en in _collect_from_doctypes():
		ar = WORKSPACE_GLOBAL_AR.get(en) or _DOMAIN_GLOSSARY.get(en) or _COMMON_WORDS.get(en)
		if ar:
			_add(en, ar, domain="DocType", context="Database metadata")

	# Pull high-frequency terms from merged ar.csv
	for en, variants in list(term_variants.items())[:500]:
		if en in rows or not variants:
			continue
		ar = sorted(variants, key=len)[0]
		if re.search(r"[\u0600-\u06FF]", ar):
			_add(en, ar, domain="App CSV", context="translations/ar.csv")

	return sorted(rows.values(), key=lambda r: (r["domain"], r["english_term"].lower()))


def build_terminology_rules(*, glossary: list[dict] | None = None) -> list[dict]:
	"""Return terminology normalization rules + inconsistency findings."""
	glossary = glossary or build_arabic_glossary()
	term_variants = _collect_from_ar_csv()
	inconsistencies: list[dict] = []
	for entry in glossary:
		en = entry["english_term"]
		standard = entry["arabic_term"]
		variants = term_variants.get(en, set())
		non_standard = sorted(v for v in variants if v != standard)
		if len(non_standard) > 0:
			inconsistencies.append(
				{
					"english_term": en,
					"standard_arabic": standard,
					"inconsistent_variants": non_standard,
					"action": "normalize_to_standard",
				}
			)

	rules = [{**r, "status": "active"} for r in _TERMINOLOGY_RULES]
	return {
		"rules": rules,
		"inconsistencies_found": len(inconsistencies),
		"inconsistencies": inconsistencies[:100],
		"policy": {
			"do_not_translate_master_data": True,
			"ui_only": True,
			"glossary_authority": "ERPGENEX_ARABIC_GLOSSARY",
		},
	}


def export_arabic_glossary_artifacts(export_dir: Path) -> dict:
	export_dir.mkdir(parents=True, exist_ok=True)
	glossary = build_arabic_glossary()
	terminology = build_terminology_rules(glossary=glossary)
	glossary_path = export_dir / "ERPGENEX_ARABIC_GLOSSARY.json"
	rules_path = export_dir / "ARABIC_TERMINOLOGY_RULES.json"
	glossary_path.write_text(
		json.dumps({"generated": frappe.utils.now(), "term_count": len(glossary), "terms": glossary}, ensure_ascii=False, indent=2),
		encoding="utf-8",
	)
	rules_path.write_text(json.dumps(terminology, ensure_ascii=False, indent=2), encoding="utf-8")
	return {"glossary_path": str(glossary_path), "rules_path": str(rules_path), "term_count": len(glossary)}
