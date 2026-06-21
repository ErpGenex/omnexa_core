frappe.pages["finance-workcenter"].on_page_load = function (wrapper) {
	function start(OJ) {
		const $mount = OJ.mountDeskPage(wrapper, __("Finance Workcenter"));

		function t(ar, en) {
			return OJ.t(ar, en);
		}

		function esc(v) {
			return OJ.esc(v);
		}

		async function render() {
			const ctx = await OJ.call("omnexa_core.omnexa_core.finance_demo.finance_workcenter.get_workcenter_context_api");
			const groups = ctx.grouped_portals || [];
			const isAdmin = ctx.is_admin;

			let defaults = { companies: [], branches: [], default_company: "", default_branch: "" };
			let creds = { password: "", users: [] };
			if (isAdmin) {
				[defaults, creds] = await Promise.all([
					OJ.call("omnexa_core.omnexa_core.finance_demo.finance_role_demo.get_finance_demo_defaults"),
					OJ.call("omnexa_core.omnexa_core.finance_demo.finance_role_demo.get_finance_demo_credentials"),
				]);
			}

			const $panel = $(`<div class="oj-workcenter-panel finance-workcenter-journey"></div>`);
			if (isAdmin) {
				const companyOpts = (defaults.companies || [])
					.map(
						(c) =>
							`<option value="${esc(c.name)}" ${c.name === defaults.default_company ? "selected" : ""}>${esc(c.name)}</option>`
					)
					.join("");
				const branchOpts = (defaults.branches || [])
					.map(
						(b) =>
							`<option value="${esc(b.name)}" data-company="${esc(b.company)}" ${b.name === defaults.default_branch ? "selected" : ""}>${esc(b.name)}</option>`
					)
					.join("");
				$panel.append(`
				<h4>${t("مركز عمل المجموعة المالية", "Finance Group Workcenter")}</h4>
				<p class="oj-muted">${t(
					"نظام البوابات الأساسي — كل مستخدم يدخل حسب دوره إلى البوابة المخصصة",
					"Primary portal system — each user enters their app through a role-based portal"
				)}</p>
				<div class="row mb-3">
					<div class="col-md-4"><label class="small oj-muted">${t("الشركة", "Company")}</label><select class="form-control wc-company">${companyOpts}</select></div>
					<div class="col-md-4"><label class="small oj-muted">${t("الفرع", "Branch")}</label><select class="form-control wc-branch">${branchOpts}</select></div>
				</div>
				<button type="button" class="oj-btn oj-btn-primary btn-seed-roles">${t("تهيئة أدوار Workcenter", "Seed Workcenter Roles")}</button>
				<button type="button" class="oj-btn oj-btn-secondary btn-seed-all ml-2">${t("مزامنة Workflow + بيانات", "Sync Workflow + Data")}</button>
				<button type="button" class="oj-btn oj-btn-success btn-run-closure ml-2">${t("فحص إغلاق — Global #1", "Closure Audit")}</button>
				<p class="oj-muted small mt-2">${t("حسابات التدريب", "Training accounts")}: <code>${esc(creds.password || "—")}</code></p>
			`);
				const $usersTable = OJ.dataTable(
					[
						{ field: "role", label: t("الدور", "Role") },
						{ field: "email", label: t("البريد", "Email") },
						{ field: "route", label: t("البوابة", "Portal") },
					],
					(creds.users || []).map((u) => ({ role: u.role, email: u.email, route: u.route }))
				);
				$panel.append(`<h5 class="oj-section-title">${t("حسابات الأدوار", "Role Accounts")}</h5>`);
				$panel.append($usersTable);
			} else {
				$panel.append(`
				<h4>${t("مركز العمل", "Workcenter")}</h4>
				<p class="oj-muted">${t("مرحباً — اختر البوابة المناسبة لدورك", "Welcome — open your role portal below")}</p>
				<p><strong>${esc(ctx.role_label || "")}</strong></p>
				<button type="button" class="oj-btn oj-btn-primary btn-primary-portal">${t("فتح بوابتي", "Open My Portal")}</button>
			`);
			}

			const $portalRoot = OJ.portalCategoryGrid(groups);
			const $body = $("<div class='finance-workcenter-journey'></div>");
			$body.append($panel);
			$body.append(
				`<h4 class="oj-section-title">${t("بوابات Journey حسب التطبيق", "Journey portals by application")}</h4>`
			);
			$body.append($portalRoot);

			const $shell = OJ.shell({
				title: t("Finance Workcenter", "Finance Workcenter"),
				subtitle: t("ErpGenEx — Finance Group", "ErpGenEx — Finance Group"),
				role: ctx.role_label || t("مستخدم", "User"),
				sidebar: OJ.defaultSidebar("executive", "/app/finance-workcenter"),
				bodyEl: $body,
				currentPage: "finance-workcenter",
			});

			$mount.empty().append($shell);
			if (window.omnexa_finance && omnexa_finance.dismissOnboardingDialog) {
				omnexa_finance.dismissOnboardingDialog();
			}

			if (isAdmin) {
				$body.find(".wc-company").on("change", function () {
					const company = $(this).val();
					const $branch = $body.find(".wc-branch");
					$branch.find("option").each(function () {
						$(this).toggle(!company || $(this).data("company") === company);
					});
					const first = $branch.find("option:visible:first").val();
					if (first) $branch.val(first);
				});
				$body.find(".btn-seed-roles").on("click", () => {
					const company = $body.find(".wc-company").val();
					const branch = $body.find(".wc-branch").val();
					frappe.confirm(t("تهيئة Workcenter والأدوار؟", "Seed Workcenter roles?"), () => {
						frappe.call({
							method: "omnexa_core.omnexa_core.finance_demo.finance_role_demo.seed_finance_role_demo",
							args: { company, branch },
							freeze: true,
							callback() {
								frappe.show_alert({ message: t("تم", "Done"), indicator: "green" });
								render();
							},
						});
					});
				});
				$body.find(".btn-seed-all").on("click", () => {
					const company = $body.find(".wc-company").val();
					const branch = $body.find(".wc-branch").val();
					frappe.call({
						method: "omnexa_core.omnexa_core.finance_demo.finance_vertical_bpe.seed_all_finance_vertical_demos",
						args: { company, branch },
						freeze: true,
						callback() {
							frappe.show_alert({ message: t("تم", "Done"), indicator: "green" });
						},
					});
				});
				$body.find(".btn-run-closure").on("click", () => {
					frappe.call({
						method: "omnexa_core.omnexa_core.finance_demo.finance_group_master.run_full_finance_group_closure",
						freeze: true,
						callback(r) {
							const m = r.message || {};
							frappe.msgprint({ title: t("إغلاق", "Closure"), message: `<pre>${esc(JSON.stringify(m, null, 2))}</pre>` });
						},
					});
				});
			} else {
				$body.find(".btn-primary-portal").on("click", () => {
					if (ctx.primary_portal_route) window.location.href = ctx.primary_portal_route;
				});
			}
		}

		render().catch((e) => frappe.msgprint({ title: __("Error"), message: e.message || String(e), indicator: "red" }));
	}

	function boot() {
		start(window.OmnexaFinanceJourney);
	}

	if (window.omnexa_finance && omnexa_finance.ensureJourneyAssets) {
		omnexa_finance.ensureJourneyAssets(boot);
	} else {
		frappe.require(["/assets/omnexa_core/js/finance-portal-factory.js"], () => {
			omnexa_finance.ensureJourneyAssets(boot);
		});
	}
};

/** Legacy route — redirect bookmarks from demo hub */
frappe.pages["finance-demo-hub"] = frappe.pages["finance-demo-hub"] || {};
frappe.pages["finance-demo-hub"].on_page_load = function (wrapper) {
	frappe.set_route("finance-workcenter");
};
