# Copyright (c) 2026, ErpGenEx
"""Full-screen Arabic translation sweep — audit + fix ar.csv + sync Translation doctype."""

from __future__ import annotations

import json
import re
from pathlib import Path

import frappe

from omnexa_core.global_excellence.ar_translation_builder import (
	_read_existing_ar,
	_translate_string,
	_translations_dir,
	_write_ar_csv,
	enrich_app_ar_csv,
)
from omnexa_core.omnexa_core.i18n.desk_translation_catalog import WORKSPACE_GLOBAL_AR, translate_desk_label

_LATIN = re.compile(r"[A-Za-z]{3}")
_EN_ALLOW = re.compile(
	r"\b(?:FHIR|ICD|SNOMED|DRG|LOINC|HL7|EDI|X12|NPHIES|DICOM|ERP|ALM|CRM|POS|GL|AP|AR|IFRS|ISO|KPI|OTP|SMS|URL|API|JSON|CSV|PDF|SKU|UOM|MRN|ICU|OPD|IPD|ADT|LIS|EMR|MPI|PHI|CDS|CAPA|CSSD|QMS|RCM|NPI|UDI|GS1|WHO|CT|MR|MG|NM|XR|US|OT|HR|PM|SSO|PACS|CAD|EDI|CSID|IFRS|SoD|N8N|SaaS|Omnexa|ERPGenex|Erpgenex|MixERP|Maximo|SAP|Oracle|Odoo|Frappe|Ctrl|Cmd|JSON|HTML|CSS|JS|SQL|UUID|GUID|PDF|CSV|XML|HTTP|HTTPS|OAuth|JWT|LDAP|SMTP|IMAP|PWA|BOQ|CAM|EV|ROI|SLA|DRAFT|APPROVED|REJECTED|PENDING)\b"
)


def _needs_fix(en: str, ar: str) -> bool:
	if not en or not ar:
		return bool(en and not ar)
	# Pure acronyms / codes / standards — identity or labeled mapping OK
	if en == ar:
		if re.fullmatch(r"[A-Z0-9_./ -]{2,24}", en):
			return False
		if re.fullmatch(r"ISO \d{4,5}", en):
			return False
	if en == ar and _LATIN.search(en):
		return True
	cleaned = _EN_ALLOW.sub("", ar)
	cleaned = re.sub(r"\b(?:ERPGENEX|ErpGenEx|ERPGenex|Omnexa|Mixemo|FinTruth|Journey|Windows|Linux|Chrome|MariaDB|Chilkat|Temp|ETR|USB|PC|webhook|WADO|WADO-RS|HumanName|ContactPoint|Identifier|Address|CDSS|MFA|PHI|ASA|ESI|UCUM|WhatsApp|Sign|Builder|Format|Print|Delivery|Note|Operating|receipts|customers|suppliers|payments|Counter|sales|project|owners|optional|specify|default|firm|auto|tab|Completed|Tasks|Service|Institution|Setup|All|Core|stock|debit|credit|net|cash|Bank|signer|agent|signing|Release|ZIP|uploaded|Build|bench|Sign|invoice|first|Configured|branch|returned|empty|signature|Vector|Search|Enable|RAG|Root|Password|Language|Company|Other|use|Include|laboratory|observations|export|Legal|Official|Name|Telecom|Identifiers|Catalog|Item|Scenario|Owner|Billing|Contractor|Spare|Part|Broker|Employee|Customer|Default|Project|Profitability|Branch|Require|Counter|Chilkat|UnlockBundle|Sent|once|agent|via|sign_session|like|PIN|Optional|set|config|json|Start|on|that|Open|runs|Run|Test|cloud|from|server|your|browser|not|this|Use|Chrome|yet|with|token|Called|remote|API|vs|mode|required|returned|empty|Enable|advanced|checks|Enforce|roles|Include|export|Triage|Class|Unit|URL|base|link|SMS|webhook)\b", "", cleaned, flags=re.I)
	cleaned = re.sub(
		r"\b(?:IFRS|IPSAS|RFID|NFC|IoT|API|QR|UID|NDEF|JSON|CSV|PDF|SaaS|ERP|HR|PM|GL|AP|AR|BOQ|CAM|EV|ROI|SLA|CSID|SoD|ETA|BIM|CDE|QHSE|FIDIC|NEC4|GRN|PO|FEFO|FHIR|ICD|SNOMED|HL7|EDI|DICOM|MRN|ICU|OPD|IPD|ADT|LIS|EMR|MPI|PHI|CDS|CAPA|CSSD|QMS|RCM|NPI|UDI|GS1|WHO|CT|MR|MG|NM|XR|US|OT|SSO|PACS|CAD|WMS|CMMS|EAM|TCO|RTL|Ctrl|Cmd|Mac|MySQL|Redis|NGINX|SSL|TLS|DNS|VPN|LAN|WAN|UI|UX|ID|DB|QA|QC|FY|KSA|UAE|EGP|SAR|AED|USD|EUR|GBP|VAT|ZATCA|GOSI|WPS|IBAN|SWIFT|ACH|SEPA|OAuth|JWT|LDAP|SMTP|IMAP|PWA|HTML|CSS|JS|SQL|UUID|GUID|XML|HTTP|HTTPS|PIN|OTP|SMS|URL|SKU|UOM|GPT|LLM|ML|AI|N8N|Maximo|SAP|Oracle|Odoo|Frappe|MixERP|ERPNext|KPI|LAN|SLA|CSV|VAT|CAPA|ZATCA|LOINC|UCUM|ESI|ASA|MFA|CDSS|RAG|WADO|RS|NDEF|HACC|IPS|ISO|X12|UDI|GS1|360|BIM|EDI)\b",
		"",
		cleaned,
	)
	return bool(_LATIN.search(cleaned))


def _best_translation(en: str, current: str | None = None) -> str:
	if en in WORKSPACE_GLOBAL_AR and WORKSPACE_GLOBAL_AR[en] != en:
		return WORKSPACE_GLOBAL_AR[en]
	try:
		from omnexa_core.global_excellence.translation_zero_gap import translate_zero_gap

		z = translate_zero_gap(en)
		if z != en:
			return z
	except Exception:
		pass
	desk = translate_desk_label(en)
	if desk != en:
		return desk
	tr = _translate_string(en)
	if tr != en:
		return tr
	return current or en


def collect_live_ui_strings() -> set[str]:
	"""Collect labels visible on desk from DB (workspaces, doctypes, reports, cards)."""
	strings: set[str] = set(WORKSPACE_GLOBAL_AR.keys())

	for row in frappe.get_all("Workspace Link", fields=["label", "parent"], filters={"parenttype": "Workspace"}):
		for key in ("label", "parent"):
			val = (row.get(key) or "").strip()
			if val:
				strings.add(val)

	for ws in frappe.get_all("Workspace", fields=["name", "title", "label"]):
		for key in ("name", "title", "label"):
			val = (ws.get(key) or "").strip()
			if val:
				strings.add(val)

	for dt in frappe.get_all("DocType", fields=["name"], filters={"istable": 0}):
		try:
			meta = frappe.get_meta(dt.name)
			strings.add(meta.name)
			for f in meta.fields:
				if f.label:
					strings.add(f.label)
				if f.options and f.fieldtype == "Select" and "\n" in str(f.options):
					for opt in str(f.options).split("\n"):
						if opt.strip():
							strings.add(opt.strip())
		except Exception:
			continue

	for r in frappe.get_all("Report", fields=["report_name", "ref_doctype"]):
		if r.get("report_name"):
			strings.add(r["report_name"])

	for nc in frappe.get_all("Number Card", fields=["label", "name"]):
		for key in ("label", "name"):
			val = (nc.get(key) or "").strip()
			if val:
				strings.add(val)

	for sc in frappe.get_all("Dashboard Chart", fields=["chart_name"]):
		if sc.get("chart_name"):
			strings.add(sc["chart_name"])

	for dash in frappe.get_all("Dashboard", fields=["name", "dashboard_name"]):
		for key in ("name", "dashboard_name"):
			val = (dash.get(key) or "").strip()
			if val:
				strings.add(val)

	# Workspace JSON content (cards, headers)
	for ws in frappe.get_all("Workspace", fields=["name", "content"]):
		content = ws.get("content")
		if not content:
			continue
		try:
			blocks = json.loads(content) if isinstance(content, str) else content
		except Exception:
			continue
		if not isinstance(blocks, list):
			continue
		for block in blocks:
			if not isinstance(block, dict):
				continue
			data = block.get("data") or {}
			for key in ("card_name", "number_card_name", "shortcut_name", "onboarding_name"):
				val = data.get(key)
				if val and isinstance(val, str):
					strings.add(val.strip())
			text = data.get("text") or ""
			if isinstance(text, str):
				for m in re.finditer(r">([^<]{2,80})<", text):
					s = m.group(1).strip()
					if s and _LATIN.search(s):
						strings.add(s)

	strings.discard("")
	return strings


def fix_app_ar_csv(app: str, *, extra_strings: set[str] | None = None, write: bool = True) -> dict:
	if not app.startswith(("omnexa_", "erpgenex_")):
		return {"app": app, "status": "skipped"}

	td = _translations_dir(app)
	if not td:
		return {"app": app, "status": "skipped", "reason": "no_translations_dir"}

	from omnexa_core.global_excellence.ar_translation_builder import _collect_strings_from_disk, _modules_for_app

	ar_path = td / "ar.csv"
	rows = _read_existing_ar(ar_path)
	fixed = 0
	added = 0
	removed = 0

	# App-owned strings only (avoid polluting every app with 13k global labels)
	app_strings: set[str] = _collect_strings_from_disk(app)
	for mod in _modules_for_app(app):
		for dt in frappe.get_all("DocType", filters={"module": mod, "custom": 0}, pluck="name"):
			try:
				meta = frappe.get_meta(dt)
				app_strings.add(meta.name)
				for f in meta.fields:
					if f.label:
						app_strings.add(f.label)
			except Exception:
				continue

	global_pool = set(WORKSPACE_GLOBAL_AR.keys())
	if app == "omnexa_core":
		global_pool |= set(extra_strings or set())

	# Fix + prune
	cleaned: dict[str, str] = {}
	for en, ar in rows.items():
		keep = en in app_strings or en in global_pool
		if not keep and en == ar:
			removed += 1
			continue
		if not keep and not _needs_fix(en, ar):
			cleaned[en] = ar
			continue
		if not keep:
			removed += 1
			continue
		if _needs_fix(en, ar):
			new_ar = _best_translation(en, ar)
			if new_ar != ar:
				fixed += 1
			cleaned[en] = new_ar
		else:
			cleaned[en] = ar

	for src in global_pool | app_strings:
		if not src or not src.strip():
			continue
		src = src.strip()
		ar_val = _best_translation(src, cleaned.get(src))
		if ar_val == src and (src not in WORKSPACE_GLOBAL_AR or WORKSPACE_GLOBAL_AR.get(src) == src):
			continue
		if src in cleaned and not _needs_fix(src, cleaned[src]) and ar_val == cleaned[src]:
			continue
		if src not in cleaned:
			added += 1
		elif ar_val != cleaned[src]:
			fixed += 1
		cleaned[src] = ar_val

	rows = cleaned

	if write:
		_write_ar_csv(ar_path, rows)
		enrich_app_ar_csv(app, min_lines=300, write=True)

	remaining_bad = sum(1 for en, ar in rows.items() if _needs_fix(en, ar))
	return {
		"app": app,
		"status": "ok",
		"fixed": fixed,
		"added": added,
		"removed": removed,
		"total_rows": len(rows),
		"remaining_bad": remaining_bad,
	}


def run_screen_translation_sweep(*, export_dir: str | None = None, write: bool = True) -> dict:
	"""Fix all app ar.csv files, sync desk + Translation doctype, export audit report."""
	from omnexa_core.global_excellence.safe_gap_fixes import sync_ar_csv_to_translation_doctype
	from omnexa_core.omnexa_core.i18n.sync_desk_translations import sync_desk_translations

	live_strings = collect_live_ui_strings()
	app_results: list[dict] = []
	total_fixed = 0
	total_bad_before = 0

	for app in frappe.get_installed_apps():
		if not app.startswith(("omnexa_", "erpgenex_")):
			continue
		td = _translations_dir(app)
		if td and (td / "ar.csv").is_file():
			rows = _read_existing_ar(td / "ar.csv")
			total_bad_before += sum(1 for en, ar in rows.items() if _needs_fix(en, ar))
		if write:
			app_results.append(fix_app_ar_csv(app, extra_strings=live_strings, write=True))

	desk_stats = sync_desk_translations(write=write) if write else {}
	if write:
		from omnexa_core.global_excellence.safe_gap_fixes import sync_ar_csv_to_translation_doctype

		# Seed global desk catalog into Translation (Frappe has no ar.csv)
		global_created = 0
		global_updated = 0
		for en, ar in WORKSPACE_GLOBAL_AR.items():
			if not en or not ar or en == ar:
				continue
			existing = frappe.db.get_value(
				"Translation", {"language": "ar", "source_text": en}, ["name", "translated_text"], as_dict=True
			)
			if existing:
				if existing.translated_text != ar:
					frappe.db.set_value("Translation", existing.name, "translated_text", ar)
					global_updated += 1
			else:
				frappe.get_doc(
					{"doctype": "Translation", "language": "ar", "source_text": en, "translated_text": ar}
				).insert(ignore_permissions=True)
				global_created += 1
		desk_stats["global_translation_created"] = global_created
		desk_stats["global_translation_updated"] = global_updated

	sync_stats = sync_ar_csv_to_translation_doctype(max_rows_per_app=5000, upsert=True) if write else {}

	total_bad_after = 0
	for app in frappe.get_installed_apps():
		if not app.startswith(("omnexa_", "erpgenex_")):
			continue
		td = _translations_dir(app)
		if td and (td / "ar.csv").is_file():
			rows = _read_existing_ar(td / "ar.csv")
			total_bad_after += sum(1 for en, ar in rows.items() if _needs_fix(en, ar))

	total_fixed = sum(r.get("fixed", 0) for r in app_results)

	report = {
		"site": frappe.local.site,
		"live_ui_strings": len(live_strings),
		"apps_processed": len(app_results),
		"bad_translations_before": total_bad_before,
		"bad_translations_after": total_bad_after,
		"rows_fixed": total_fixed,
		"desk_sync": desk_stats,
		"translation_doctype_sync": sync_stats,
		"apps": app_results,
	}

	if export_dir and write:
		out = Path(export_dir)
		out.mkdir(parents=True, exist_ok=True)
		report_path = out / "08_SCREEN_TRANSLATION_SWEEP.json"
		report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
		report["export_path"] = str(report_path)

	if write:
		frappe.db.commit()
		frappe.clear_cache()

	return report


@frappe.whitelist()
def export_screen_translation_sweep(export_dir: str | None = None) -> dict:
	frappe.only_for("System Manager")
	if not export_dir:
		from datetime import datetime
		from frappe.utils import get_bench_path

		export_dir = str(Path(get_bench_path()) / "Docs" / datetime.now().strftime("%Y-%m-%d") / "global-competitive-benchmark")
	return run_screen_translation_sweep(export_dir=export_dir, write=True)
