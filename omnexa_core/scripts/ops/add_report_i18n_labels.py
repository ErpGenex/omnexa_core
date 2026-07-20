#!/usr/bin/env python3
"""Wrap Script Report column labels with _() for bilingual Desk/print."""

from __future__ import annotations

import ast
import re
from pathlib import Path


def _find_bench_root() -> Path:
	p = Path(__file__).resolve().parent
	for _ in range(12):
		if (p / "sites" / "apps.txt").is_file():
			return p
		if p.parent == p:
			break
		p = p.parent
	raise SystemExit("Cannot find frappe-bench root")


BENCH = _find_bench_root()
LABEL_RE = re.compile(r'("label"\s*:\s*)("(?:[^"\\]|\\.)*")(\s*[}])')


def _ensure_import(text: str) -> str:
	if "from frappe import _" not in text:
		if "import frappe\n" in text:
			return text.replace("import frappe\n", "import frappe\nfrom frappe import _\n", 1)
		return "from frappe import _\n\n" + text
	return text


def _wrap_labels_in_columns(text: str) -> tuple[str, bool]:
	changed = False

	def repl(m: re.Match) -> str:
		nonlocal changed
		prefix, literal, suffix = m.group(1), m.group(2), m.group(3)
		try:
			val = ast.literal_eval(literal)
		except Exception:
			return m.group(0)
		if not isinstance(val, str) or not val.strip():
			return m.group(0)
		chunk = text[max(0, m.start() - 8) : m.start()]
		if chunk.endswith("_("):
			return m.group(0)
		changed = True
		escaped = val.replace("\\", "\\\\").replace('"', '\\"')
		return f'{prefix}_("{escaped}"){suffix}'

	new_text = LABEL_RE.sub(repl, text)
	return new_text, changed


def patch_file(py_path: Path) -> bool:
	text = py_path.read_text(encoding="utf-8")
	if "def execute" not in text or "_(" in text:
		return False
	new_text, changed = _wrap_labels_in_columns(text)
	if not changed:
		return False
	new_text = _ensure_import(new_text)
	py_path.write_text(new_text, encoding="utf-8")
	return True


def main():
	patched = 0
	for app_dir in sorted((BENCH / "apps").iterdir()):
		if not app_dir.is_dir():
			continue
		if not (app_dir.name.startswith("omnexa_") or app_dir.name.startswith("erpgenex_")):
			continue
		for py in app_dir.rglob("report/*/*.py"):
			if patch_file(py):
				patched += 1
				print("patched", py.relative_to(BENCH))
	print("total patched", patched)


if __name__ == "__main__":
	main()
