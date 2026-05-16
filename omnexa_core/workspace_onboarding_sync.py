# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt
"""Create ERPGENEX Module Onboarding + Onboarding Steps and wire Workspace content blocks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import frappe
from frappe.utils import cint

DOCS_URL = "https://frappe.io/framework"
ONBOARDING_PREFIX = "ERPGENEX — "


def onboarding_name_for(workspace_label: str) -> str:
	return f"{ONBOARDING_PREFIX}{workspace_label}"


def _is_public_workspace(ws) -> bool:
	return cint(ws.public) == 1 and not (getattr(ws, "for_user", None) or "").strip()


def _ensure_onboarding_step(name: str, fields: dict[str, Any]) -> None:
	if frappe.db.exists("Onboarding Step", name):
		doc = frappe.get_doc("Onboarding Step", name)
		for k, v in fields.items():
			setattr(doc, k, v)
		doc.save(ignore_permissions=True)
	else:
		doc = frappe.get_doc({"doctype": "Onboarding Step", "name": name, **fields})
		doc.insert(ignore_permissions=True)


def _report_meta(report_name: str) -> dict | None:
	if not frappe.db.exists("Report", report_name):
		return None
	return frappe.db.get_value(
		"Report",
		report_name,
		["report_type", "ref_doctype"],
		as_dict=True,
	)


def _commerce_step_specs() -> list[dict[str, Any]]:
	specs: list[dict[str, Any]] = [
		{
			"name": "ERPGENEX-COMM-01-Catalog-Item",
			"title": "Publish a catalog item",
			"action": "Create Entry",
			"reference_document": "Catalog Item",
			"action_label": "Create catalog item",
			"show_full_form": 1,
			"description": "Define what you sell or book: SKU, pricing, and availability for web orders and bookings.",
		},
		{
			"name": "ERPGENEX-COMM-02-Web-Order",
			"title": "Capture a web order",
			"action": "Create Entry",
			"reference_document": "Web Order",
			"action_label": "New web order",
			"show_full_form": 1,
			"description": "Run order-to-cash: customer, lines, channel, and status through invoicing and fulfilment.",
		},
		{
			"name": "ERPGENEX-COMM-03-Booking",
			"title": "Schedule a booking",
			"action": "Create Entry",
			"reference_document": "Booking",
			"action_label": "New booking",
			"show_full_form": 1,
			"description": "Reserve capacity against bookable resources without double-booking.",
		},
		{
			"name": "ERPGENEX-COMM-04-Payment-Intent",
			"title": "Record a payment intent",
			"action": "Create Entry",
			"reference_document": "Payment Intent",
			"action_label": "New payment intent",
			"show_full_form": 1,
			"description": "Track initiation, confirmation, capture, refund, and reconciliation outcomes.",
		},
	]
	meta = _report_meta("Commerce Order-to-Cash Pipeline")
	if meta:
		specs.append(
			{
				"name": "ERPGENEX-COMM-05-O2C-Report",
				"title": "Review order-to-cash pipeline",
				"action": "View Report",
				"reference_report": "Commerce Order-to-Cash Pipeline",
				"report_type": meta.get("report_type"),
				"report_reference_doctype": meta.get("ref_doctype") or "Web Order",
				"report_description": "Slice web orders by segment, branch, and status for order-to-cash visibility.",
				"action_label": "Open report",
			}
		)
	return specs


def _shortcut_to_step_spec(shortcut, idx: int, ws_name: str) -> dict[str, Any] | None:
	st = (shortcut.type or "").strip()
	link = (shortcut.link_to or "").strip()
	label = (shortcut.label or link or f"Step {idx}").strip()
	slug = frappe.scrub(ws_name)[:40]
	base = f"ERPGENEX-WS-{slug}-{idx:02d}"

	if st == "DocType" and link:
		return {
			"name": f"{base}-{frappe.scrub(link)}",
			"title": f"Get started with {link}",
			"action": "Create Entry",
			"reference_document": link,
			"action_label": "Create",
			"show_full_form": 0,
			"description": f"Create or review your first **{link}** record from this workspace.",
		}
	if st == "Report" and link:
		meta = _report_meta(link)
		if not meta:
			return None
		return {
			"name": f"{base}-report-{frappe.scrub(link)}",
			"title": f"Open report {link}",
			"action": "View Report",
			"reference_report": link,
			"report_type": meta.get("report_type"),
			"report_reference_doctype": meta.get("ref_doctype") or "",
			"report_description": f"Operational follow-up using **{link}**.",
			"action_label": "Open report",
		}
	if st == "Page" and link:
		return {
			"name": f"{base}-page-{frappe.scrub(link)}",
			"title": f"Open {label}",
			"action": "Go to Page",
			"path": link,
			"action_label": "Open",
			"description": f"Jump to the **{label}** page.",
		}
	return None


def _generic_step_specs(ws) -> list[dict[str, Any]]:
	out: list[dict[str, Any]] = []
	idx = 1
	for row in ws.shortcuts or []:
		if len(out) >= 4:
			break
		spec = _shortcut_to_step_spec(row, idx, ws.name)
		if spec:
			out.append(spec)
			idx += 1
	title = ws.title or ws.label
	path = f"Workspaces/{title}"
	out.append(
		{
			"name": f"ERPGENEX-WS-{frappe.scrub(ws.name)}-home",
			"title": "Explore this workspace",
			"action": "Go to Page",
			"path": path,
			"action_label": "Open workspace",
			"description": f"Return here for shortcuts, charts, and lists for **{title}**.",
		}
	)
	return out


def _upsert_module_onboarding(ws, specs: list[dict[str, Any]]) -> str:
	for spec in specs:
		nm = spec["name"]
		body = {k: v for k, v in spec.items() if k != "name"}
		_ensure_onboarding_step(nm, body)

	mo_name = onboarding_name_for(ws.label)
	if frappe.db.exists("Module Onboarding", mo_name):
		mo = frappe.get_doc("Module Onboarding", mo_name)
	else:
		mo = frappe.new_doc("Module Onboarding")
		mo.name = mo_name

	mo.module = ws.module
	# Sidebar already shows branding; onboarding title mirrors the workspace (no EG / duplicate prefix).
	mo.title = ws.label or ws.title or ws.name
	mo.subtitle = frappe._("Guided setup for this workspace.")
	mo.success_message = f"You are ready to work in {ws.label}."
	mo.documentation_url = DOCS_URL
	mo.is_complete = 0
	mo.set("steps", [])
	for spec in specs:
		mo.append("steps", {"step": spec["name"]})

	mo.set("allow_roles", [])
	for role in ("Desk User", "System Manager"):
		mo.append("allow_roles", {"role": role})

	mo.save(ignore_permissions=True)
	return mo_name


def ensure_workspace_module_onboarding(ws) -> str | None:
	"""Create/update Module Onboarding for an in-memory or saved Workspace doc (uses current shortcuts/links)."""
	if not ws.module or not _is_public_workspace(ws) or cint(getattr(ws, "is_hidden", 0)):
		return None

	if ws.name == "Commerce" and frappe.db.exists("DocType", "Catalog Item"):
		specs = _commerce_step_specs()
	else:
		specs = _generic_step_specs(ws)

	if not specs:
		return None

	return _upsert_module_onboarding(ws, specs)


def ensure_module_onboarding_doc(ws_name: str) -> str | None:
	ws = frappe.get_doc("Workspace", ws_name)
	return ensure_workspace_module_onboarding(ws)


def prepend_onboarding_block(content_json: str | None, mo_name: str) -> str:
	arr = json.loads(content_json or "[]")
	filtered = [x for x in arr if x.get("type") != "onboarding"]
	block = {
		"id": "erpgenex-onboarding",
		"type": "onboarding",
		"data": {"onboarding_name": mo_name, "col": 12},
	}
	return json.dumps([block] + filtered, ensure_ascii=False)


def sync_workspace_database() -> int:
	n = 0
	for row in frappe.get_all("Workspace", fields=["name"], order_by="name asc"):
		try:
			mo_name = ensure_module_onboarding_doc(row.name)
		except Exception:
			frappe.log_error(title=f"ERPGENEX onboarding: Workspace {row.name}", message=frappe.get_traceback())
			continue
		if not mo_name:
			continue
		ws = frappe.get_doc("Workspace", row.name)
		new_content = prepend_onboarding_block(ws.content, mo_name)
		if new_content != (ws.content or ""):
			frappe.db.set_value("Workspace", row.name, "content", new_content)
			n += 1
	frappe.db.commit()
	return n


def _iter_workspace_json_files() -> list[Path]:
	from frappe.utils import get_bench_path

	out: list[Path] = []
	bench = Path(get_bench_path()) / "apps"
	if not bench.is_dir():
		return out
	for app_dir in bench.iterdir():
		if not app_dir.is_dir() or app_dir.name in ("frappe", "node_modules"):
			continue
		for j in app_dir.rglob("workspace/**/*.json"):
			if j.is_file():
				out.append(j)
	return out


def sync_workspace_json_files() -> int:
	updated = 0
	for path in _iter_workspace_json_files():
		try:
			raw = path.read_text(encoding="utf-8")
			data = json.loads(raw)
		except (OSError, json.JSONDecodeError):
			continue
		if data.get("doctype") != "Workspace":
			continue
		label = data.get("label") or data.get("name")
		if not label:
			continue
		if not data.get("module"):
			continue
		if not int(data.get("public") or 0):
			continue
		if int(data.get("is_hidden") or 0):
			continue
		if (data.get("for_user") or "").strip():
			continue

		mo_name = onboarding_name_for(label)
		try:
			new_content = prepend_onboarding_block(data.get("content"), mo_name)
		except (json.JSONDecodeError, TypeError):
			continue
		if new_content == (data.get("content") or ""):
			continue
		data["content"] = new_content
		path.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
		updated += 1
	return updated


def enable_onboarding_setting() -> None:
	frappe.db.set_single_value("System Settings", "enable_onboarding", 1)
	frappe.db.commit()


def run_full_sync() -> dict[str, int]:
	enable_onboarding_setting()
	db_n = sync_workspace_database()
	json_n = sync_workspace_json_files()
	return {"workspace_rows_updated": db_n, "workspace_json_files_updated": json_n}
