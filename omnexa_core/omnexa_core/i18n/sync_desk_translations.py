# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Sync workspace sidebar labels into omnexa_core translations."""

from __future__ import annotations

import csv
from pathlib import Path

import frappe

from omnexa_core.omnexa_core.i18n.desk_translation_catalog import (
	WORKSPACE_GLOBAL_AR,
	translate_desk_label,
)

_TRANSLATIONS_DIR = Path(__file__).resolve().parents[2] / "translations"


def collect_workspace_labels() -> set[str]:
	labels: set[str] = set(WORKSPACE_GLOBAL_AR.keys())
	for row in frappe.get_all("Workspace Link", fields=["label", "type"], filters={"parenttype": "Workspace"}):
		label = (row.get("label") or "").strip()
		if label:
			labels.add(label)
	for name in frappe.get_all("Workspace", pluck="name"):
		labels.add(name)
		title = frappe.db.get_value("Workspace", name, "title")
		if title:
			labels.add(title)
		label = frappe.db.get_value("Workspace", name, "label")
		if label:
			labels.add(label)
	return {s for s in labels if s and s.strip()}


def _read_csv(path: Path) -> dict[str, str]:
	if not path.exists():
		return {}
	out: dict[str, str] = {}
	with path.open(encoding="utf-8", newline="") as f:
		for row in csv.reader(f):
			if len(row) >= 2 and row[0] and not row[0].startswith("#"):
				out[row[0]] = row[1]
	return out


def _write_csv(path: Path, rows: dict[str, str]) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	with path.open("w", encoding="utf-8", newline="") as f:
		writer = csv.writer(f, lineterminator="\n")
		for key in sorted(rows.keys(), key=lambda k: (k.lower(), k)):
			writer.writerow([key, rows[key]])


def sync_desk_translations(*, write: bool = True) -> dict:
	ar_path = _TRANSLATIONS_DIR / "ar.csv"
	existing = _read_csv(ar_path)
	strings = collect_workspace_labels()
	stats = {"total": len(strings), "added": 0, "kept": 0, "still_english": 0}

	for src in strings:
		ar_val = translate_desk_label(src)
		if ar_val == src and src in existing:
			prev = existing[src]
			if prev and prev != src:
				ar_val = prev
				stats["kept"] += 1
		elif ar_val != src:
			stats["added"] += 1
		else:
			stats["still_english"] += 1
		existing[src] = ar_val

	if write:
		_write_csv(ar_path, existing)
		frappe.clear_cache()

	stats["ar_total"] = len(existing)
	stats["ar_path"] = str(ar_path)
	return stats


def inject_desk_i18n_boot(bootinfo) -> None:
	lang = (bootinfo.get("lang") or frappe.local.lang or "en").lower()
	if not lang.startswith("ar"):
		return
	messages = bootinfo.get("__messages") or {}
	if not isinstance(messages, dict):
		messages = {}
	else:
		messages = dict(messages)
	from omnexa_core.omnexa_core.i18n.desk_translation_catalog import build_global_desk_messages

	messages.update(build_global_desk_messages(lang))
	bootinfo["__messages"] = messages


def execute():
	stats = sync_desk_translations(write=True)
	print(
		f"Desk i18n: {stats['ar_total']} AR rows, "
		f"{stats['added']} workspace labels translated, "
		f"{stats['still_english']} still English"
	)
