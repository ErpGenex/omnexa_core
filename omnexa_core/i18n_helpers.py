# Copyright (c) 2026, ErpGenex and contributors
# License: MIT

"""Safe translated string formatting (handles broken CSV placeholders like ``{ 0 }``)."""

from __future__ import annotations

import re

from frappe import _


def format_msg(msg: str, *args) -> str:
	text = _(msg)
	if not args:
		return text
	text = re.sub(r"\{\s*(\d+)\s*\}", r"{\1}", text)
	try:
		return text.format(*args)
	except (KeyError, IndexError, ValueError):
		return f"{text} ({', '.join(str(a) for a in args)})"
