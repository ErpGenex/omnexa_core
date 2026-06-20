// Copyright (c) 2026, ErpGenEx
// Desk: brand PNG logos on Finance Group sidebar children (no catalog numbers).

(function () {
	"use strict";

	const TITLE_TO_LOGO = {
		"Finance Engine": "/assets/omnexa_finance_engine/logo.png",
		"Credit Engine": "/assets/omnexa_credit_engine/logo.png",
		"Credit Risk": "/assets/omnexa_credit_risk/logo.png",
		ALM: "/assets/omnexa_alm/logo.png",
		"Consumer Finance": "/assets/omnexa_consumer_finance/logo.png",
		"Vehicle Finance": "/assets/omnexa_vehicle_finance/logo.png",
		"Mortgage Finance": "/assets/omnexa_mortgage_finance/logo.png",
		Factoring: "/assets/omnexa_factoring/logo.png",
		"SME Retail Finance": "/assets/omnexa_sme_retail_finance/logo.png",
		"SME Microfinance": "/assets/omnexa_sme_microfinance/logo.png",
		"Leasing Finance": "/assets/omnexa_leasing_finance/logo.png",
		"Operational Risk": "/assets/omnexa_operational_risk/logo.png",
	};

	function apply_brand_logos(root) {
		(root || document).querySelectorAll(".sidebar-item-container[item-parent='Finance Group']").forEach((el) => {
			const title = el.getAttribute("item-name") || "";
			const logo = TITLE_TO_LOGO[title];
			if (!logo) return;
			const iconWrap = el.querySelector(".sidebar-item-icon");
			if (!iconWrap || iconWrap.dataset.omnexaBrandApplied) return;
			iconWrap.dataset.omnexaBrandApplied = "1";
			iconWrap.innerHTML = `<img src="${logo}" alt="" class="omnexa-fg-sidebar-logo" />`;
		});
	}

	function mount() {
		if (!window.frappe || frappe.session.user === "Guest") return;
		apply_brand_logos(document);
		const sidebar = document.querySelector(".desk-sidebar");
		if (sidebar && !sidebar.dataset.omnexaFgBrandObs) {
			sidebar.dataset.omnexaFgBrandObs = "1";
			const obs = new MutationObserver(() => apply_brand_logos(sidebar));
			obs.observe(sidebar, { childList: true, subtree: true });
		}
		frappe.router?.on?.("change", () => setTimeout(mount, 300));
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", mount);
	} else {
		mount();
	}
	$(window).on("load", mount);
})();
