#!/usr/bin/env python3
"""Deploy categorized ERPGENEX print HTML templates to all report folders."""

from __future__ import annotations

import json
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(BENCH / "apps" / "omnexa_core"))

from omnexa_core.omnexa_core.report_print.report_print_categories import (  # noqa: E402
	report_print_category,
	template_filename,
)

TEMPLATE_DIR = BENCH / "apps" / "omnexa_core/omnexa_core/omnexa_core/report_print/templates"


def main(force: bool = False) -> None:
	written = skipped = 0
	for app_dir in sorted((BENCH / "apps").iterdir()):
		if not app_dir.is_dir():
			continue
		if not (app_dir.name.startswith("omnexa_") or app_dir.name.startswith("erpgenex_")):
			continue
		for json_path in app_dir.rglob("report/*/*.json"):
			try:
				doc = json.loads(json_path.read_text(encoding="utf-8"))
			except Exception:
				continue
			if doc.get("doctype") != "Report":
				continue
			report_name = doc.get("name") or json_path.stem
			category = report_print_category(report_name, doc.get("module"), doc.get("ref_doctype"))
			tpl_name = template_filename(category)
			content = (TEMPLATE_DIR / tpl_name).read_text(encoding="utf-8")
			slug = report_name.lower().replace(" ", "_").replace("(", "").replace(")", "")
			html_path = json_path.parent / f"{json_path.parent.name}.html"
			if not html_path.name.endswith(".html"):
				html_path = json_path.with_suffix(".html")
			# Frappe scrub naming
			import re

			slug = re.sub(r"[^\w\s-]", "", report_name).strip().lower().replace(" ", "_")
			html_path = json_path.parent / f"{slug}.html"
			marker = f"erpg-{category[:3]}-print"
			if html_path.exists() and not force:
				if marker in html_path.read_text(encoding="utf-8"):
					skipped += 1
					continue
			html_path.write_text(content, encoding="utf-8")
			written += 1
	print(f"html_written={written} html_skipped={skipped}")


if __name__ == "__main__":
	main(force="--force" in sys.argv)
