#!/usr/bin/env python3
"""Attach auto_chart_for_columns to Omnexa Script Reports missing charts."""
from __future__ import annotations

import re
from pathlib import Path

IMPORT_LINE = "from omnexa_core.omnexa_core.utils.report_charts import auto_chart_for_columns\n"
SKIP_NAMES = {"governance_overview", "trial_balance", "income_statement", "balance_sheet"}


def _add_import(text: str) -> str:
	if "auto_chart_for_columns" in text:
		return text
	if "from omnexa_core.omnexa_core.utils.report_charts import" in text:
		return re.sub(
			r"(from omnexa_core\.omnexa_core\.utils\.report_charts import)([^\n]+)",
			lambda m: m.group(1) + m.group(2)
			if "auto_chart_for_columns" in m.group(2)
			else m.group(1) + m.group(2).rstrip() + ", auto_chart_for_columns",
			text,
			count=1,
		)
	anchor = "from frappe import _\n"
	if anchor in text:
		return text.replace(anchor, anchor + "\n" + IMPORT_LINE, 1)
	return text.replace("import frappe\n", "import frappe\n\n" + IMPORT_LINE, 1)


def _patch_returns(text: str) -> str:
	# return _columns(), data|rows  (not empty [])
	def repl_columns(match: re.Match) -> str:
		indent, var = match.group(1), match.group(2)
		return (
			f"\n{indent}columns = _columns()\n"
			f"{indent}chart = auto_chart_for_columns({var}, columns)\n"
			f"{indent}return columns, {var}, None, chart"
		)

	text = re.sub(r"\n(\t+)return _columns\(\), (data|rows)\s*$", repl_columns, text, flags=re.MULTILINE)

	def repl_existing(match: re.Match) -> str:
		indent, var = match.group(1), match.group(2)
		return (
			f"\n{indent}chart = auto_chart_for_columns({var}, columns)\n"
			f"{indent}return columns, {var}, None, chart"
		)

	text = re.sub(r"\n(\t+)return columns, (data|rows)\s*$", repl_existing, text, flags=re.MULTILINE)
	return text


def patch_file(path: Path) -> bool:
	if path.parent.name in SKIP_NAMES:
		return False
	text = path.read_text(encoding="utf-8")
	if "def execute" not in text:
		return False
	if "frappe.db.sql" not in text and "frappe.get_all" not in text:
		return False
	if re.search(r"return\s+[^;\n]+,\s*None,\s*chart", text):
		return False
	if "auto_chart_for_columns" in text and ", None, chart" in text:
		return False
	if not re.search(r"return _columns\(\), (data|rows)", text) and not re.search(
		r"return columns, (data|rows)\s*$", text, flags=re.MULTILINE
	):
		return False

	new_text = _add_import(text)
	new_text = _patch_returns(new_text)
	if new_text == text:
		return False
	path.write_text(new_text, encoding="utf-8")
	return True


def main() -> None:
	root = Path("/home/frappeuser/frappe-bench/apps")
	patched = 0
	for app_dir in sorted(root.glob("*")):
		if not app_dir.is_dir() or app_dir.name in ("frappe",):
			continue
		for report_py in app_dir.rglob("report/*/*.py"):
			if report_py.name == "__init__.py":
				continue
			if patch_file(report_py):
				patched += 1
				print(report_py)
	print(f"PATCHED {patched} reports")


if __name__ == "__main__":
	main()
