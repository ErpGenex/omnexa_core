# Copyright (c) 2026, ErpGenEx
"""Portal Factory — creates role portals from JSON configuration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import frappe

from omnexa_core.multi_portal.config_loader import ConfigLoader
from omnexa_core.multi_portal.dynamic_permission_engine import DynamicPermissionEngine


@dataclass
class PortalConfig:
	application_id: str
	role_id: str
	portal_id: str
	portal_name: str
	base_url: str
	theme: dict[str, str]


@dataclass
class Portal:
	config: PortalConfig
	sidebar: dict[str, Any]
	dashboard: dict[str, Any]
	permissions: dict[str, Any]
	workspace: dict[str, Any]
	widgets: dict[str, Any]
	navigation: dict[str, Any]


class DynamicSidebarBuilder:
	def build(self, role_config: dict[str, Any]) -> dict[str, Any]:
		sidebar_sections = []
		for section_config in role_config.get("sidebar", {}).get("sections", []):
			section = {"title": section_config["title"], "items": []}
			for item_config in section_config.get("items", []):
				section["items"].append(
					{
						"id": item_config["id"],
						"title": item_config["title"],
						"icon": item_config.get("icon", ""),
						"route": item_config["route"],
					}
				)
			sidebar_sections.append(section)
		return {"sections": sidebar_sections, "enabled": True, "collapsible": True}


class DynamicDashboardBuilder:
	def build(self, role_config: dict[str, Any]) -> dict[str, Any]:
		dashboard_config = role_config.get("dashboard", {})
		return {
			"kpis": self._build_kpis(dashboard_config.get("kpis", [])),
			"quick_actions": self._build_quick_actions(dashboard_config.get("quick_actions", [])),
			"widgets": self._build_widgets(dashboard_config.get("widgets", [])),
			"charts": self._build_charts(dashboard_config.get("charts", [])),
			"layout": "grid",
			"columns": 12,
		}

	def _build_kpis(self, kpis_config: list) -> list:
		kpis = []
		for kpi_config in kpis_config:
			kpis.append(
				{
					"id": kpi_config["id"],
					"title": kpi_config["title"],
					"value": self._calculate_kpi_value(kpi_config),
					"source": kpi_config.get("source"),
					"filter": kpi_config.get("filter"),
				}
			)
		return kpis

	def _build_quick_actions(self, actions_config: list) -> list:
		return [
			{
				"id": action_config["id"],
				"title": action_config["title"],
				"action": action_config["action"],
				"doctype": action_config.get("doctype"),
			}
			for action_config in actions_config
		]

	def _build_widgets(self, widgets_config: list) -> list:
		return [
			{
				"id": widget_config["id"],
				"title": widget_config["title"],
				"type": widget_config["type"],
				"source": widget_config.get("source"),
			}
			for widget_config in widgets_config
		]

	def _build_charts(self, charts_config: list) -> list:
		return [
			{
				"id": chart_config["id"],
				"title": chart_config["title"],
				"type": chart_config["type"],
				"source": chart_config.get("source"),
			}
			for chart_config in charts_config
		]

	def _calculate_kpi_value(self, kpi_config: dict[str, Any]) -> int | float:
		source = (kpi_config.get("source") or "").replace("_", " ").title()
		if not source or not frappe.db.exists("DocType", source):
			return 0
		try:
			filters: dict[str, Any] = {}
			company = frappe.defaults.get_user_default("Company")
			if company and frappe.get_meta(source).has_field("company"):
				filters["company"] = company
			kpi_filter = kpi_config.get("filter")
			if kpi_filter == "today" and frappe.get_meta(source).has_field("creation"):
				filters["creation"] = [">=", frappe.utils.today()]
			elif kpi_filter == "pending" and frappe.get_meta(source).has_field("status"):
				filters["status"] = ["in", ["Draft", "To Deliver", "To Bill", "Open"]]
			elif kpi_filter == "this_month" and frappe.get_meta(source).has_field("creation"):
				filters["creation"] = [
					"between",
					[frappe.utils.get_first_day(frappe.utils.today()), frappe.utils.get_last_day(frappe.utils.today())],
				]
			if kpi_config.get("value") == "count":
				return frappe.db.count(source, filters)
		except Exception:
			return 0
		return 0


class DynamicWorkspaceGenerator:
	def generate(self, role_config: dict[str, Any]) -> dict[str, Any]:
		return {
			"name": f"{role_config.get('role_name', 'Role')} Workspace",
			"description": f"Workspace for {role_config.get('role_name', 'Role')}",
			"links": self._generate_links(role_config),
			"shortcuts": self._generate_shortcuts(role_config),
			"charts": self._generate_charts(role_config),
		}

	def _generate_links(self, role_config: dict[str, Any]) -> list:
		links = []
		for section in role_config.get("sidebar", {}).get("sections", []):
			for item in section.get("items", []):
				links.append({"label": item["title"], "link_to": item["route"], "type": "Link"})
		return links

	def _generate_shortcuts(self, role_config: dict[str, Any]) -> list:
		shortcuts = []
		for action in role_config.get("dashboard", {}).get("quick_actions", []):
			if action.get("doctype"):
				shortcuts.append({"label": action["title"], "link_to": action["doctype"], "type": "DocType"})
		return shortcuts

	def _generate_charts(self, role_config: dict[str, Any]) -> list:
		return [
			{"chart_name": chart["id"], "label": chart["title"]}
			for chart in role_config.get("dashboard", {}).get("charts", [])
		]


class DynamicWidgetLoader:
	def load_widgets(self, role_config: dict[str, Any]) -> dict[str, Any]:
		widgets = {}
		for widget_config in role_config.get("dashboard", {}).get("widgets", []):
			widgets[widget_config["id"]] = {
				"title": widget_config["title"],
				"type": widget_config["type"],
				"source": widget_config.get("source"),
				"config": {},
			}
		return widgets


class PortalFactory:
	"""Creates complete portal instances from application + role configuration."""

	def __init__(self):
		self.config_loader = ConfigLoader()
		self.sidebar_builder = DynamicSidebarBuilder()
		self.dashboard_builder = DynamicDashboardBuilder()
		self.permission_engine = DynamicPermissionEngine()
		self.workspace_generator = DynamicWorkspaceGenerator()
		self.widget_loader = DynamicWidgetLoader()

	def create_portal(self, application_id: str, role_id: str) -> Portal:
		app_config = self.config_loader.load_application_config(application_id)
		role_config = self.config_loader.load_role_config(application_id, role_id)
		theme_config = self.config_loader.load_theme_config(application_id)
		portal_config_data = self._find_portal_config(app_config, role_id)
		portal_config = PortalConfig(
			application_id=application_id,
			role_id=role_id,
			portal_id=portal_config_data["portal_id"],
			portal_name=portal_config_data["portal_name"],
			base_url=app_config.get("base_url", f"/app/{application_id}"),
			theme=theme_config,
		)
		return Portal(
			config=portal_config,
			sidebar=self.sidebar_builder.build(role_config),
			dashboard=self.dashboard_builder.build(role_config),
			permissions=self.permission_engine.load_permissions(application_id, role_id),
			workspace=self.workspace_generator.generate(role_config),
			widgets=self.widget_loader.load_widgets(role_config),
			navigation=self._build_navigation(app_config),
		)

	def _find_portal_config(self, app_config: dict[str, Any], role_id: str) -> dict[str, Any]:
		for portal in app_config.get("portals", []):
			if portal.get("role") == role_id:
				return portal
		frappe.throw(f"Portal not found for role: {role_id}")

	def _build_navigation(self, app_config: dict[str, Any]) -> dict[str, Any]:
		return app_config.get(
			"navigation",
			{
				"sidebar": {"enabled": True, "collapsible": True, "position": "left"},
				"navbar": {
					"enabled": True,
					"position": "top",
					"search_enabled": True,
					"notifications_enabled": True,
					"user_menu_enabled": True,
				},
				"breadcrumb": {"enabled": True, "position": "top"},
			},
		)

	def get_available_applications(self) -> list[str]:
		from omnexa_core.multi_portal import VALID_APPLICATIONS

		installed = set(frappe.get_installed_apps() or [])
		from omnexa_core.multi_portal import APPLICATION_APP_MAP

		return [app_id for app_id in VALID_APPLICATIONS if APPLICATION_APP_MAP.get(app_id) in installed]

	def get_available_roles(self, application_id: str) -> list[str]:
		app_config = self.config_loader.load_application_config(application_id)
		return app_config.get("roles", [])
