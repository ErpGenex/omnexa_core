frappe.pages["erpgenex-marketplace"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("ErpGenEx Marketplace"),
		single_column: true,
	});

	const $container = $(`
		<div class="erpgenex-marketplace">
			<div class="mb-3 text-muted" data-section="meta"></div>
			<div class="table-responsive">
				<table class="table table-sm table-hover">
					<thead>
						<tr>
							<th>${__("Icon")}</th>
							<th>${__("App")}</th>
							<th>${__("Type")}</th>
							<th>${__("Install")}</th>
							<th>${__("License Status")}</th>
							<th>${__("Actions")}</th>
						</tr>
					</thead>
					<tbody data-section="rows">
						<tr><td colspan="6" class="text-muted">${__("Loading...")}</td></tr>
					</tbody>
				</table>
			</div>
		</div>
	`);
	$(page.body).append($container);

	function renderRow(item) {
		const status = frappe.utils.escape_html(item.license_status || "");
		const title = frappe.utils.escape_html(item.title || item.app_slug);
		const appSlug = frappe.utils.escape_html(item.app_slug);
		const type = item.is_free ? __("Free") : __("Paid");
		const iconUrl = frappe.utils.escape_html(item.icon_url || "/assets/frappe/images/frappe-framework-logo.svg");
		const installState = item.is_installed ? __("Installed") : __("Not Installed");
		const installBadge = item.is_installed
			? `<span class="badge bg-success-subtle text-success">${installState}</span>`
			: `<span class="badge bg-warning-subtle text-warning">${installState}</span>`;
		return `
			<tr data-app="${appSlug}">
				<td><img src="${iconUrl}" style="width:24px;height:24px;object-fit:contain;" alt="${title}"/></td>
				<td><strong>${title}</strong><div class="text-muted small">${appSlug}</div></td>
				<td>${type}</td>
				<td>${installBadge}</td>
				<td>${status}</td>
				<td>
					${item.is_free ? `<button class="btn btn-sm btn-outline-primary me-2" data-action="install" data-app="${appSlug}">${__("Install")}</button>` : `<button class="btn btn-sm btn-primary me-2" data-action="buy" data-app="${appSlug}">${__("Buy")}</button>`}
					<button class="btn btn-sm btn-secondary" data-action="activate" data-app="${appSlug}">${__("Activate Key")}</button>
				</td>
			</tr>`;
	}

	async function loadCatalog() {
		const r = await frappe.call("omnexa_core.omnexa_core.marketplace.get_marketplace_catalog");
		const payload = (r && r.message) || {};
		const items = payload.items || [];
		$container.find('[data-section="meta"]').html(
			`${__("Marketplace")}: <a href="${frappe.utils.escape_html(payload.platform_url || "https://erpgenex.com")}" target="_blank">` +
				`${frappe.utils.escape_html(payload.platform_url || "https://erpgenex.com")}</a> - ${__("Support")}: ` +
				`${frappe.utils.escape_html(payload.support_email || "info@erpgenex.com")}`
		);
		if (!items.length) {
			$container.find('[data-section="rows"]').html(`<tr><td colspan="6" class="text-muted">${__("No apps found.")}</td></tr>`);
			return;
		}
		$container.find('[data-section="rows"]').html(items.map(renderRow).join(""));
	}

	async function onBuy(appSlug) {
		const r = await frappe.call("omnexa_core.omnexa_core.marketplace.get_checkout_url", {
			app_slug: appSlug,
			months: 12,
		});
		const url = r && r.message && r.message.url;
		if (url) window.open(url, "_blank", "noopener,noreferrer");
	}

	async function onInstall(appSlug) {
		const planResp = await frappe.call("omnexa_core.omnexa_core.marketplace.get_install_plan", {
			app_slug: appSlug,
		});
		const plan = (planResp && planResp.message) || {};
		const confirmed = await new Promise((resolve) => {
			frappe.confirm(
				`${__("Install from approved GitHub repo?")}<br><br>` +
					`<b>${__("Repo")}:</b> ${frappe.utils.escape_html(plan.repo_url || "")}<br>` +
					`<b>${__("Current Version")}:</b> ${frappe.utils.escape_html(plan.current_version || "N/A")}<br>` +
					`<b>${__("What's New")}:</b> ${frappe.utils.escape_html(plan.whats_new || "")}<br><br>` +
					`${__("A full backup will run before install to avoid data loss.")}`,
				() => resolve(true),
				() => resolve(false)
			);
		});
		if (!confirmed) return;
		const r = await frappe.call("omnexa_core.omnexa_core.marketplace.install_app_now", {
			app_slug: appSlug,
			confirm_install: 1,
		});
		const result = (r && r.message) || {};
		if (result.installed) {
			const version = result.version || "N/A";
			const whatsNew = result.whats_new || "";
			frappe.show_alert({ message: __("App is installed: {0}", [appSlug]), indicator: "green" });
			frappe.msgprint({
				title: __("Installation Completed"),
				indicator: "green",
				message:
					`<b>${__("Version")}:</b> ${frappe.utils.escape_html(version)}<br>` +
					`<b>${__("What's New")}:</b> ${frappe.utils.escape_html(whatsNew)}`,
			});
		} else {
			frappe.msgprint(__("Install status: {0}", [result.message || "unknown"]));
		}
		await loadCatalog();
	}

	async function onActivate(appSlug) {
		const data = await frappe.prompt(
			[{ fieldname: "activation_key", fieldtype: "Small Text", label: __("Activation Key"), reqd: 1 }],
			(values) => values,
			__("Activate License"),
			__("Save")
		);
		if (!data || !data.activation_key) return;
		const r = await frappe.call("omnexa_core.omnexa_core.marketplace.activate_app_license", {
			app_slug: appSlug,
			activation_key: data.activation_key,
		});
		const result = (r && r.message) || {};
		const installMsg = result.install ? ` (${__("install")}: ${result.install.message || "n/a"})` : "";
		frappe.show_alert({ message: __("License activated") + installMsg, indicator: "green" });
		await loadCatalog();
	}

	$container.on("click", '[data-action="buy"]', async function () {
		await onBuy($(this).data("app"));
	});
	$container.on("click", '[data-action="install"]', async function () {
		await onInstall($(this).data("app"));
	});
	$container.on("click", '[data-action="activate"]', async function () {
		await onActivate($(this).data("app"));
	});

	loadCatalog();
};
