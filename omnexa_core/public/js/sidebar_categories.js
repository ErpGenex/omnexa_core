/* global frappe */
// Sidebar Business Categories - Render category headers and organize items

(function () {
	"use strict";

	function renderCategoryHeaders() {
		// Wait for sidebar to be ready
		if (document.readyState === "loading") {
			document.addEventListener("DOMContentLoaded", renderCategoryHeaders);
			return;
		}

		// Find the sidebar container
		const sidebar = document.querySelector(".sidebar-menu") || document.querySelector(".desk-sidebar");
		if (!sidebar) {
			setTimeout(renderCategoryHeaders, 500);
			return;
		}

		// Process sidebar items
		const items = sidebar.querySelectorAll(".sidebar-item, .sidebar-link");
		const categoryMap = new Map();

		items.forEach((item) => {
			const isHeader = item.dataset.isCategoryHeader === "true";
			if (isHeader) {
				const label = item.dataset.label || "";
				const purpose = item.dataset.purpose || "";
				const headerHtml = `
					<div class="sidebar-category-header">
						<span class="category-label">${frappe.utils.escape_html(label)}</span>
						<span class="category-purpose">${frappe.utils.escape_html(purpose)}</span>
					</div>
				`;
				item.innerHTML = headerHtml;
				item.classList.add("sidebar-category-header");
				item.classList.remove("sidebar-item", "sidebar-link");
			}
		});
	}

	// Initialize
	if (window.frappe) {
		frappe.ready(renderCategoryHeaders);
	} else {
		window.addEventListener("load", renderCategoryHeaders);
	}

	// Re-render on page changes
	$(document).on("page-change", renderCategoryHeaders);
})();
