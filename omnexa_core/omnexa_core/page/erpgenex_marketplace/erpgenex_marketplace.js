frappe.pages["erpgenex-marketplace"].on_page_load = function (wrapper) {
	if (!document.getElementById("erpgenex-marketplace-compact-style")) {
		const style = document.createElement("style");
		style.id = "erpgenex-marketplace-compact-style";
		style.textContent = `
			.erpgenex-marketplace .table {
				font-size: 12px;
				table-layout: fixed;
			}
			.erpgenex-marketplace .table th,
			.erpgenex-marketplace .table td {
				padding: 0.3rem 0.35rem;
				vertical-align: top;
				word-break: break-word;
			}
			.erpgenex-marketplace .table th:nth-child(1),
			.erpgenex-marketplace .table td:nth-child(1) { width: 36px; }
			.erpgenex-marketplace .table th:nth-child(2),
			.erpgenex-marketplace .table td:nth-child(2) { width: 170px; }
			.erpgenex-marketplace .table th:nth-child(3),
			.erpgenex-marketplace .table td:nth-child(3) { width: 120px; }
			.erpgenex-marketplace .table th:nth-child(4),
			.erpgenex-marketplace .table td:nth-child(4) { width: 96px; }
			.erpgenex-marketplace .table th:nth-child(5),
			.erpgenex-marketplace .table td:nth-child(5) { width: 72px; }
			.erpgenex-marketplace .table th:nth-child(6),
			.erpgenex-marketplace .table td:nth-child(6) { width: 86px; }
			.erpgenex-marketplace .table th:nth-child(7),
			.erpgenex-marketplace .table td:nth-child(7) { width: 56px; }
			.erpgenex-marketplace .table th:nth-child(8),
			.erpgenex-marketplace .table td:nth-child(8) { width: 68px; }
			.erpgenex-marketplace .table th:nth-child(9),
			.erpgenex-marketplace .table td:nth-child(9) { width: 120px; }
			.erpgenex-marketplace .table th:nth-child(10),
			.erpgenex-marketplace .table td:nth-child(10) { width: 62px; }
			.erpgenex-marketplace .table th:nth-child(11),
			.erpgenex-marketplace .table td:nth-child(11) { width: 106px; }
			.erpgenex-marketplace .btn.btn-sm {
				padding: 0.12rem 0.35rem;
				font-size: 11px;
				line-height: 1.2;
			}
		`;
		document.head.appendChild(style);
	}

	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("ErpGenEx Marketplace"),
		single_column: true,
	});

	const $container = $(`
		<div class="erpgenex-marketplace">
			<div class="mb-2" data-section="update-banner"></div>
			<div class="mb-3 text-muted" data-section="meta"></div>
			<div class="row g-2 mb-2" data-section="filters">
				<div class="col-md-5">
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
					<button class="btn btn-sm btn-light w-100" data-action="reset-filters">${__("Reset")}</button>
				</div>
			</div>
			<div class="mb-2 small text-muted" data-section="sort-hint">${__("Sort: click a column title (toggle ascending / descending).")}</div>
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
							<th class="marketplace-sort-th user-select-none" data-sort-col="title" role="button" tabindex="0" title="${__("Sort")}" style="cursor:pointer">${__("App")}<span class="sort-indicator text-primary"></span></th>
							<th class="marketplace-sort-th user-select-none" data-sort-col="description" role="button" tabindex="0" title="${__("Sort")}" style="cursor:pointer">${__("Description")}<span class="sort-indicator text-primary"></span></th>
							<th class="marketplace-sort-th user-select-none" data-sort-col="activity" role="button" tabindex="0" title="${__("Sort")}" style="cursor:pointer">${__("Activity")}<span class="sort-indicator text-primary"></span></th>
							<th class="marketplace-sort-th user-select-none" data-sort-col="version" role="button" tabindex="0" title="${__("Sort")}" style="cursor:pointer">${__("Version")}<span class="sort-indicator text-primary"></span></th>
							<th class="marketplace-sort-th user-select-none" data-sort-col="updated" role="button" tabindex="0" title="${__("Sort")}" style="cursor:pointer">${__("Updated")}<span class="sort-indicator text-primary"></span></th>
							<th class="marketplace-sort-th user-select-none" data-sort-col="type" role="button" tabindex="0" title="${__("Sort")}" style="cursor:pointer">${__("Type")}<span class="sort-indicator text-primary"></span></th>
							<th class="marketplace-sort-th user-select-none" data-sort-col="installed" role="button" tabindex="0" title="${__("Sort")}" style="cursor:pointer">${__("Install")}<span class="sort-indicator text-primary"></span></th>
							<th class="marketplace-sort-th user-select-none" data-sort-col="license" role="button" tabindex="0" title="${__("Sort")}" style="cursor:pointer">${__("License Status")}<span class="sort-indicator text-primary"></span></th>
							<th class="marketplace-sort-th user-select-none" data-sort-col="expires" role="button" tabindex="0" title="${__("Sort")}" style="cursor:pointer">${__("Expires")}<span class="sort-indicator text-primary"></span></th>
							<th>${__("Actions")}</th>
						</tr>
					</thead>
					<tbody data-section="rows">
						<tr><td colspan="11" class="text-muted">${__("Loading...")}</td></tr>
					</tbody>
				</table>
			</div>
		</div>
	`);
	$(page.body).append($container);
	let allItems = [];
	let lastTrialDays = 7;
	let sortColumn = "title";
	let sortDir = "asc";
	let catalogAutoRefreshTimer = null;

	/** Paid marketplace row (server: not in FREE_APPS — includes erpgenex_* verticals). */
	function isPaidCatalogItem(item) {
		return Boolean(item && !item.is_free);
	}

	/** License or developer bypass accepted — hide Buy / Activate; allow Install from public repo. */
	function is_license_gate_passed(status) {
		return [
			"licensed",
			"licensed_free",
			"licensed_dev_override",
			"licensed_bundle",
			"trial",
			"licensed_grace",
			"trial_grace",
		].includes(String(status || ""));
	}

	/** Shown while install/uninstall API runs (server does not stream real %). */
	function startMarketplaceProgress(title, description) {
		frappe.show_progress(title, 0, 100, description, false);
		let pseudo = 0;
		const interval = setInterval(() => {
			pseudo = Math.min(pseudo + (pseudo < 45 ? 4 : pseudo < 80 ? 2 : 1), 92);
			frappe.show_progress(title, pseudo, 100, description, false);
		}, 400);
		return () => clearInterval(interval);
	}

	async function completeMarketplaceProgress(title) {
		frappe.show_progress(title, 100, 100, __("Completed"), true);
		await new Promise((resolve) => setTimeout(resolve, 550));
	}

	function renderUpdateBanner(items) {
		const $b = $container.find('[data-section="update-banner"]');
		const stale = (items || []).filter((x) => x.update_available);
		if (!stale.length) {
			$b.empty();
			return;
		}
		const names = stale
			.map((i) => frappe.utils.escape_html(String(i.title || i.app_slug || "")))
			.slice(0, 12)
			.join(", ");
		const more = stale.length > 12 ? ` (+${stale.length - 12})` : "";
		$b.html(
			`<div class="alert alert-info alert-dismissible fade show mb-0" role="alert">
				<strong>${frappe.utils.escape_html(__("Updates available"))}</strong>
				<div class="small mt-1">${frappe.utils.escape_html(
					__(
						"The catalog checks Git in the background. When you are ready, use Update on a row and choose branch or tag."
					)
				)}</div>
				<div class="small font-monospace mt-1">${names}${frappe.utils.escape_html(more)}</div>
				<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="${frappe.utils.escape_html(
					__("Close")
				)}"></button>
			</div>`
		);
	}

	function scheduleCatalogAutoRefresh(ms) {
		let n = Number(ms);
		if (!Number.isFinite(n) || n < 60000) {
			n = 600000;
		}
		if (catalogAutoRefreshTimer) {
			clearInterval(catalogAutoRefreshTimer);
			catalogAutoRefreshTimer = null;
		}
		catalogAutoRefreshTimer = setInterval(function () {
			loadCatalog();
		}, n);
	}

	function pickUpdateTargetRef(plan, appSlug) {
		return new Promise((resolve) => {
			const refs = plan.update_refs || [];
			if (!refs.length) {
				resolve("");
				return;
			}
			const gm = plan.git_meta || {};
			const shaLine =
				gm.local_sha && gm.remote_sha
					? `<div class="small text-muted">${frappe.utils.escape_html(__("Local git"))}: <code>${frappe.utils.escape_html(
							gm.local_sha
					  )}</code> → ${frappe.utils.escape_html(__("Remote"))}: <code>${frappe.utils.escape_html(
							gm.remote_sha
					  )}</code></div>`
					: "";
			const d = new frappe.ui.Dialog({
				title: __("Update {0}", [appSlug]),
				fields: [
					{
						fieldname: "hint",
						fieldtype: "HTML",
						options:
							`<p class="small"><b>${frappe.utils.escape_html(__("Repo"))}:</b> ${frappe.utils.escape_html(
								plan.repo_url || ""
							)}<br>` +
							`<b>${frappe.utils.escape_html(__("App version"))}:</b> ${frappe.utils.escape_html(
								plan.current_version || "N/A"
							)}</p>` +
							shaLine +
							`<p class="text-muted small mt-2">${frappe.utils.escape_html(plan.warning || "")}</p>`,
					},
					{
						fieldname: "target_ref",
						fieldtype: "Select",
						label: __("Version / branch"),
						options: refs.map((r) => r.label).join("\n"),
						default: refs[0].label,
						reqd: 1,
					},
				],
				primary_action_label: __("Continue"),
				primary_action() {
					const label = d.get_value("target_ref");
					const picked = refs.find((r) => r.label === label);
					d.hide();
					resolve(picked ? picked.value : "");
				},
				secondary_action_label: __("Cancel"),
				secondary_action() {
					d.hide();
					resolve(null);
				},
			});
			d.show();
		});
	}

	function renderRow(item) {
		const status = frappe.utils.escape_html(item.license_status || "");
		const title = frappe.utils.escape_html(item.title || item.app_slug);
		const appSlug = frappe.utils.escape_html(item.app_slug);
		const shortDesc = frappe.utils.escape_html(item.short_description || "");
		const activity = frappe.utils.escape_html(item.activity || "General");
		let versionHtml = frappe.utils.escape_html(item.current_version || "N/A");
		if (item.update_available) {
			versionHtml += ` <span class="badge bg-info-subtle text-info ms-1" title="${frappe.utils.escape_html(
				__("New commits on remote — open Update to choose a version")
			)}">${__("Update available")}</span>`;
		}
		const updated = frappe.utils.escape_html(formatDate(item.updated_at));
		const expires = item.is_free
			? frappe.utils.escape_html(__("Forever"))
			: frappe.utils.escape_html(formatDate(item.license_expires_on));
		const expiresSrc = frappe.utils.escape_html(item.license_expiry_source || "");
		const type = item.is_free ? __("Free") : isPaidCatalogItem(item) ? __("Paid") : __("Repo");
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
		if (String(item.app_slug || "") === "omnexa_core" && item.is_installed) {
			actions.push(
				`<span class="small text-muted me-2 align-middle" title="${__("Hosts ErpGenEx Marketplace — use Update only")}">${__(
					"Platform core (update only)"
				)}</span>`
			);
		}
		if (frappe.user.has_role("System Manager") && item.is_installed && item.uninstall_allowed !== false) {
			actions.push(
				`<button class="btn btn-sm btn-outline-danger me-2" data-action="uninstall" data-app="${appSlug}">${__("Uninstall")}</button>`
			);
		}
		if (isPaidCatalogItem(item) && !gate) {
			actions.push(
				`<button class="btn btn-sm btn-primary me-2" data-action="buy" data-app="${appSlug}">${__("Buy")}</button>`
			);
		}
		if (isPaidCatalogItem(item) && !gate) {
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
				<td>${versionHtml}</td>
				<td>${updated}</td>
				<td>${type}</td>
				<td>${installBadge}</td>
				<td>${status}${expires !== "N/A" ? `<div class="small text-muted">${__("Expires")}: ${expires}${expiresSrc ? ` (${expiresSrc})` : ""}</div>` : ""}</td>
				<td>${expires}</td>
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

	function typeRank(item) {
		if (item.is_free) {
			return 0;
		}
		if (isPaidCatalogItem(item)) {
			return 1;
		}
		return 2;
	}

	function titleCmp(a, b) {
		return String(a.title || a.app_slug || "").localeCompare(String(b.title || b.app_slug || ""), undefined, {
			sensitivity: "base",
		});
	}

	function sortFilteredRows(rows) {
		const list = [...(rows || [])];
		const desc = sortDir === "desc";
		const verCmp = (a, b) =>
			String(a.current_version || "").localeCompare(String(b.current_version || ""), undefined, {
				numeric: true,
			});
		const licCmp = (a, b) =>
			String(a.license_status || "").localeCompare(String(b.license_status || ""), undefined, {
				sensitivity: "base",
			});
		const expCmp = (a, b) =>
			String(a.license_expires_on || "").localeCompare(String(b.license_expires_on || ""), undefined, {
				sensitivity: "base",
			});
		const descCmp = (a, b) =>
			String(a.short_description || "").localeCompare(String(b.short_description || ""), undefined, {
				sensitivity: "base",
			});
		const col = sortColumn || "title";

		list.sort((a, b) => {
			let c = 0;
			if (col === "title") {
				c = titleCmp(a, b);
			} else if (col === "description") {
				c = descCmp(a, b);
			} else if (col === "activity") {
				c = String(a.activity || "").localeCompare(String(b.activity || ""), undefined, { sensitivity: "base" });
			} else if (col === "version") {
				c = verCmp(a, b);
			} else if (col === "updated") {
				c = parseUpdatedTs(a) - parseUpdatedTs(b);
			} else if (col === "type") {
				c = typeRank(a) - typeRank(b);
			} else if (col === "installed") {
				c = Number(!!a.is_installed) - Number(!!b.is_installed);
			} else if (col === "license") {
				c = licCmp(a, b);
			} else if (col === "expires") {
				c = expCmp(a, b);
			} else {
				c = titleCmp(a, b);
			}
			if (c === 0) {
				c = titleCmp(a, b);
			}
			if (desc) {
				c = -c;
			}
			return c;
		});
		return list;
	}

	function updateSortColumnIndicators() {
		const arrow = sortDir === "asc" ? " \u25b2" : " \u25bc";
		$container.find(".marketplace-sort-th").each(function () {
			const col = $(this).attr("data-sort-col");
			const $ind = $(this).find(".sort-indicator");
			if (col === sortColumn) {
				$ind.text(arrow);
			} else {
				$ind.text("");
			}
		});
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
			$container.find('[data-section="rows"]').html(`<tr><td colspan="11" class="text-muted">${__("No apps match current filters.")}</td></tr>`);
			updateSortColumnIndicators();
			return;
		}
		$container.find('[data-section="rows"]').html(rows.map(renderRow).join(""));
		updateSortColumnIndicators();
	}

	function mergeItemsBySlug(baseItems, freshItems) {
		const freshMap = new Map((freshItems || []).map((x) => [String(x.app_slug || ""), x]));
		return (baseItems || []).map((row) => {
			const slug = String(row.app_slug || "");
			const fresher = freshMap.get(slug);
			return fresher ? { ...row, ...fresher } : row;
		});
	}

	async function refreshUpdateStatusInBackground() {
		try {
			const r = await frappe.call("omnexa_core.omnexa_core.marketplace.get_marketplace_catalog", {
				with_git_meta: 1,
			});
			const payload = (r && r.message) || {};
			const freshItems = payload.items || [];
			if (!freshItems.length) return;
			allItems = mergeItemsBySlug(allItems, freshItems);
			renderUpdateBanner(allItems);
			applyFiltersAndRender();
		} catch (e) {
			// Keep initial fast catalog on screen; background update checks are best-effort.
		}
	}

	async function loadCatalog() {
		const r = await frappe.call("omnexa_core.omnexa_core.marketplace.get_marketplace_catalog", {
			with_git_meta: 0,
		});
		const payload = (r && r.message) || {};
		const items = payload.items || [];
		allItems = items;
		lastTrialDays = Number(payload.trial_days) > 0 ? Number(payload.trial_days) : 7;
		renderUpdateBanner(items);
		scheduleCatalogAutoRefresh(payload.catalog_auto_refresh_ms);
		updateActivityFilterOptions(items);
		const gh = frappe.utils.escape_html(payload.github_base || "https://github.com/ErpGenex");
		const helpHtml = payload.license_help_html || "";
		$container.find('[data-section="meta"]').html(
			(helpHtml ? `<div class="mb-2">${helpHtml}</div>` : "") +
				`<div class="mb-2">${__(
					"Install and update use one GitHub organization base for every app (no GitHub login on this server)."
				)} <code class="small">${gh}/&lt;app&gt;.git</code></div>` +
				`<div>${__("Marketplace")}: <a href="${frappe.utils.escape_html(payload.platform_url || "https://erpgenex.com")}" target="_blank">` +
				`${frappe.utils.escape_html(payload.platform_url || "https://erpgenex.com")}</a> — ${__("Support")}: ` +
				`${frappe.utils.escape_html(payload.support_email || "info@erpgenex.com")}</div>`
		);
		if (!items.length) {
			$container.find('[data-section="rows"]').html(`<tr><td colspan="11" class="text-muted">${__("No apps found.")}</td></tr>`);
			updateSortColumnIndicators();
			refreshUpdateStatusInBackground();
			return;
		}
		applyFiltersAndRender();
		refreshUpdateStatusInBackground();
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
		const installSources = Array.isArray(plan.install_sources) ? plan.install_sources : [];
		const enabledSources = installSources.filter((s) => s && s.enabled);
		const installRefs = Array.isArray(plan.install_refs) ? plan.install_refs : [];
		let installSource = "github";
		if (enabledSources.length > 1) {
			installSource = await new Promise((resolve) => {
				frappe.prompt(
					[
						{
							fieldname: "install_source",
							label: __("Install source"),
							fieldtype: "Select",
							reqd: 1,
							options: enabledSources.map((s) => `${s.value}|${__(s.label)}`).join("\n"),
							default: "github",
							description: __("Choose source before installation."),
						},
					],
					(values) => resolve((values && values.install_source) || "github"),
					__("Install Source"),
					__("Continue")
				);
			});
			if (!installSource) return;
		} else if (enabledSources.length === 1) {
			installSource = enabledSources[0].value || "github";
		}
		let installRef = "";
		if (installSource === "github") {
			installRef = await new Promise((resolve) => {
				const quickRefs = installRefs
					.filter((r) => r && r.value && /^v?\d+\.\d+\.\d+/.test(r.value))
					.slice(0, 6);
				const d = new frappe.ui.Dialog({
					title: __("Choose Version"),
					fields: [
						{
							fieldname: "quick_hint",
							fieldtype: "HTML",
							options: quickRefs.length
								? `<div class="small text-muted mb-2">${__(
										"Quick buttons for latest release tags"
								  )}</div>
								   <div class="d-flex flex-wrap gap-2">
									${quickRefs
										.map(
											(r) =>
												`<button class="btn btn-xs btn-secondary js-install-ref-chip" data-ref="${frappe.utils.escape_html(
													r.value
												)}">${frappe.utils.escape_html(r.value)}</button>`
										)
										.join("")}
								   </div>`
								: `<div class="small text-muted">${__("No quick tags available. Use pick list or manual ref.")}</div>`,
						},
						{
							fieldname: "install_ref_pick",
							label: __("Version / branch (pick list)"),
							fieldtype: "Select",
							options: [__("Default (server policy / default branch)")]
								.concat(installRefs.map((r) => r.label || r.value))
								.join("\n"),
							default: __("Default (server policy / default branch)"),
						},
						{
							fieldname: "install_ref",
							label: __("Version / branch / tag"),
							fieldtype: "Data",
							description: __("Optional. Example: develop, main, v1.0.0-beta"),
						},
					],
					primary_action_label: __("Continue"),
					primary_action() {
						const manual = (d.get_value("install_ref") || "").trim();
						if (manual) {
							d.hide();
							resolve(manual);
							return;
						}
						const pickedLabel = d.get_value("install_ref_pick") || "";
						const picked = installRefs.find((r) => (r.label || r.value) === pickedLabel);
						d.hide();
						resolve((picked && picked.value) || "");
					},
					secondary_action_label: __("Cancel"),
					secondary_action() {
						d.hide();
						resolve(null);
					},
				});
				d.show();
				d.$wrapper.on("click", ".js-install-ref-chip", (e) => {
					e.preventDefault();
					const ref = $(e.currentTarget).attr("data-ref") || "";
					d.set_value("install_ref", ref);
				});
			});
			if (installRef === null) return;
		}
		const sourceLabel =
			(installSources.find((s) => s && s.value === installSource) || {}).label || installSource;
		const confirmed = await new Promise((resolve) => {
			frappe.confirm(
				`${__("Proceed with app installation?")}<br><br>` +
					`<b>${__("Source")}:</b> ${frappe.utils.escape_html(__(sourceLabel))}<br>` +
					`<b>${__("Version / ref")}:</b> ${frappe.utils.escape_html(installRef || __("Default"))}<br>` +
					`<b>${__("Repo")}:</b> ${frappe.utils.escape_html(plan.repo_url || "")}<br>` +
					`<b>${__("Current Version")}:</b> ${frappe.utils.escape_html(plan.current_version || "N/A")}<br>` +
					`<b>${__("What's New")}:</b> ${frappe.utils.escape_html(plan.whats_new || "")}<br><br>` +
					`${__("A full backup will run before install to avoid data loss.")}`,
				() => resolve(true),
				() => resolve(false)
			);
		});
		if (!confirmed) return;
		const stopTick = startMarketplaceProgress(
			__("Installing app"),
			__("Backup, repository fetch, and install may take a few minutes…")
		);
		let r;
		try {
			r = await frappe.call({
				method: "omnexa_core.omnexa_core.marketplace.install_app_now",
				args: { app_slug: appSlug, confirm_install: 1, install_source: installSource, install_ref: installRef },
				freeze: false,
			});
		} catch (e) {
			frappe.hide_progress();
			return;
		} finally {
			stopTick();
		}
		if (!r || r.exc) {
			frappe.hide_progress();
			return;
		}
		await completeMarketplaceProgress(__("Installing app"));
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

	async function onUninstall(appSlug) {
		const planResp = await frappe.call("omnexa_core.omnexa_core.marketplace.get_uninstall_plan", {
			app_slug: appSlug,
		});
		const plan = (planResp && planResp.message) || {};
		if (!plan.is_installed) {
			frappe.msgprint(__("This app is not installed on this site."));
			return;
		}
		if (plan.is_protected) {
			frappe.msgprint(__("This app cannot be uninstalled from here (protected platform app)."));
			return;
		}
		if ((plan.dependents || []).length) {
			frappe.msgprint(
				`${__("Uninstall blocked — other apps depend on this one")}: <b>${frappe.utils.escape_html(
					(plan.dependents || []).join(", ")
				)}</b>`
			);
			return;
		}
		if (!plan.can_uninstall) {
			frappe.msgprint(__("Uninstall is not available for this app right now."));
			return;
		}
		const confirmed = await new Promise((resolve) => {
			frappe.confirm(
				`<b>${__("Remove this app from the current site?")}</b><br><br>` +
					`${frappe.utils.escape_html(plan.warning || "")}<br><br>` +
					`<span class="text-danger">${__("This deletes DocTypes and data for this app on this site.")}</span>`,
				() => resolve(true),
				() => resolve(false)
			);
		});
		if (!confirmed) return;
		const stopTick = startMarketplaceProgress(
			__("Uninstalling app"),
			__("Backup (if enabled), then removing modules and DocTypes — may take a few minutes…")
		);
		let r;
		try {
			r = await frappe.call({
				method: "omnexa_core.omnexa_core.marketplace.uninstall_app_now",
				args: { app_slug: appSlug, confirm_uninstall: 1 },
				freeze: false,
			});
		} catch (e) {
			frappe.hide_progress();
			return;
		} finally {
			stopTick();
		}
		if (!r || r.exc) {
			frappe.hide_progress();
			return;
		}
		await completeMarketplaceProgress(__("Uninstalling app"));
		const result = (r && r.message) || {};
		if (result.uninstalled) {
			frappe.show_alert({ message: __("App uninstalled from site: {0}", [appSlug]), indicator: "green" });
			frappe.msgprint({
				title: __("Uninstall completed"),
				indicator: "green",
				message: __("The app was removed from this site. Restart bench or clear cache if Desk still shows old menus."),
			});
		} else {
			frappe.msgprint(__("Uninstall status: {0}", [result.message || "unknown"]));
		}
		await loadCatalog();
	}

	async function onUpdate(appSlug) {
		const planResp = await frappe.call("omnexa_core.omnexa_core.marketplace.get_update_plan", {
			app_slug: appSlug,
		});
		const plan = (planResp && planResp.message) || {};
		const updateSources = Array.isArray(plan.update_sources) ? plan.update_sources : [];
		const enabledSources = updateSources.filter((s) => s && s.enabled);
		let updateSource = "github";
		if (enabledSources.length > 1) {
			updateSource = await new Promise((resolve) => {
				frappe.prompt(
					[
						{
							fieldname: "update_source",
							label: __("Update source"),
							fieldtype: "Select",
							reqd: 1,
							options: enabledSources.map((s) => `${s.value}|${__(s.label)}`).join("\n"),
							default: "github",
							description: __("Choose source before update."),
						},
					],
					(values) => resolve((values && values.update_source) || "github"),
					__("Update Source"),
					__("Continue")
				);
			});
			if (!updateSource) return;
		} else if (enabledSources.length === 1) {
			updateSource = enabledSources[0].value || "github";
		}
		const targetRef = updateSource === "github" ? await pickUpdateTargetRef(plan, appSlug) : "";
		if (targetRef === null) {
			return;
		}
		const stopTick = startMarketplaceProgress(
			__("Updating app"),
			__("Git pull, database migrate, and asset build may take several minutes…")
		);
		let r;
		try {
			r = await frappe.call({
				method: "omnexa_core.omnexa_core.marketplace.update_app_now",
				args: { app_slug: appSlug, confirm_update: 1, target_ref: targetRef, update_source: updateSource },
				freeze: false,
			});
		} catch (e) {
			frappe.hide_progress();
			return;
		} finally {
			stopTick();
		}
		if (!r || r.exc) {
			frappe.hide_progress();
			return;
		}
		await completeMarketplaceProgress(__("Updating app"));
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
	function onRevoke(appSlug, isFree) {
		const fields = [];
		if (!isFree) {
			fields.push({
				fieldname: "remove_key",
				fieldtype: "Check",
				label: __("Remove stored license key from this site"),
				default: 1,
			});
		}
		fields.push({
			fieldname: "clear_trial",
			fieldtype: "Check",
			label: __("Reset trial counter (new {0}-day window from next license check)", [String(lastTrialDays)]),
			default: 0,
		});
		frappe.prompt(
			fields,
			function (values) {
				const removeKey = isFree ? 0 : values.remove_key ? 1 : 0;
				const clearTrial = values.clear_trial ? 1 : 0;
				frappe.call({
					method: "omnexa_core.omnexa_core.marketplace.revoke_app_license",
					args: {
						app_slug: appSlug,
						remove_key: removeKey,
						clear_trial: clearTrial,
					},
					freeze: true,
					callback: function (resp) {
						if (resp.exc) {
							return;
						}
						const msg = (resp.message && resp.message.status) || "";
						frappe.show_alert({
							message: __("License data updated: {0}. Reloading…", [msg]),
							indicator: "orange",
						});
						if (typeof frappe.refresh_omnexa_license_boot === "function") {
							frappe.refresh_omnexa_license_boot().always(function () {
								window.location.reload();
							});
						} else {
							window.location.reload();
						}
					},
				});
			},
			__("Revoke or reset trial"),
			__("Apply")
		);
	}

	function onActivate(appSlug) {
		frappe.prompt(
			[
				{
					fieldname: "activation_key",
					fieldtype: "Password",
					label: __("License or developer key"),
					length: 2048,
					description: __("Supports long JWT / armored activation keys."),
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
	$container.on("click", '[data-action="uninstall"]', async function () {
		await onUninstall($(this).data("app"));
	});
	$container.on("click", '[data-action="activate"]', function () {
		onActivate($(this).data("app"));
	});
	$container.on("input change", "[data-filter]", function () {
		applyFiltersAndRender();
	});
	$container.on("click", ".marketplace-sort-th", function (e) {
		e.preventDefault();
		const col = $(this).attr("data-sort-col");
		if (!col) {
			return;
		}
		if (sortColumn === col) {
			sortDir = sortDir === "asc" ? "desc" : "asc";
		} else {
			sortColumn = col;
			sortDir = col === "updated" ? "desc" : "asc";
		}
		applyFiltersAndRender();
	});
	$container.on("keydown", ".marketplace-sort-th", function (e) {
		if (e.key === "Enter" || e.key === " ") {
			e.preventDefault();
			$(this).trigger("click");
		}
	});
	$container.on("click", '[data-action="reset-filters"]', function () {
		$container.find('[data-filter="search"]').val("");
		$container.find('[data-filter="activity"]').val("");
		$container.find('[data-filter="version"]').val("");
		$container.find('[data-filter="updated_from"]').val("");
		$container.find('[data-filter="updated_to"]').val("");
		sortColumn = "title";
		sortDir = "asc";
		applyFiltersAndRender();
	});

	loadCatalog();
};
