#!/usr/bin/env python3
"""Second pass: charts for _cols(), 6-tuple returns, and inline column reports."""
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


def _has_chart_return(text: str) -> bool:
	if re.search(r"return\s+[^;\n]+,\s*chart\b", text):
		return True
	if re.search(r"return\s+[^;\n]+,\s*None,\s*chart", text):
		return True
	if "governance_policy_chart" in text or "grouped_sum_chart" in text or "currency_bar_chart" in text:
		return True
	return False


def _patch_cols_tuple(text: str) -> str:
	"""return _cols(), data, msg, None, None, False -> inject chart at slot 4."""

	def repl(match: re.Match) -> str:
		indent, data_var, msg = match.group(1), match.group(2), match.group(3)
		return (
			f"\n{indent}columns = _cols()\n"
			f"{indent}chart = auto_chart_for_columns({data_var}, columns)\n"
			f"{indent}return columns, {data_var}, {msg}, chart, None, False"
		)

	return re.sub(
		r"\n(\t+)return _cols\(\), (data|rows), ([^,]+), None, None, False\s*$",
		repl,
		text,
		flags=re.MULTILINE,
	)


def _patch_cols_simple(text: str) -> str:
	def repl(match: re.Match) -> str:
		indent, var = match.group(1), match.group(2)
		return (
			f"\n{indent}columns = _cols()\n"
			f"{indent}chart = auto_chart_for_columns({var}, columns)\n"
			f"{indent}return columns, {var}, None, chart"
		)

	return re.sub(r"\n(\t+)return _cols\(\), (data|rows)\s*$", repl, text, flags=re.MULTILINE)


def _patch_inline_columns(text: str) -> str:
	"""return columns, data, None, None, None, False (chart slot empty)."""

	def repl(match: re.Match) -> str:
		indent, data_var = match.group(1), match.group(2)
		return (
			f"\n{indent}chart = auto_chart_for_columns({data_var}, columns)\n"
			f"{indent}return columns, {data_var}, None, chart, None, False"
		)

	return re.sub(
		r"\n(\t+)return columns, (data|rows), None, None, None, False\s*$",
		repl,
		text,
		flags=re.MULTILINE,
	)


def _patch_columns_msg_none(text: str) -> str:
	def repl(match: re.Match) -> str:
		indent, data_var, msg = match.group(1), match.group(2), match.group(3)
		return (
			f"\n{indent}chart = auto_chart_for_columns({data_var}, columns)\n"
			f"{indent}return columns, {data_var}, {msg}, chart"
		)

	return re.sub(
		r"\n(\t+)return columns, (data|rows), ([^,\n]+)\s*$",
		repl,
		text,
		flags=re.MULTILINE,
	)


def patch_file(path: Path) -> bool:
	if path.parent.name in SKIP_NAMES:
		return False
	text = path.read_text(encoding="utf-8")
	if "def execute" not in text:
		return False
	if "frappe.db.sql" not in text and "frappe.get_all" not in text and "frappe.db.count" not in text:
		return False
	if _has_chart_return(text):
		return False

	original = text
	text = _add_import(text)
	text = _patch_cols_tuple(text)
	text = _patch_cols_simple(text)
	text = _patch_inline_columns(text)
	text = _patch_columns_msg_none(text)

	if text == original:
		return False
	path.write_text(text, encoding="utf-8")
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
