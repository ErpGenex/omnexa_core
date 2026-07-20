# Copyright (c) 2026, Omnexa and contributors
# License: MIT
"""omnexa_core gap register — platform leader checklist (48 items)."""

from __future__ import annotations

import os

import frappe
from frappe.utils import get_bench_path

GLOBAL_LEADER_TARGET = 4.85
GAPS_TOTAL = 48
APP = "omnexa_core"

GAP_DEFINITIONS: list[dict] = [
	{"id": "CORE-001", "domain": "integration", "title": "Global benchmark module", "wave": 1, "detect": "module:core_global_benchmark"
	},
	{"id": "CORE-002", "domain": "integration", "title": "Gap register", "wave": 1, "detect": "module:core_gap_register"
	},
	{"id": "CORE-003", "domain": "integration", "title": "App hooks registered", "wave": 1, "detect": "file:hooks.py"
	},
	{"id": "CORE-004", "domain": "integration", "title": "Assessment export", "wave": 1, "detect": "module:core_assessment"
	},
	{"id": "CORE-005", "domain": "portfolio", "title": "Branch master", "wave": 1, "detect": "doctype:Branch"
	},
	{"id": "CORE-006", "domain": "portfolio", "title": "User Branch Access", "wave": 1, "detect": "doctype:User Branch Access"
	},
	{"id": "CORE-007", "domain": "portfolio", "title": "Event Audit Log", "wave": 1, "detect": "doctype:Event Audit Log"
	},
	{"id": "CORE-008", "domain": "portfolio", "title": "Marketplace settings", "wave": 1, "detect": "doctype:Omnexa Marketplace Settings"
	},
	{"id": "CORE-009", "domain": "reporting", "title": "Query report link titles", "wave": 1, "detect": "module:omnexa_core.report_link_titles"
	},
	{"id": "CORE-010", "domain": "analytics", "title": "Ops weekly health", "wave": 1, "detect": "api:omnexa_core.omnexa_core.ops_weekly_health.collect_ops_health"
	},
	{"id": "CORE-011", "domain": "analytics", "title": "Platform portfolio gate", "wave": 1, "detect": "module:omnexa_core.platform_portfolio_gate"
	},
	{"id": "CORE-012", "domain": "analytics", "title": "Platform health API", "wave": 1, "detect": "api:omnexa_core.omnexa_core.platform_health_api.get_platform_health"
	},
	{"id": "CORE-013", "domain": "digital", "title": "ERPGenex Marketplace page", "wave": 1, "detect": "file:omnexa_core/page/erpgenex_marketplace/erpgenex_marketplace.json"
	},
	{"id": "CORE-014", "domain": "digital", "title": "Platform API surface", "wave": 1, "detect": "module:omnexa_core.platform_api"
	},
	{"id": "CORE-015", "domain": "bi", "title": "KPI preview bridge", "wave": 1, "detect": "api:omnexa_core.omnexa_core.parity_api.preview_infra_kpi"
	},
	{"id": "CORE-016", "domain": "operations", "title": "Event dispatcher scheduler", "wave": 1, "detect": "file:hooks.py"
	},
	{"id": "CORE-017", "domain": "security", "title": "License gate before_request", "wave": 1, "detect": "module:omnexa_core.license_gate"
	},
	{"id": "CORE-018", "domain": "security", "title": "MFA gate", "wave": 1, "detect": "module:omnexa_core.omnexa_mfa_gate"
	},
	{"id": "CORE-019", "domain": "security", "title": "Compliance guard", "wave": 1, "detect": "module:omnexa_core.compliance_guard"
	},
	{"id": "CORE-020", "domain": "security", "title": "Branch access enforcement", "wave": 1, "detect": "module:omnexa_core.branch_access"
	},
	{"id": "CORE-021", "domain": "security", "title": "Structured logging", "wave": 1, "detect": "module:omnexa_core.structured_logging"
	},
	{"id": "CORE-022", "domain": "security", "title": "Report performance metrics", "wave": 1, "detect": "module:omnexa_core.report_perf"
	},
	{"id": "CORE-023", "domain": "compliance", "title": "SAP parity platform test", "wave": 1, "detect": "file:tests/test_sap_parity_platform.py"
	},
	{"id": "CORE-024", "domain": "compliance", "title": "DocType event registry", "wave": 1, "detect": "module:omnexa_core.doctype_event_registry"
	},
	{"id": "CORE-025", "domain": "compliance", "title": "Feature flags", "wave": 1, "detect": "module:omnexa_core.feature_flags"
	},
	{"id": "CORE-026", "domain": "compliance", "title": "AI governance module", "wave": 1, "detect": "module:omnexa_core.ai_governance"
	},
	{"id": "CORE-027", "domain": "compliance", "title": "Global certificates sync", "wave": 1, "detect": "module:omnexa_core.global_certificates_sync"
	},
	{"id": "CORE-028", "domain": "compliance", "title": "Install constants refactor", "wave": 1, "detect": "module:omnexa_core.install_pkg.constants"
	},
	{"id": "CORE-029", "domain": "compliance", "title": "Session boot shim", "wave": 1, "detect": "module:session_boot"
	},
	{"id": "CORE-030", "domain": "compliance", "title": "Marketplace module", "wave": 1, "detect": "module:omnexa_core.marketplace"
	},
	{"id": "CORE-031", "domain": "compliance", "title": "Integration hub", "wave": 1, "detect": "module:omnexa_core.integration_hub"
	},
	{"id": "CORE-032", "domain": "compliance", "title": "Localization module", "wave": 1, "detect": "module:omnexa_core.localization"
	},
	{"id": "CORE-033", "domain": "compliance", "title": "Permissions module", "wave": 1, "detect": "module:omnexa_core.permissions"
	},
	{"id": "CORE-034", "domain": "compliance", "title": "User context defaults", "wave": 1, "detect": "module:omnexa_core.user_context"
	},
	{"id": "CORE-035", "domain": "compliance", "title": "Core global benchmark test", "wave": 1, "detect": "file:tests/test_core_global_benchmark.py"
	},
	{"id": "CORE-036", "domain": "compliance", "title": "MFA gate test", "wave": 1, "detect": "file:tests/test_omnexa_mfa_gate.py"
	},
	{"id": "CORE-037", "domain": "compliance", "title": "Finance control center page", "wave": 1, "detect": "file:omnexa_core/page/finance_control_center/finance_control_center.json"
	},
	{"id": "CORE-038", "domain": "compliance", "title": "Inventory control center page", "wave": 1, "detect": "file:omnexa_core/page/inventory_control_center/inventory_control_center.json"
	},
	{"id": "CORE-039", "domain": "compliance", "title": "ERPGenex scheduler", "wave": 1, "detect": "module:erpgenex_scheduler"
	},
	{"id": "CORE-040", "domain": "compliance", "title": "Ops load smoke", "wave": 1, "detect": "module:omnexa_core.ops_load_smoke"
	},
	{"id": "CORE-041", "domain": "compliance", "title": "GRC parity", "wave": 1, "detect": "module:omnexa_core.grc_parity"
	},
	{"id": "CORE-042", "domain": "compliance", "title": "Infra parity", "wave": 1, "detect": "module:omnexa_core.infra_parity"
	},
	{"id": "CORE-043", "domain": "compliance", "title": "App visibility", "wave": 1, "detect": "module:omnexa_core.app_visibility"
	},
	{"id": "CORE-044", "domain": "compliance", "title": "Vertical workspace catalog", "wave": 1, "detect": "module:omnexa_core.vertical_workspace_catalog"
	},
	{"id": "CORE-045", "domain": "compliance", "title": "List view unifier", "wave": 1, "detect": "module:omnexa_core.listview_unifier"
	},
	{"id": "CORE-046", "domain": "compliance", "title": "Export enhancements JS", "wave": 1, "detect": "file:public/js/query_report_export_enhancements.js"
	},
	{"id": "CORE-047", "domain": "compliance", "title": "Core ERP readiness", "wave": 1, "detect": "module:core_erp_readiness"
	},
	{"id": "CORE-048", "domain": "compliance", "title": "Global benchmark closed gate", "wave": 1, "detect": "module:core_global_benchmark"
	},
]


def _detect_gap(gap: dict) -> bool:
	detect = gap.get("detect")
	if not detect:
		return False
	try:
		if detect.startswith("doctype:"):
			return bool(frappe.db.exists("DocType", detect.split(":", 1)[1]))
		if detect.startswith("page:"):
			return bool(frappe.db.exists("Page", detect.split(":", 1)[1]))
		if detect.startswith("report:"):
			return bool(frappe.db.exists("Report", detect.split(":", 1)[1]))
		if detect.startswith("api:"):
			return bool(frappe.get_attr(detect.split(":", 1)[1]))
		if detect.startswith("module:"):
			target = detect.split(":", 1)[1]
			if "." in target and not target.startswith(APP):
				return bool(frappe.get_module(target))
			return bool(frappe.get_module(f"{APP}.{target}"))
		if detect.startswith("file:"):
			rel = detect.split(":", 1)[1]
			root = os.path.join(get_bench_path(), "apps", APP, APP)
			return os.path.isfile(os.path.join(root, rel))
	except Exception:
		return False
	return False


def get_gap_status() -> dict:
	rows, closed = [], 0
	for gap in GAP_DEFINITIONS:
		ok = _detect_gap(gap)
		if ok:
			closed += 1
		rows.append({**gap, "status": "closed" if ok else "open"
	})
	return {
		"version": "2026.06.25",
		"target_score": GLOBAL_LEADER_TARGET,
		"gaps_total": GAPS_TOTAL,
		"gaps_closed": closed,
		"gaps_open": GAPS_TOTAL - closed,
		"global_leader_gate": closed >= GAPS_TOTAL,
		"gaps": rows,
		"app": APP
	}
