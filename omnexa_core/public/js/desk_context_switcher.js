// Company / branch view scope + activity menu filter mode (any company).
(function () {
	function can_switch() {
		return Boolean(frappe.boot && frappe.boot.omnexa_view_context && frappe.boot.omnexa_view_context.can_switch);
	}

	function bootOptions() {
		return (frappe.boot && frappe.boot.omnexa_filter_options) || {};
	}

	function activityFilterBoot() {
		return (frappe.boot && frappe.boot.omnexa_activity_filter) || {};
	}

	function bindActivityScope($activityScope, active) {
		$activityScope.removeClass("d-none").empty();
		$activityScope.append(`<option value="company">${__("Company activity menus")}</option>`);
		$activityScope.append(`<option value="all">${__("All activities")}</option>`);
		const filter = activityFilterBoot();
		$activityScope.val(active.activity_menu_scope || filter.activity_menu_scope || "company");
	}

	function wireActivityScopeChange($activityScope) {
		$activityScope.off("change.omnexaActivityScope").on("change.omnexaActivityScope", function () {
			const scope = $(this).val() || "company";
			frappe.call({
				method: "omnexa_core.omnexa_core.session_context.set_desk_activity_menu_scope",
				type: "POST",
				args: { scope },
				freeze: true,
				freeze_message: __("Updating activity menus…"),
				callback(res) {
					if (!res.exc && res.message) {
						frappe.boot.omnexa_view_context = {
							...(frappe.boot.omnexa_view_context || {}),
							...res.message,
						};
						if (frappe.boot.omnexa_activity_filter) {
							frappe.boot.omnexa_activity_filter.activity_menu_scope = res.message.activity_menu_scope;
							frappe.boot.omnexa_activity_filter.active = res.message.activity_menu_scope === "company";
						}
						window.location.reload();
					}
				},
			});
		});
	}

	function mount() {
		if (!window.frappe || frappe.session.user === "Guest") return;
		if (document.getElementById("omnexa-desk-context-switcher")) return;

		const ctx = frappe.boot.omnexa_view_context || {};
		const boot = bootOptions();
		const switcher = can_switch();
		const $li = $(`
			<li class="nav-item d-none d-md-flex align-items-center omnexa-desk-context-switcher" id="omnexa-desk-context-switcher">
				<div class="omnexa-ctx-wrap">
					<select class="form-control input-xs omnexa-ctx-company${switcher ? "" : " d-none"}" title="${__("Company")}"></select>
					<select class="form-control input-xs omnexa-ctx-branch${switcher ? "" : " d-none"}" title="${__("Branch")}"></select>
					<select class="form-control input-xs omnexa-ctx-activity-scope d-none" title="${__("Activity menus")}"></select>
				</div>
			</li>
		`);

		let $anchor = $("header .navbar-nav .dropdown-help").closest("li.nav-item");
		if (!$anchor.length) {
			$anchor = $("header .navbar-nav .dropdown-navbar-user").closest("li.nav-item");
		}
		if ($anchor.length) {
			$anchor.before($li);
		} else {
			$("header .navbar-nav").prepend($li);
		}

		const $company = $li.find(".omnexa-ctx-company");
		const $branch = $li.find(".omnexa-ctx-branch");
		const $activityScope = $li.find(".omnexa-ctx-activity-scope");
		const branchesByCo = { ...(boot.branches_by_company || {}) };

		function populateCompanies(companies, active) {
			if (!switcher) return;
			$company.empty().append(`<option value="">${__("All companies")}</option>`);
			(companies || []).forEach((co) => {
				$company.append(`<option value="${frappe.utils.escape_html(co)}">${frappe.utils.escape_html(co)}</option>`);
			});
			$company.val(active.company || "");
		}

		function fill_branches(company, active) {
			if (!switcher) return;
			$branch.empty();
			$branch.append(`<option value="__ALL__">${__("All branches")}</option>`);
			if (!company) {
				$branch.prop("disabled", true);
				return;
			}
			$branch.prop("disabled", false);

			function renderBranches(rows) {
				(rows || []).forEach((b) => {
					const label = b.branch_name || b.name;
					$branch.append(
						`<option value="${frappe.utils.escape_html(b.name)}">${frappe.utils.escape_html(label)}</option>`
					);
				});
				if (active.view_all_branches) {
					$branch.val("__ALL__");
				} else if (active.branch) {
					$branch.val(active.branch);
				}
			}

			if (branchesByCo[company]) {
				renderBranches(branchesByCo[company]);
				return;
			}

			frappe.call({
				method: "omnexa_core.omnexa_core.session_context.get_branches_for_company",
				args: { company },
				callback(r) {
					branchesByCo[company] = r.message || [];
					renderBranches(branchesByCo[company]);
				},
			});
		}

		function apply() {
			if (!switcher) return;
			const company = $company.val() || null;
			const branchVal = $branch.val();
			const view_all = !company ? 0 : branchVal === "__ALL__" ? 1 : 0;
			const branch = view_all ? null : branchVal;

			frappe.call({
				method: "omnexa_core.omnexa_core.session_context.set_desk_view_context",
				type: "POST",
				args: { company, branch, view_all_branches: view_all },
				freeze: true,
				freeze_message: __("Updating view scope…"),
				callback(res) {
					if (!res.exc && res.message) {
						frappe.boot.omnexa_view_context = res.message;
						if (window.omnexaUpdateActivityBadge) {
							window.omnexaUpdateActivityBadge(res.message.company);
						}
						frappe.show_alert({
							message: __("View scope: {0}", [res.message.label || __("Updated")]),
							indicator: "green",
						});
						window.location.reload();
					}
				},
			});
		}

		const active = boot.context || ctx;
		populateCompanies(boot.companies || [], active);
		if (boot.company_activities && window.omnexaSetCompanyActivities) {
			window.omnexaSetCompanyActivities(boot.company_activities);
		}
		fill_branches(active.company || "", active);
		bindActivityScope($activityScope, active);
		wireActivityScopeChange($activityScope);

		if (switcher) {
			$company.on("change", function () {
				const co = $(this).val();
				fill_branches(co, { view_all_branches: true });
				if (co) {
					$branch.val("__ALL__");
				}
				apply();
			});
			$branch.on("change", apply);
		}

		if (switcher) {
			frappe.call({
				method: "omnexa_core.omnexa_core.session_context.get_view_context_options",
				callback(r) {
					if (!r.message) return;
					const data = r.message;
					if (data.company_activities && window.omnexaSetCompanyActivities) {
						window.omnexaSetCompanyActivities(data.company_activities);
					}
					Object.assign(branchesByCo, data.branches_by_company || {});
					const current = data.context || frappe.boot.omnexa_view_context || {};
					populateCompanies(data.companies || boot.companies || [], current);
					fill_branches(current.company || "", current);
					bindActivityScope($activityScope, current);
				},
			});
		}
	}

	function init() {
		if (!window.frappe) return;
		$(document).on("toolbar_setup", mount);
		mount();
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", init);
	} else {
		init();
	}
	$(window).on("load", init);
})();
