(() => {
	const BTN_ID = "erpgenex-new-pos-sale-btn";
	const BAR_ID = "erpgenex-sell-pos-banner";

	function isSellRoute() {
		const route = frappe.get_route() || [];
		const r0 = (route[0] || "").toLowerCase();
		if (r0 === "sell") return true;
		if (r0 === "workspaces") {
			const ws = (route[2] || route[1] || "").toLowerCase();
			return ws === "sell";
		}
		return false;
	}

	function openRetailPos() {
		frappe.set_route("retail-pos");
	}

	function injectHeaderButton() {
		if (!isSellRoute()) return;
		const actions =
			document.querySelector(".layout-main .page-head .page-actions") ||
			document.querySelector(".page-head .page-actions") ||
			document.querySelector(".page-actions");
		if (!actions || document.getElementById(BTN_ID)) return;
		const btn = document.createElement("button");
		btn.id = BTN_ID;
		btn.className = "btn btn-primary btn-sm erpgenex-sell-pos-btn";
		btn.textContent = __("Retail POS");
		btn.addEventListener("click", openRetailPos);
		actions.prepend(btn);
	}

	function injectWorkspaceBanner() {
		if (!isSellRoute()) return;
		const main =
			document.querySelector(".layout-main-section") ||
			document.querySelector(".workspace-container") ||
			document.querySelector(".layout-main");
		if (!main || document.getElementById(BAR_ID)) return;
		const bar = document.createElement("div");
		bar.id = BAR_ID;
		bar.className = "erpgenex-sell-pos-banner";
		bar.innerHTML = `
			<div class="erpgenex-sell-pos-banner__text">
				<strong>${__("Retail POS")}</strong>
				<span>${__("Integrated counter sales — scan, cart, pay, thermal receipt")}</span>
			</div>
			<button type="button" class="btn btn-primary erpgenex-sell-pos-banner__btn">${__("Open Retail POS")}</button>
		`;
		bar.querySelector("button").addEventListener("click", openRetailPos);
		main.prepend(bar);
	}

	function install() {
		injectHeaderButton();
		injectWorkspaceBanner();
		setTimeout(() => {
			injectHeaderButton();
			injectWorkspaceBanner();
		}, 500);
		setTimeout(() => {
			injectHeaderButton();
			injectWorkspaceBanner();
		}, 1500);
	}

	frappe.router?.on?.("change", install);
	$(document).on("app_ready", install);
})();
