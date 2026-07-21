/* global frappe */
/**
 * ERPGENEX Sector Sidebar — short labels and icons for sector group headers.
 */
(function () {
	"use strict";

	const STORAGE_KEY = "omnexa_sector_collapsed";

	function getSectorParents() {
		return (frappe.boot && frappe.boot.omnexa_sector_parents) || [];
	}

	function getSectorByWorkspace() {
		return (frappe.boot && frappe.boot.omnexa_sector_by_workspace) || {};
	}

	function loadCollapsedState() {
		try {
			return JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
		} catch (e) {
			return {};
		}
	}

	function saveCollapsedState(state) {
		try {
			localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
		} catch (e) {
			/* ignore */
		}
	}

	function displayLabel(def) {
		if (!def) {
			return "";
		}
		const lang = (frappe.boot && frappe.boot.lang) || "en";
		if (String(lang).toLowerCase().startsWith("ar") && def.label_ar) {
			return def.label_ar;
		}
		return def.sidebar_label || def.label || "";
	}

	function enhanceSectorParents() {
		const sidebar = document.querySelector(".desk-sidebar");
		if (!sidebar) {
			return;
		}

		const sectorParents = new Set(getSectorParents());
		const sectorByWs = getSectorByWorkspace();
		const collapsed = loadCollapsedState();

		sidebar.querySelectorAll(".sidebar-item-container").forEach((container) => {
			const labelEl = container.querySelector(".sidebar-item-label");
			if (!labelEl) {
				return;
			}

			const itemTitle = (container.getAttribute("item-name") || labelEl.textContent || "").trim();
			if (!sectorParents.has(itemTitle)) {
				return;
			}

			let def = null;
			for (const wsName of Object.keys(sectorByWs)) {
				if (sectorByWs[wsName].sidebar_label === itemTitle) {
					def = sectorByWs[wsName];
					break;
				}
			}

			const shown = displayLabel(
				def || { sidebar_label: itemTitle, label_ar: itemTitle }
			);
			if (shown) {
				labelEl.textContent = shown;
			}

			container.classList.add("omnexa-sector-parent");
			container.dataset.sectorParent = itemTitle;

			const childContainer = container.querySelector(".sidebar-child-item");
			if (!childContainer) {
				return;
			}

			const sectorKey = itemTitle;
			if (collapsed[sectorKey] === true) {
				childContainer.classList.add("hidden");
				container.classList.add("omnexa-sector-collapsed");
			}

			const header = container.querySelector(".standard-sidebar-item");
			if (header && !header.dataset.sectorToggleBound) {
				header.dataset.sectorToggleBound = "1";
				header.style.cursor = "pointer";
				header.addEventListener("click", (e) => {
					if (e.target.closest(".sidebar-item-control")) {
						return;
					}
					const hidden = childContainer.classList.toggle("hidden");
					container.classList.toggle("omnexa-sector-collapsed", hidden);
					collapsed[sectorKey] = hidden;
					saveCollapsedState(collapsed);
				});
			}
		});
	}

	function scheduleEnhance() {
		window.requestAnimationFrame(() => {
			setTimeout(enhanceSectorParents, 120);
		});
	}

	if (window.frappe) {
		frappe.ready(scheduleEnhance);
	} else {
		window.addEventListener("load", scheduleEnhance);
	}

	$(document).on("page-change workspace_sidebar_updated route-change", scheduleEnhance);
})();
