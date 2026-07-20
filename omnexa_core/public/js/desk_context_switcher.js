// Company / branch view scope for privileged desk users (top navbar).
(function () {
	function can_switch() {
		return Boolean(frappe.boot && frappe.boot.omnexa_view_context && frappe.boot.omnexa_view_context.can_switch);
	}

	function mount() {
		if (!window.frappe || frappe.session.user === "Guest" || !can_switch()) return;
		if (document.getElementById("omnexa-desk-context-switcher")) return;

		const ctx = frappe.boot.omnexa_view_context || {};
		const $li = $(`
			<li class="nav-item d-none d-md-flex align-items-center omnexa-desk-context-switcher" id="omnexa-desk-context-switcher">
				<div class="omnexa-ctx-wrap">
					<select class="form-control input-xs omnexa-ctx-company" title="${__("Company")}"></select>
					<select class="form-control input-xs omnexa-ctx-branch" title="${__("Branch")}"></select>
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

		frappe.call({
			method: "omnexa_core.omnexa_core.session_context.get_view_context_options",
			callback(r) {
				if (!r.message) return;
				const data = r.message;
				const branchesByCo = data.branches_by_company || {};
				const active = data.context || ctx;
				if (data.company_activities && window.omnexaSetCompanyActivities) {
					window.omnexaSetCompanyActivities(data.company_activities);
				}

				$company.empty().append(`<option value="">${__("All companies")}</option>`);
				(data.companies || []).forEach((co) => {
					$company.append(`<option value="${frappe.utils.escape_html(co)}">${frappe.utils.escape_html(co)}</option>`);
				});

				function fill_branches(company) {
					$branch.empty();
					$branch.append(`<option value="__ALL__">${__("All branches")}</option>`);
					if (!company) {
						$branch.prop("disabled", true);
						return;
					}
					$branch.prop("disabled", false);
					(branchesByCo[company] || []).forEach((b) => {
						const label = b.branch_name || b.name;
						$branch.append(
							`<option value="${frappe.utils.escape_html(b.name)}">${frappe.utils.escape_html(label)}</option>`
						);
					});
				}

				$company.val(active.company || "");
				fill_branches(active.company || "");
				if (active.view_all_branches) {
					$branch.val("__ALL__");
				} else if (active.branch) {
					$branch.val(active.branch);
				}

				function apply() {
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
								if (frappe.ui.toolbar.clear_cache) {
									frappe.ui.toolbar.clear_cache();
								}
								frappe.set_route("Workspaces");
							}
						},
					});
				}

				$company.on("change", function () {
					fill_branches($(this).val());
					if ($(this).val()) {
						$branch.val("__ALL__");
					}
					apply();
				});
				$branch.on("change", apply);
			},
		});
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
