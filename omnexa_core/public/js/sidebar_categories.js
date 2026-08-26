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

	function resolveSectorDef(itemTitle, sectorByWs, sectorParents) {
		if (sectorByWs[itemTitle]) {
			return { def: sectorByWs[itemTitle], sectorKey: itemTitle };
		}
		for (const wsName of Object.keys(sectorByWs)) {
			const def = sectorByWs[wsName];
			if (
				sectorParents.has(wsName) &&
				(def.sidebar_label === itemTitle || def.label_full === itemTitle)
			) {
				return { def, sectorKey: wsName };
			}
		}
		if (sectorParents.has(itemTitle)) {
			return { def: { sidebar_label: itemTitle, label_ar: itemTitle }, sectorKey: itemTitle };
		}
		return null;
	}

	function toggleSectorChildren(container, childContainer, collapsed, sectorKey) {
		const hidden = childContainer.classList.toggle("hidden");
		container.classList.toggle("omnexa-sector-collapsed", hidden);
		collapsed[sectorKey] = hidden;
		saveCollapsedState(collapsed);
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
			const resolved = resolveSectorDef(itemTitle, sectorByWs, sectorParents);
			if (!resolved) {
				return;
			}

			const { def, sectorKey } = resolved;
			const shown = displayLabel(def);
			const fullName = def.label_full || sectorKey;
			if (shown) {
				labelEl.textContent = shown;
			}
			labelEl.setAttribute("title", fullName);

			container.classList.add("omnexa-sector-parent");
			container.dataset.sectorParent = sectorKey;

			const childContainer = container.querySelector(".sidebar-child-item");
			if (!childContainer) {
				return;
			}

			if (collapsed[sectorKey] === true) {
				childContainer.classList.add("hidden");
				container.classList.add("omnexa-sector-collapsed");
			}

			const header = container.querySelector(".standard-sidebar-item");
			const anchor = header && header.querySelector("a.item-anchor");
			if (anchor && window.frappe && frappe.router && sectorKey) {
				anchor.setAttribute("href", `/app/${frappe.router.slug(sectorKey)}`);
				anchor.setAttribute("title", fullName);
			}

			const onSectorToggle = (e) => {
				if (e.target.closest(".sidebar-item-control")) {
					return;
				}
				e.preventDefault();
				e.stopPropagation();
				toggleSectorChildren(container, childContainer, collapsed, sectorKey);
			};

			if (header && !header.dataset.sectorToggleBound) {
				header.dataset.sectorToggleBound = "1";
				header.style.cursor = "pointer";
				header.addEventListener("click", onSectorToggle);
			}
			if (anchor && !anchor.dataset.sectorToggleBound) {
				anchor.dataset.sectorToggleBound = "1";
				anchor.addEventListener("click", onSectorToggle);
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
