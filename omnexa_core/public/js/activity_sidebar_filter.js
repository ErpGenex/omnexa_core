// Hide desk sidebar workspaces outside company business activity (explicit denylist only).
(function () {
	"use strict";

	function filterState() {
		return (frappe.boot && frappe.boot.omnexa_activity_filter) || {};
	}

	function shouldFilter() {
		const f = filterState();
		if (f.activity_menu_scope === "all") return false;
		return Boolean(f.active);
	}

	function deniedWorkspaceKeys() {
		const raw = (frappe.boot.omnexa_denied_workspace_keys || []).map(String);
		const set = new Set(raw);
		for (const key of raw) {
			const bare = stripLeadingEmoji(key);
			if (bare) set.add(bare);
		}
		const f = filterState();
		const act = String(f.company_activity || "");
		if (f.active && act && act !== "Financial Services") {
			const platform = new Set((frappe.boot.omnexa_platform_workspace_keys || []).map(String));
			for (const key of frappe.boot.omnexa_finance_workspace_keys || []) {
				const s = String(key);
				if (platform.has(s)) continue;
				set.add(s);
				const bare = stripLeadingEmoji(s);
				if (bare) set.add(bare);
			}
		}
		return set;
	}

	function stripLeadingEmoji(value) {
		return String(value || "")
			.replace(
				/^(?:[\u{1F300}-\u{1FAFF}\u{2700}-\u{27BF}\u{1F1E0}-\u{1F1FF}][\u{FE0F}\u{200D}]?)+\s*/u,
				""
			)
			.trim();
	}

	function sectorParents() {
		return new Set((frappe.boot.omnexa_sector_parents || []).map(String));
	}

	function hideContainer($container) {
		$container.addClass("omnexa-activity-hidden").attr("hidden", "hidden").hide();
	}

	function isDenied(itemName, denied) {
		if (!itemName) return false;
		if (denied.has(itemName)) return true;
		const bare = stripLeadingEmoji(itemName);
		if (bare && bare !== itemName && denied.has(bare)) return true;
		return false;
	}

	function applySidebarFilter() {
		if (!shouldFilter()) {
			$(".sidebar-item-container.omnexa-activity-hidden")
				.removeClass("omnexa-activity-hidden")
				.removeAttr("hidden")
				.show();
			return;
		}

		const denied = deniedWorkspaceKeys();
		const sectors = sectorParents();

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
			// Desk rebuilds the sidebar asynchronously after boot — re-apply a few times.
			[150, 400, 1000].forEach((ms) => setTimeout(applySidebarFilter, ms));
		});
	}

	init();
})();
