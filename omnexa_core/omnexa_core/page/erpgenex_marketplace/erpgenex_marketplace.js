frappe.pages["erpgenex-marketplace"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("ErpGenEx Marketplace"),
		single_column: true,
	});

	const $container = $(`
		<div class="erpgenex-marketplace">
			<div class="mb-3 text-muted" data-section="meta"></div>
			<div class="row g-2 mb-2" data-section="filters">
				<div class="col-md-3">
					<input type="text" class="form-control form-control-sm" data-filter="search" placeholder="${__("Search by title, description, slug, or version")}">
				</div>
				<div class="col-md-2">
					<select class="form-select form-select-sm" data-filter="activity">
						<option value="">${__("All Activities")}</option>
					</select>
				</div>
				<div class="col-md-2">
					<input type="text" class="form-control form-control-sm" data-filter="version" placeholder="${__("Version")}">
				</div>
				<div class="col-md-3">
					<select class="form-select form-select-sm marketplace-sort" title="${__("Sort order")}">
						<option value="title_asc">${__("Sort: App name A–Z")}</option>
						<option value="title_desc">${__("Sort: App name Z–A")}</option>
						<option value="activity">${__("Sort: Activity")}</option>
						<option value="version">${__("Sort: Version")}</option>
						<option value="updated_desc">${__("Sort: Updated (newest)")}</option>
						<option value="updated_asc">${__("Sort: Updated (oldest)")}</option>
						<option value="installed_first">${__("Sort: Installed first")}</option>
						<option value="installed_last">${__("Sort: Not installed first")}</option>
						<option value="license">${__("Sort: License status")}</option>
					</select>
				</div>
				<div class="col-md-2">
					<button class="btn btn-sm btn-light w-100" data-action="reset-filters">${__("Reset")}</button>
				</div>
			</div>
			<div class="row g-2 mb-3" data-section="filters-dates">
				<div class="col-md-3">
					<input type="date" class="form-control form-control-sm" data-filter="updated_from" title="${__("Updated from")}">
				</div>
				<div class="col-md-3">
					<input type="date" class="form-control form-control-sm" data-filter="updated_to" title="${__("Updated to")}">
				</div>
			</div>
			<div class="table-responsive">
				<table class="table table-sm table-hover">
					<thead>
						<tr>
							<th>${__("Icon")}</th>
							<th>${__("App")}</th>
							<th>${__("Description")}</th>
							<th>${__("Activity")}</th>
							<th>${__("Version")}</th>
							<th>${__("Updated")}</th>
							<th>${__("Type")}</th>
							<th>${__("Install")}</th>
							<th>${__("License Status")}</th>
							<th>${__("Actions")}</th>
						</tr>
					</thead>
					<tbody data-section="rows">
						<tr><td colspan="10" class="text-muted">${__("Loading...")}</td></tr>
					</tbody>
				</table>
			</div>
		</div>
	`);
	$(page.body).append($container);
	let allItems = [];
	let sortKey = "title_asc";

	/** License or developer bypass accepted — hide Buy / Activate; allow Install from public repo. */
	function is_license_gate_passed(status) {
		return [
			"licensed",
			"licensed_free",
			"licensed_dev_override",
			"licensed_bundle",
			"trial",
		].includes(String(status || ""));
	}

	function renderRow(item) {
		const status = frappe.utils.escape_html(item.license_status || "");
		const title = frappe.utils.escape_html(item.title || item.app_slug);
		const appSlug = frappe.utils.escape_html(item.app_slug);
		const shortDesc = frappe.utils.escape_html(item.short_description || "");
		const activity = frappe.utils.escape_html(item.activity || "General");
		const version = frappe.utils.escape_html(item.current_version || "N/A");
		const updated = frappe.utils.escape_html(formatDate(item.updated_at));
		const type = item.is_free
			? __("Free")
			: String(item.app_slug || "").startsWith("omnexa_")
				? __("Paid")
				: __("Repo");
		const iconUrl = frappe.utils.escape_html(item.icon_url || "/assets/frappe/images/frappe-framework-logo.svg");
		const installState = item.is_installed ? __("Installed") : __("Not Installed");
		const installBadge = item.is_installed
			? `<span class="badge bg-success-subtle text-success">${installState}</span>`
			: `<span class="badge bg-warning-subtle text-warning">${installState}</span>`;
		const gate = is_license_gate_passed(item.license_status);
		const actions = [];
		// Public repos: anyone with server access can install once license gate passes (free apps always pass when licensed_free).
		if (item.is_free || gate) {
			if (item.is_installed) {
				actions.push(
					`<button class="btn btn-sm btn-outline-primary me-2" data-action="update" data-app="${appSlug}">${__("Update")}</button>`
				);
			} else {
				actions.push(
					`<button class="btn btn-sm btn-outline-primary me-2" data-action="install" data-app="${appSlug}">${__("Install")}</button>`
				);
			}
		}
		if (!item.is_free && !gate && String(item.app_slug || "").startsWith("omnexa_")) {
			actions.push(
				`<button class="btn btn-sm btn-primary me-2" data-action="buy" data-app="${appSlug}">${__("Buy")}</button>`
			);
		}
		if (!gate && String(item.app_slug || "").startsWith("omnexa_")) {
			actions.push(
				`<button class="btn btn-sm btn-secondary" data-action="activate" data-app="${appSlug}">${__("Activate Key")}</button>`
			);
		}
		return `
			<tr data-app="${appSlug}">
				<td><img src="${iconUrl}" style="width:24px;height:24px;object-fit:contain;" alt="${title}"/></td>
				<td><strong>${title}</strong><div class="text-muted small font-monospace">${appSlug}</div></td>
				<td class="small text-muted" style="max-width:22rem;">${shortDesc || "—"}</td>
				<td>${activity}</td>
				<td>${version}</td>
				<td>${updated}</td>
				<td>${type}</td>
				<td>${installBadge}</td>
				<td>${status}</td>
				<td>${actions.join("")}</td>
			</tr>`;
	}

	function formatDate(value) {
		if (!value) return "N/A";
		const d = new Date(value);
		if (Number.isNaN(d.getTime())) return "N/A";
		return frappe.datetime.str_to_user(d.toISOString().slice(0, 10));
	}

	function updateActivityFilterOptions(items) {
		const $activity = $container.find('[data-filter="activity"]');
		const selected = $activity.val() || "";
		const activities = Array.from(
			new Set((items || []).map((x) => String(x.activity || "General").trim()).filter(Boolean))
		).sort();
		$activity.empty();
		$activity.append(`<option value="">${__("All Activities")}</option>`);
		activities.forEach((a) => $activity.append(`<option value="${frappe.utils.escape_html(a)}">${frappe.utils.escape_html(a)}</option>`));
		if (selected && activities.includes(selected)) $activity.val(selected);
	}

	function parseUpdatedTs(item) {
		const v = item.updated_at;
		if (!v) return 0;
		const t = new Date(v).getTime();
		return Number.isNaN(t) ? 0 : t;
	}

	function sortFilteredRows(rows) {
		const list = [...(rows || [])];
		const sk = sortKey || "title_asc";
		const titleCmp = (a, b) =>
			String(a.title || a.app_slug || "").localeCompare(String(b.title || b.app_slug || ""), undefined, {
				sensitivity: "base",
			});
		const verCmp = (a, b) =>
			String(a.current_version || "").localeCompare(String(b.current_version || ""), undefined, {
				numeric: true,
			});
		const licCmp = (a, b) =>
			String(a.license_status || "").localeCompare(String(b.license_status || ""), undefined, {
				sensitivity: "base",
			});
		if (sk === "title_desc") {
			list.sort((a, b) => -titleCmp(a, b));
		} else if (sk === "title_asc") {
			list.sort(titleCmp);
		} else if (sk === "activity") {
			list.sort((a, b) => {
				const c = String(a.activity || "").localeCompare(String(b.activity || ""), undefined, {
					sensitivity: "base",
				});
				return c || titleCmp(a, b);
			});
		} else if (sk === "version") {
			list.sort((a, b) => verCmp(a, b) || titleCmp(a, b));
		} else if (sk === "updated_desc") {
			list.sort((a, b) => parseUpdatedTs(b) - parseUpdatedTs(a) || titleCmp(a, b));
		} else if (sk === "updated_asc") {
			list.sort((a, b) => parseUpdatedTs(a) - parseUpdatedTs(b) || titleCmp(a, b));
		} else if (sk === "installed_first") {
			list.sort((a, b) => Number(!!b.is_installed) - Number(!!a.is_installed) || titleCmp(a, b));
		} else if (sk === "installed_last") {
			list.sort((a, b) => Number(!!a.is_installed) - Number(!!b.is_installed) || titleCmp(a, b));
		} else if (sk === "license") {
			list.sort((a, b) => licCmp(a, b) || titleCmp(a, b));
		} else {
			list.sort(titleCmp);
		}
		return list;
	}

	function applyFiltersAndRender() {
		const q = String($container.find('[data-filter="search"]').val() || "").trim().toLowerCase();
		const activity = String($container.find('[data-filter="activity"]').val() || "").trim();
		const version = String($container.find('[data-filter="version"]').val() || "").trim().toLowerCase();
		const from = String($container.find('[data-filter="updated_from"]').val() || "").trim();
		const to = String($container.find('[data-filter="updated_to"]').val() || "").trim();

		const filtered = (allItems || []).filter((item) => {
			const haystack = `${item.title || ""} ${item.app_slug || ""} ${item.short_description || ""} ${item.current_version || ""}`.toLowerCase();
			if (q && !haystack.includes(q)) return false;
			if (activity && String(item.activity || "General").trim() !== activity) return false;
			if (version && !String(item.current_version || "").toLowerCase().includes(version)) return false;
			const day = item.updated_at ? String(item.updated_at).slice(0, 10) : "";
			if (from && (!day || day < from)) return false;
			if (to && (!day || day > to)) return false;
			return true;
		});

		const rows = sortFilteredRows(filtered);

		if (!rows.length) {
			$container.find('[data-section="rows"]').html(`<tr><td colspan="10" class="text-muted">${__("No apps match current filters.")}</td></tr>`);
			return;
		}
		$container.find('[data-section="rows"]').html(rows.map(renderRow).join(""));
	}

	async function loadCatalog() {
		const r = await frappe.call("omnexa_core.omnexa_core.marketplace.get_marketplace_catalog");
		const payload = (r && r.message) || {};
		const items = payload.items || [];
		allItems = items;
		updateActivityFilterOptions(items);
		const gh = frappe.utils.escape_html(payload.github_base || "https://github.com/ErpGenex");
		$container.find('[data-section="meta"]').html(
			`<div class="mb-2">${__(
				"Install and update use one GitHub organization base for every app (no GitHub login on this server)."
			)} <code class="small">${gh}/&lt;app&gt;.git</code></div>` +
				`<div>${__("Marketplace")}: <a href="${frappe.utils.escape_html(payload.platform_url || "https://erpgenex.com")}" target="_blank">` +
				`${frappe.utils.escape_html(payload.platform_url || "https://erpgenex.com")}</a> — ${__("Support")}: ` +
				`${frappe.utils.escape_html(payload.support_email || "info@erpgenex.com")}</div>`
		);
		if (!items.length) {
			$container.find('[data-section="rows"]').html(`<tr><td colspan="10" class="text-muted">${__("No apps found.")}</td></tr>`);
			return;
		}
		applyFiltersAndRender();
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

	async function onUpdate(appSlug) {
		const planResp = await frappe.call("omnexa_core.omnexa_core.marketplace.get_update_plan", {
			app_slug: appSlug,
		});
		const plan = (planResp && planResp.message) || {};
		const confirmed = await new Promise((resolve) => {
			frappe.confirm(
				`${__("Pull the latest code for this app, run migrate on this site, and rebuild assets?")}<br><br>` +
					`<b>${__("Repo")}:</b> ${frappe.utils.escape_html(plan.repo_url || "")}<br>` +
					`<b>${__("Current Version")}:</b> ${frappe.utils.escape_html(plan.current_version || "N/A")}<br>` +
					`<b>${__("What's New")}:</b> ${frappe.utils.escape_html(plan.whats_new || "")}<br><br>` +
					`<span class="text-muted">${frappe.utils.escape_html(plan.warning || "")}</span>`,
				() => resolve(true),
				() => resolve(false)
			);
		});
		if (!confirmed) return;
		const r = await frappe.call("omnexa_core.omnexa_core.marketplace.update_app_now", {
			app_slug: appSlug,
			confirm_update: 1,
		});
		const result = (r && r.message) || {};
		if (result.updated) {
			const version = result.version || "N/A";
			const buildNote = result.build_ok
				? ""
				: `<br><span class="text-warning">${__("Asset build reported a problem; check bench logs.")}</span>`;
			frappe.show_alert({ message: __("App updated: {0}", [appSlug]), indicator: "green" });
			frappe.msgprint({
				title: __("Update completed"),
				indicator: "green",
				message:
					`<b>${__("Version")}:</b> ${frappe.utils.escape_html(version)}` +
					buildNote,
			});
		} else {
			frappe.msgprint(
				`${__("Update status")}: ${frappe.utils.escape_html(result.message || "unknown")}` +
					(result.output ? `<pre class="small">${frappe.utils.escape_html(result.output)}</pre>` : "")
			);
		}
		await loadCatalog();
	}

	/** ``frappe.prompt`` returns a Dialog, not a Promise — use callback style only. */
	function onActivate(appSlug) {
		frappe.prompt(
			[
				{
					fieldname: "activation_key",
					fieldtype: "Password",
					label: __("License or developer key"),
					reqd: 1,
				},
			],
			function (values) {
				if (!values || !values.activation_key) {
					return;
				}
				const key = String(values.activation_key).trim();
				if (!key) {
					return;
				}
				frappe.call({
					method: "omnexa_core.omnexa_core.marketplace.activate_app_license",
					args: {
						app_slug: appSlug,
						activation_key: key,
					},
					freeze: true,
					freeze_message: __("Validating license..."),
					callback: function (r) {
						if (r.exc) {
							return;
						}
						const result = r.message || {};
						const installMsg = result.install
							? ` (${__("install")}: ${result.install.message || "n/a"})`
							: "";
						frappe.show_alert({
							message: __("License activated") + installMsg,
							indicator: "green",
						});
						loadCatalog();
					},
				});
			},
			__("Activate license"),
			__("Save")
		);
	}

	$container.on("click", '[data-action="buy"]', async function () {
		await onBuy($(this).data("app"));
	});
	$container.on("click", '[data-action="install"]', async function () {
		await onInstall($(this).data("app"));
	});
	$container.on("click", '[data-action="update"]', async function () {
		await onUpdate($(this).data("app"));
	});
	$container.on("click", '[data-action="activate"]', function () {
		onActivate($(this).data("app"));
	});
	$container.on("input change", "[data-filter]", function () {
		applyFiltersAndRender();
	});
	$container.on("change", ".marketplace-sort", function () {
		sortKey = String($(this).val() || "title_asc");
		applyFiltersAndRender();
	});
	$container.on("click", '[data-action="reset-filters"]', function () {
		$container.find('[data-filter="search"]').val("");
		$container.find('[data-filter="activity"]').val("");
		$container.find('[data-filter="version"]').val("");
		$container.find('[data-filter="updated_from"]').val("");
		$container.find('[data-filter="updated_to"]').val("");
		sortKey = "title_asc";
		$container.find(".marketplace-sort").val("title_asc");
		applyFiltersAndRender();
	});

	loadCatalog();
};
