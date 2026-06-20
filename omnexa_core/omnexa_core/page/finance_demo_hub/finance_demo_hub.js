frappe.pages["finance-demo-hub"].on_page_load = function (wrapper) {
	function start(OJ) {
		const $mount = OJ.mountDeskPage(wrapper, __("Finance Demo Hub"));

		function t(ar, en) {
			return OJ.t(ar, en);
		}

		function esc(v) {
			return OJ.esc(v);
		}

		async function render() {
			const [creds, groups, defaults] = await Promise.all([
				OJ.call("omnexa_core.omnexa_core.finance_demo.finance_role_demo.get_finance_demo_credentials"),
				OJ.call("omnexa_core.omnexa_core.finance_demo.finance_portal_catalog.get_grouped_portal_catalog"),
				OJ.call("omnexa_core.omnexa_core.finance_demo.finance_role_demo.get_finance_demo_defaults"),
			]);

			const companyOpts = (defaults.companies || [])
				.map((c) => `<option value="${esc(c.name)}" ${c.name === defaults.default_company ? "selected" : ""}>${esc(c.name)}</option>`)
				.join("");
			const branchOpts = (defaults.branches || [])
				.map(
					(b) =>
						`<option value="${esc(b.name)}" data-company="${esc(b.company)}" ${b.name === defaults.default_branch ? "selected" : ""}>${esc(b.name)}</option>`
				)
				.join("");

			const $demoPanel = $(`<div class="oj-demo-panel finance-demo-hub-journey"></div>`);
			$demoPanel.append(`
			<h4>${t("مركز تجربة المجموعة المالية", "Finance Group Demo Hub")}</h4>
			<p class="oj-muted">${t(
				"محاكاة واقعية لجميع أدوار المجموعة المالية — بوابات Journey · workspaces · حسابات ديمو",
				"Full finance role simulation — Journey portals · workspaces · demo accounts"
			)}</p>
			<p>${t("كلمة المرور", "Password")}: <code>${esc(creds.password)}</code></p>
			<div class="row mb-3">
				<div class="col-md-4">
					<label class="small oj-muted">${t("الشركة", "Company")}</label>
					<select class="form-control demo-company">${companyOpts}</select>
				</div>
				<div class="col-md-4">
					<label class="small oj-muted">${t("الفرع", "Branch")}</label>
					<select class="form-control demo-branch">${branchOpts}</select>
				</div>
			</div>
			<button type="button" class="oj-btn oj-btn-primary btn-seed-roles">${t("زرع أدوار الديمو", "Seed Role Demo")}</button>
			<button type="button" class="oj-btn oj-btn-secondary btn-seed-all ml-2">${t("زرع Workflow + بيانات كل التطبيقات", "Seed All Verticals (BPE)")}</button>
			<button type="button" class="oj-btn oj-btn-success btn-run-closure ml-2">${t("إغلاق كامل — Global #1", "Full Closure — Global #1")}</button>
			<p class="oj-muted small mt-2">${t("التوثيق الموحد", "Unified docs")}: <code>Docs/ERPGENEX_BANKING_FINANCIAL_GROUP_MASTER</code></p>
		`);

			const $usersTable = OJ.dataTable(
				[
					{ field: "role", label: t("الدور", "Role") },
					{ field: "email", label: t("البريد", "Email") },
					{ field: "route", label: t("البوابة", "Portal") },
				],
				(creds.users || []).map((u) => ({
					role: u.role,
					email: u.email,
					route: u.route,
				}))
			);
			$demoPanel.append(`<h5 class="oj-section-title">${t("حسابات الديمو", "Demo Accounts")}</h5>`);
			$demoPanel.append($usersTable);

			const $portalRoot = OJ.portalCategoryGrid(groups);

			const $body = $("<div class='finance-demo-hub-journey'></div>");
			$body.append($demoPanel);
			$body.append(`<h4 class="oj-section-title">${t("بوابات Journey حسب التطبيق", "Journey portals by application")}</h4>`);
			$body.append($portalRoot);

			const $shell = OJ.shell({
				title: t("Finance Demo Hub", "Finance Demo Hub"),
				subtitle: t("ErpGenEx — Finance Group", "ErpGenEx — Finance Group"),
				role: t("مدير النظام", "System Manager"),
				sidebar: OJ.defaultSidebar("executive", "/app/finance-demo-hub"),
				bodyEl: $body,
			});

			$mount.empty().append($shell);
			if (window.omnexa_finance && omnexa_finance.dismissOnboardingDialog) {
				omnexa_finance.dismissOnboardingDialog();
			}

			$body.find(".demo-company").on("change", function () {
				const company = $(this).val();
				const $branch = $body.find(".demo-branch");
				$branch.find("option").each(function () {
					const match = !company || $(this).data("company") === company;
					$(this).toggle(match);
				});
				const first = $branch.find("option:visible:first").val();
				if (first) $branch.val(first);
			});

			$body.find(".btn-seed-roles").on("click", () => {
				const company = $body.find(".demo-company").val();
				const branch = $body.find(".demo-branch").val();
				frappe.confirm(
					t("سيتم إنشاء workspaces ومستخدمي الديمو. متابعة؟", "This will create demo workspaces and users. Continue?"),
					() => {
						frappe.call({
							method: "omnexa_core.omnexa_core.finance_demo.finance_role_demo.seed_finance_role_demo",
							args: { company, branch },
							freeze: true,
							callback(r) {
								frappe.show_alert({ message: t("تم", "Done"), indicator: "green" });
								if (r.message && r.message.message) frappe.msgprint(r.message.message);
								render();
							},
						});
					}
				);
			});

			$body.find(".btn-seed-all").on("click", () => {
				const company = $body.find(".demo-company").val();
				const branch = $body.find(".demo-branch").val();
				frappe.confirm(
					t(
						"سيتم مزامنة Workflow + SoD + زرع 7 حالات ديمو لكل تطبيق مالي. متابعة؟",
						"Sync workflow/SoD and seed demo cases for all finance apps. Continue?"
					),
					() => {
						frappe.call({
							method: "omnexa_core.omnexa_core.finance_demo.finance_vertical_bpe.seed_all_finance_vertical_demos",
							args: { company, branch },
							freeze: true,
							callback(r) {
								frappe.show_alert({ message: t("تم زرع كل التطبيقات", "All verticals seeded"), indicator: "green" });
								if (r.message && r.message.seeds) {
									const n = (r.message.seeds || []).reduce((a, s) => a + (s.count || 0), 0);
									frappe.msgprint(t("تم إنشاء", "Created") + ` ${n} ` + t("سجل ديمو", "demo records"));
								}
								render();
							},
						});
					}
				);
			});

			$body.find(".btn-run-closure").on("click", () => {
				const company = $body.find(".demo-company").val();
				const branch = $body.find(".demo-branch").val();
				frappe.confirm(
					t(
						"إغلاق كامل: أدوار + Workflow + Demo + Smoke + Benchmark + Global #1. متابعة؟",
						"Full closure: roles + workflow + demo + smoke + benchmark. Continue?"
					),
					() => {
						frappe.call({
							method: "omnexa_core.omnexa_core.finance_demo.finance_group_master.run_full_finance_group_closure",
							args: { company, branch },
							freeze: true,
							callback(r) {
								const m = r.message || {};
								const score = m.weighted_score || "—";
								const ok = m.all_closed ? "green" : "orange";
								frappe.show_alert({
									message: t("النتيجة", "Score") + `: ${score} · Global #1: ${m.global_number_one ? "✓" : "—"}`,
									indicator: ok,
								});
								frappe.msgprint({
									title: t("إغلاق المجموعة المالية", "Finance Group Closure"),
									message: `<pre>${esc(JSON.stringify(m, null, 2))}</pre>`,
									indicator: ok,
								});
								render();
							},
						});
					}
				);
			});
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
