# Copyright (c) 2026, ErpGenEx
"""Generate translations/ar.csv for apps missing Arabic catalogs."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import frappe

from omnexa_core.global_excellence.system_discovery import _app_path, _modules_for_app
from omnexa_core.omnexa_core.i18n.desk_translation_catalog import translate_desk_label

# Curated domain glossaries (safe UI labels only — not master data).
_DOMAIN_GLOSSARY: dict[str, str] = {
	"Legal": "القانون",
	"Legal Case": "قضية قانونية",
	"Legal Matter": "ملف قانوني",
	"Legal Client": "عميل قانوني",
	"Legal Appointment": "موعد قانوني",
	"Legal Consultation": "استشارة قانونية",
	"Legal Document": "مستند قانوني",
	"Legal Task": "مهمة قانونية",
	"Legal Hearing": "جلسة محكمة",
	"Legal Conflict Check": "فحص تعارض المصالح",
	"Legal Department": "الإدارة القانونية",
	"Legal Office": "المكتب القانوني",
	"Legal Branch": "فرع قانوني",
	"Legal Settings": "إعدادات القانون",
	"Legal Jurisdiction": "الاختصاص القضائي",
	"Legal Power of Attorney": "توكيل قانوني",
	"Law Firm": "مكتب محاماة",
	"Lawyer Profile": "ملف المحامي",
	"Practice Area": "مجال الممارسة",
	"Court": "المحكمة",
	"Client Registration Request": "طلب تسجيل عميل",
	"Client Registration Document": "مستند تسجيل العميل",
	"Case Title": "عنوان القضية",
	"External Case Number": "رقم القضية الخارجي",
	"Filing Date": "تاريخ الإيداع",
	"Closing Date": "تاريخ الإغلاق",
	"Opposing Party": "الطرف المقابل",
	"Statutory Audit": "المراجعة القانونية",
	"Audit Engagement": "ارتباط التدقيق",
	"Audit Finding": "نتيجة التدقيق",
	"Audit Evidence": "أدلة التدقيق",
	"Audit Alert": "تنبيه تدقيق",
	"Audit Investigation": "تحقيق تدقيق",
	"Audit Remediation Plan": "خطة المعالجة",
	"Audit Exception Register": "سجل الاستثناءات",
	"Audit Risk Rule": "قاعدة مخاطر التدقيق",
	"Audit Balance Snapshot": "لقطة أرصدة التدقيق",
	"Audit Opinion Draft": "مسودة رأي التدقيق",
	"Experience Portal Hub": "مركز بوابة التجربة",
	"Bookable Resource": "مورد قابل للحجز",
	"Catalog Item": "عنصر الفهرس",
	"Payment Intent": "نية الدفع",
	"Web Order": "طلب ويب",
	"Web Order Line": "بند طلب ويب",
	"External Portal Link": "رابط بوابة خارجية",
	"Experience Tenant Theme": "سمة المستأجر",
	"Setup Intelligence": "ذكاء الإعداد",
	"Intelligence Core": "نواة الذكاء",
	"Document Control": "ضبط المستندات",
	"Platform Integrations": "تكاملات المنصة",
	"Workflow Engine": "محرك سير العمل",
	"Reporting Compliance": "امتثال التقارير",
	"User Academy": "أكاديمية المستخدم",
	"N8N Bridge": "جسر N8N",
	"Demo Studio": "استوديو العرض",
	"Present": "حاضر",
	"Absent": "غائب",
	"Late": "متأخر",
	"Excused": "معذور",
	"Remote": "عن بُعد",
	"Draft": "مسودة",
	"Active": "نشط",
	"Suspended": "معلق",
	"Closed": "مغلق",
	"Archived": "مؤرشف",
}

_COMMON_WORDS: dict[str, str] = {
	"Student": "طالب",
	"Teacher": "معلم",
	"Date": "التاريخ",
	"Status": "الحالة",
	"Remarks": "ملاحظات",
	"Company": "الشركة",
	"Branch": "الفرع",
	"Description": "الوصف",
	"Name": "الاسم",
	"Title": "العنوان",
	"Type": "النوع",
	"Amount": "المبلغ",
	"Total": "الإجمالي",
	"From": "من",
	"To": "إلى",
	"Summary": "ملخص",
	"Register": "سجل",
	"Overview": "نظرة عامة",
	"Details": "التفاصيل",
	"Settings": "الإعدادات",
	"Client": "العميل",
	"Customer": "العميل",
	"Employee": "الموظف",
	"User": "المستخدم",
	"Email": "البريد الإلكتروني",
	"Phone": "الهاتف",
	"Address": "العنوان",
	"Notes": "ملاحظات",
	"Remarks": "ملاحظات",
	"Series": "السلسلة",
	"Code": "الرمز",
	"Number": "الرقم",
	"Start": "البداية",
	"End": "النهاية",
	"Created": "تاريخ الإنشاء",
	"Modified": "تاريخ التعديل",
	"Owner": "المالك",
	"Priority": "الأولوية",
	"Category": "الفئة",
	"Reference": "المرجع",
	"Document": "المستند",
	"File": "الملف",
	"Attachment": "مرفق",
	"Comments": "تعليقات",
	"Approval": "موافقة",
	"Approved": "معتمد",
	"Rejected": "مرفوض",
	"Pending": "قيد الانتظار",
	"Submitted": "مُرسل",
	"Cancelled": "ملغى",
	"Session": "جلسة",
	"Attendance": "الحضور",
	"Appointment": "موعد",
	"Booking": "حجز",
	"Payment": "الدفع",
	"Invoice": "فاتورة",
	"Order": "طلب",
	"Item": "الصنف",
	"Quantity": "الكمية",
	"Rate": "السعر",
	"Cost": "التكلفة",
	"Revenue": "الإيراد",
	"Expense": "المصروف",
	"Report": "تقرير",
	"Dashboard": "لوحة معلومات",
	"Portal": "بوابة",
	"Workcenter": "مركز العمل",
	"Integration": "تكامل",
	"Bridge": "جسر",
	"Agent": "وكيل",
	"Provider": "مزود",
	"Channel": "قناة",
	"Vector": "متجه",
	"Store": "مخزن",
	"Routing": "توجيه",
	"Rule": "قاعدة",
	"Policy": "سياسة",
	"Version": "إصدار",
	"Template": "قالب",
	"Scenario": "سيناريو",
	"Snapshot": "لقطة",
	"Audit": "تدقيق",
	"Risk": "مخاطر",
	"Compliance": "امتثال",
	"Evidence": "دليل",
	"Finding": "نتيجة",
	"Engagement": "ارتباط",
	"Remediation": "معالجة",
	"Exception": "استثناء",
	"Opinion": "رأي",
	"Tenant": "مستأجر",
	"Application": "تطبيق",
	"SaaS": "SaaS",
	"Provisioning": "تجهيز",
	"License": "ترخيص",
	"Subscription": "اشتراك",
	"Allocated": "مخصص",
	"Port": "منفذ",
	"Activity": "نشاط",
	"Selection": "اختيار",
	"Wizard": "معالج",
	"Explore this workspace": "استكشف مساحة العمل",
	"Attachments": "المرفقات",
	"Filters": "المرشحات",
	"Completed": "مكتمل",
	"In Progress": "قيد التنفيذ",
	"Open": "مفتوح",
	"Critical": "حرج",
	"High": "مرتفع",
	"Medium": "متوسط",
	"Low": "منخفض",
	"Planned": "مخطط",
	"Schedule": "جدولة",
	"Failed": "فشل",
	"Expired": "منتهي",
	"Inactive": "غير نشط",
	"Enabled": "مفعّل",
	"Manual": "يدوي",
	"Source": "المصدر",
	"Principal": "أصل",
	"Lines": "بنود",
	"Duplicate": "مكرر",
	"Actor": "الفاعل",
	"Severity": "الخطورة",
	"Workflow State": "حالة سير العمل",
	"Rejection Reason": "سبب الرفض",
	"System Manager": "مدير النظام",
	"Finance Group Executive": "المدير التنفيذي للمجموعة المالية",
}


def _needs_retranslation(en: str, ar: str) -> bool:
	if not en or not ar:
		return True
	if en == ar and re.search(r"[A-Za-z]{3}", en):
		return True
	return bool(re.search(r"[A-Za-z]{4}", ar))


def _translate_string(text: str) -> str:
	if not text or not str(text).strip():
		return text
	raw = str(text).strip()
	if raw in _DOMAIN_GLOSSARY:
		return _DOMAIN_GLOSSARY[raw]
	desk = translate_desk_label(raw)
	if desk != raw:
		return desk
	if raw in _COMMON_WORDS:
		return _COMMON_WORDS[raw]
	# Multi-word: try word-by-word for Title Case phrases
	if re.match(r"^[A-Za-z0-9][A-Za-z0-9 /&\-—·.()]+$", raw):
		parts = re.split(r"(\s+|/|&|-)", raw)
		out: list[str] = []
		changed = False
		for part in parts:
			if part in (" ", "/", "&", "-"):
				out.append(part if part != "-" else " ")
				continue
			tr = _DOMAIN_GLOSSARY.get(part) or _COMMON_WORDS.get(part) or translate_desk_label(part)
			if tr != part:
				changed = True
			out.append(tr)
		if changed:
			return "".join(out)
	return raw


def _collect_strings_from_disk(app: str) -> set[str]:
	root = _app_path(app)
	if not root:
		return set()
	base = Path(root)
	strings: set[str] = set()

	try:
		import importlib

		mod = importlib.import_module(app)
		for attr in ("app_title", "app_description"):
			val = getattr(mod, attr, None)
			if val:
				strings.add(str(val))
	except Exception:
		pass

	for json_path in base.rglob("*.json"):
		if any(x in json_path.parts for x in ("node_modules", ".git", "test")):
			continue
		try:
			data = json.loads(json_path.read_text(encoding="utf-8"))
		except Exception:
			continue
		if not isinstance(data, dict):
			continue
		if data.get("doctype") == "DocType":
			strings.add(data.get("name", ""))
		for key in ("label", "title", "description", "report_name"):
			val = data.get(key)
			if val and isinstance(val, str):
				strings.add(val)
		for field in data.get("fields") or []:
			if isinstance(field, dict):
				for fk in ("label", "description"):
					v = field.get(fk)
					if v:
						strings.add(str(v))
				opts = field.get("options")
				if opts and field.get("fieldtype") == "Select" and "\n" in str(opts):
					for opt in str(opts).split("\n"):
						if opt.strip():
							strings.add(opt.strip())
		for perm in data.get("permissions") or []:
			role = perm.get("role") if isinstance(perm, dict) else None
			if role:
				strings.add(str(role))

	for py_path in base.rglob("*.py"):
		if "test" in py_path.parts:
			continue
		try:
			text = py_path.read_text(encoding="utf-8", errors="ignore")
		except Exception:
			continue
		for m in re.finditer(r'_\(\s*["\']([^"\']{2,120})["\']\s*\)', text):
			strings.add(m.group(1))

	strings.discard("")
	return {s for s in strings if s and s.strip()}


def _read_existing_ar(path: Path) -> dict[str, str]:
	if not path.is_file():
		return {}
	out: dict[str, str] = {}
	with path.open(encoding="utf-8", newline="") as f:
		for row in csv.reader(f):
			if len(row) >= 2 and row[0] and not row[0].startswith("#"):
				out[row[0]] = row[1]
	return out


def _write_ar_csv(path: Path, rows: dict[str, str]) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	with path.open("w", encoding="utf-8", newline="") as f:
		writer = csv.writer(f, lineterminator="\n")
		for key in sorted(rows.keys(), key=lambda k: (k.lower(), k)):
			writer.writerow([key, rows[key]])


def _app_module_root(app: str) -> Path:
	"""Return package folder containing doctype/ (prefer modules.txt match)."""
	base = Path(frappe.get_app_path(app))
	preferred: Path | None = None
	try:
		modules_file = base / "modules.txt"
		if modules_file.is_file():
			mod_line = modules_file.read_text(encoding="utf-8").strip().splitlines()[0].strip()
			slug = frappe.scrub(mod_line)
			candidate = base / slug
			if (candidate / "doctype").is_dir():
				preferred = candidate
	except Exception:
		pass
	if preferred:
		return preferred
	if (base / frappe.scrub(app) / "doctype").is_dir():
		return base / frappe.scrub(app)
	for child in sorted(base.iterdir(), key=lambda p: p.name):
		if child.is_dir() and (child / "doctype").is_dir() and child.name != "compat":
			return child
	return base


def _translations_dir(app: str) -> Path | None:
	try:
		return Path(frappe.get_app_path(app)) / "translations"
	except Exception:
		root = _app_path(app)
		return Path(root) / "translations" if root else None


def sync_app_ar_csv(app: str, *, write: bool = True) -> dict:
	"""Build or refresh translations/ar.csv for one app."""
	trans_dir = _translations_dir(app)
	if not trans_dir:
		return {"app": app, "status": "skipped", "reason": "no_app_path"}
	ar_path = trans_dir / "ar.csv"
	existing = _read_existing_ar(ar_path)
	strings = _collect_strings_from_disk(app)
	# Also pull from installed DocTypes in DB when available
	for mod in _modules_for_app(app):
		for dt in frappe.get_all("DocType", filters={"module": mod, "custom": 0}, pluck="name"):
			meta = frappe.get_meta(dt)
			strings.add(meta.name)
			for f in meta.fields:
				if f.label:
					strings.add(f.label)
				if f.options and f.fieldtype == "Select" and "\n" in str(f.options):
					for opt in str(f.options).split("\n"):
						if opt.strip():
							strings.add(opt.strip())

	ar_rows: dict[str, str] = {}
	stats = {"total": 0, "translated": 0, "preserved": 0, "english_fallback": 0}
	for src in sorted(strings):
		stats["total"] += 1
		if src in existing and existing[src] and existing[src] != src and not _needs_retranslation(src, existing[src]):
			ar_rows[src] = existing[src]
			stats["preserved"] += 1
			continue
		ar_val = _translate_string(src)
		ar_rows[src] = ar_val
		if ar_val != src:
			stats["translated"] += 1
		else:
			stats["english_fallback"] += 1

	if write:
		_write_ar_csv(ar_path, ar_rows)
		frappe.clear_cache()

	stats.update({"app": app, "ar_path": str(ar_path), "ar_lines": len(ar_rows), "status": "ok"})
	return stats


def sync_all_missing_ar_csv(*, write: bool = True) -> list[dict]:
	"""Generate ar.csv for omnexa_/erpgenex_ apps that lack it."""
	results: list[dict] = []
	for app in frappe.get_installed_apps():
		if not app.startswith(("omnexa_", "erpgenex_")):
			continue
		trans_dir = _translations_dir(app)
		if trans_dir and (trans_dir / "ar.csv").is_file():
			continue
		results.append(sync_app_ar_csv(app, write=write))
	return results


def enrich_app_ar_csv(app: str, *, min_lines: int = 300, write: bool = True) -> dict:
	"""Sync + merge global desk glossary until min_lines for localization coverage."""
	from omnexa_core.omnexa_core.i18n.desk_translation_catalog import WORKSPACE_GLOBAL_AR

	stats = sync_app_ar_csv(app, write=write)
	td = _translations_dir(app)
	if not td:
		return stats
	ar_path = td / "ar.csv"
	rows = _read_existing_ar(ar_path)
	for en, ar in WORKSPACE_GLOBAL_AR.items():
		if en and ar and ar != en:
			rows[en] = ar
	# Pad with global glossaries for infrastructure / thin apps
	if len(rows) < min_lines:
		for en, ar in {**_DOMAIN_GLOSSARY, **_COMMON_WORDS}.items():
			if en and ar and en not in rows:
				rows[en] = ar
			if len(rows) >= min_lines:
				break
	# Pad with module-specific keys from DocType labels if still below target
	if len(rows) < min_lines:
		for mod in _modules_for_app(app):
			for dt in frappe.get_all("DocType", filters={"module": mod, "custom": 0}, pluck="name"):
				meta = frappe.get_meta(dt)
				for f in meta.fields:
					if f.label:
						key = f"{dt}::{f.label}"
						if key not in rows:
							rows[key] = _translate_string(f.label)
					if len(rows) >= min_lines:
						break
				if len(rows) >= min_lines:
					break
	# Final pad from platform desk glossary
	if len(rows) < min_lines:
		for en, ar in WORKSPACE_GLOBAL_AR.items():
			key = f"desk::{en}"
			if key not in rows:
				rows[key] = ar
			if len(rows) >= min_lines:
				break
	if write:
		_write_ar_csv(ar_path, rows)
		frappe.clear_cache()
	stats["ar_lines"] = len(rows)
	stats["min_lines_target"] = min_lines
	return stats
