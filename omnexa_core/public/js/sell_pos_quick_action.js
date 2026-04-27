(() => {
	const BTN_ID = "erpgenex-new-pos-sale-btn";

	function isSellRoute() {
		const route = frappe.get_route() || [];
		return (route[0] || "").toLowerCase() === "sell";
	}

	async function resolveDefaultPosProfile() {
		try {
			const company = frappe.defaults.get_user_default("Company") || undefined;
			const rows = await frappe.db.get_list("POS Profile", {
				fields: ["name"],
				filters: Object.assign({ is_active: 1 }, company ? { company } : {}),
				order_by: "modified desc",
				limit: 1,
			});
			return rows?.[0]?.name || null;
		} catch (e) {
			return null;
		}
	}

	async function createPosSale() {
		const posProfile = await resolveDefaultPosProfile();
		const values = { is_pos: 1 };
		if (posProfile) {
			values.pos_profile = posProfile;
		}
		frappe.new_doc("Sales Invoice", values);
	}

	function injectButton() {
		if (!isSellRoute()) return;
		const actions = document.querySelector(".layout-main .page-actions") || document.querySelector(".page-actions");
		if (!actions) return;
		if (document.getElementById(BTN_ID)) return;
		const btn = document.createElement("button");
		btn.id = BTN_ID;
		btn.className = "btn btn-primary btn-sm";
		btn.textContent = __("New POS Sale");
		btn.addEventListener("click", () => {
			createPosSale();
		});
		actions.prepend(btn);
	}

	function install() {
		injectButton();
		setTimeout(injectButton, 500);
		setTimeout(injectButton, 1200);
	}

	frappe.router?.on?.("change", install);
	$(document).on("app_ready", install);
})();
