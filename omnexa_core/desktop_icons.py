# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Desktop Icons Organization by Business Categories"""

from __future__ import annotations

import frappe
from frappe import _


def get_desktop_icons():
	"""
	Organize desktop icons by business categories.
	This hook is called by Frappe to get the desktop icons for the sidebar.
	"""
	from omnexa_core.omnexa_core.business_categories import (
		BUSINESS_CATEGORIES,
		get_installed_apps_in_category,
	)

	desktop_icons = []
	installed_apps = frappe.get_installed_apps()

	# Get sorted categories by order
	sorted_categories = sorted(
		BUSINESS_CATEGORIES.items(), key=lambda x: x[1]["order"]
	)

	for category_id, category_data in sorted_categories:
		# Get installed apps in this category
		category_apps = get_installed_apps_in_category(category_id)

		# Skip empty categories
		if not category_apps:
			continue

		# Add category header
		desktop_icons.append(
			{
				"type": "header",
				"label": category_data["label"],
				"purpose": category_data["purpose"]
	}
		)

		# Add apps in this category
		for app_name in category_apps:
			# Get app info
			app_info = get_app_info(app_name)
			if app_info:
				desktop_icons.append(app_info)

	return desktop_icons


def get_app_info(app_name: str) -> dict | None:
	"""Get desktop icon information for an app"""
	try:
		# Try to get app info from hooks
		app_hooks = frappe.get_hooks(app_name=app_name)
		if not app_hooks:
			return None

		# Get app name and description
		app_label = app_hooks.get("app_name", [app_name])[0]
		app_title = app_hooks.get("app_title", [app_label])[0]
		app_description = app_hooks.get("app_description", [""])[0]
		app_icon = app_hooks.get("app_icon", ["octicon octicon-file-directory"])[0]
		app_color = app_hooks.get("app_color", ["grey"])[0]
		app_route = app_hooks.get("home_page", ["/app"])[0]

		return {
			"type": "link",
			"label": app_title,
			"description": app_description,
			"icon": app_icon,
			"color": app_color,
			"route": app_route,
			"app_name": app_name
	}
	except Exception:
		# Fallback to basic app info
		return {
			"type": "link",
			"label": app_name.replace("_", " ").title(),
			"description": "",
			"icon": "octicon octicon-file-directory",
			"color": "grey",
			"route": "/app",
			"app_name": app_name
	}
