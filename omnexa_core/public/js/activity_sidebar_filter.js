// Hide desk sidebar workspaces outside company business activity (explicit denylist only).
(function () {
	"use strict";

	function filterState() {
		return (frappe.boot && frappe.boot.omnexa_activity_filter) || {};
	}

	function shouldFilter() {
		const f = filterState();
		if (f.activity_menu_scope === "all") return false;
		if (!f.active) return false;
		return Boolean((frappe.boot.omnexa_denied_workspace_keys || []).length);
	}

	function deniedWorkspaceKeys() {
		return new Set((frappe.boot.omnexa_denied_workspace_keys || []).map(String));
	}

	function sectorParents() {
		return new Set((frappe.boot.omnexa_sector_parents || []).map(String));
	}

	function hideContainer($container) {
		$container.addClass("omnexa-activity-hidden").attr("hidden", "hidden").hide();
	}

	function isDenied(itemName, denied) {
		return Boolean(itemName && denied.has(itemName));
	}

	function applySidebarFilter() {
		if (!shouldFilter()) {
			$(".sidebar-item-container.omnexa-activity-hidden").removeClass("omnexa-activity-hidden").removeAttr("hidden").show();
			return;
		}

		const denied = deniedWorkspaceKeys();
		const sectors = sectorParents();
		if (!denied.size) return;

		const $sidebar = $(".desk-sidebar");
		if (!$sidebar.length) return;

		$sidebar.find(".sidebar-item-container").each(function () {
			const $container = $(this);
			const itemName = ($container.attr("item-name") || "").trim();
			if (!itemName) return;

			if (sectors.has(itemName)) {
				const $children = $container.find(".sidebar-child-item .sidebar-item-container");
				let visibleChild = 0;
				$children.each(function () {
					const childName = ($(this).attr("item-name") || "").trim();
					if (childName && !isDenied(childName, denied)) visibleChild += 1;
				});
				if (visibleChild === 0) hideContainer($container);
				else $container.removeClass("omnexa-activity-hidden").removeAttr("hidden").show();
				return;
			}

			if (isDenied(itemName, denied)) hideContainer($container);
			else $container.removeClass("omnexa-activity-hidden").removeAttr("hidden").show();
		});
	}

	function init() {
		if (!window.frappe) return;
		frappe.ready(() => {
			applySidebarFilter();
			$(document).on("workspace_sidebar_updated page-change route-change", () => {
				setTimeout(applySidebarFilter, 50);
			});
		});
	}

	init();
})();
