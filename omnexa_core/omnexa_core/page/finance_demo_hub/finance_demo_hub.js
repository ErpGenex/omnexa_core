frappe.pages["finance-demo-hub"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Finance Demo Hub"),
		single_column: true,
	});

	function t(ar, en) {
		return frappe.boot.lang === "ar" ? ar : en;
	}

	function esc(v) {
		return frappe.utils.escape_html(String(v ?? ""));
	}

	function portalLabel(p) {
		return frappe.boot.lang === "ar" ? p.label_ar : p.label_en;
	}

	function renderPortalCard(p) {
		const disabled = p.exists === false ? " opacity-50" : "";
		const route = p.route || "#";
		return `<div class="col-md-3 mb-3">
			<div class="card finance-demo-portal${disabled}" data-route="${esc(route)}" style="cursor:pointer;min-height:120px">
				<div class="card-body">
					<div style="font-size:1.6rem">${esc(p.icon || "🏦")}</div>
					<strong>${esc(portalLabel(p))}</strong>
					<div class="text-muted small">${esc(p.page)}</div>
				</div>
			</div>
		</div>`;
	}

	async function render() {
		const [creds, groups] = await Promise.all([
			frappe.call({
				method: "omnexa_core.omnexa_core.finance_demo.finance_role_demo.get_finance_demo_credentials",
			}).then((r) => r.message || {}),
			frappe.call({
				method: "omnexa_core.omnexa_core.finance_demo.finance_portal_catalog.get_grouped_portal_catalog",
			}).then((r) => r.message || []),
		]);

		const $body = $(`<div class="finance-demo-hub p-3"></div>`);
		$body.append(`
			<div class="alert alert-info">
				<h5>${t("مركز تجربة المجموعة المالية", "Finance Group Demo Hub")}</h5>
				<p class="mb-0">${t(
					"محاكاة العمل اليومي لأدوار المؤسسات المالية — بوابات · workspaces · حسابات ديمو",
					"Simulate daily work across finance roles — portals · workspaces · demo accounts"
				)}</p>
			</div>
		`);

		$body.append(`
			<div class="card mb-4">
				<div class="card-body">
					<h5>${t("حسابات الديمو", "Demo Accounts")}</h5>
					<p>${t("كلمة المرور", "Password")}: <code>${esc(creds.password)}</code></p>
					<button type="button" class="btn btn-primary btn-seed-roles">${t("زرع أدوار الديمو", "Seed Role Demo")}</button>
					<div class="table-responsive mt-3">
						<table class="table table-bordered table-sm">
							<thead><tr>
								<th>${t("الدور", "Role")}</th>
								<th>${t("البريد", "Email")}</th>
								<th>${t("البوابة", "Portal")}</th>
							</tr></thead>
							<tbody>
								${(creds.users || [])
									.map(
										(u) => `<tr>
									<td>${esc(u.role)}</td>
									<td><code>${esc(u.email)}</code></td>
									<td><a href="${esc(u.route)}">${esc(u.route)}</a></td>
								</tr>`
									)
									.join("")}
							</tbody>
						</table>
					</div>
				</div>
			</div>
		`);

		(groups || []).forEach((g) => {
			const title = frappe.boot.lang === "ar" ? g.label_ar : g.label_en;
			$body.append(`<h5 class="mt-4">${esc(title)}</h5><div class="row">`);
			const $row = $('<div class="row"></div>');
			(g.portals || []).forEach((p) => $row.append(renderPortalCard(p)));
			$body.append($row);
		});

		$(page.body).empty().append($body);

		$body.find(".finance-demo-portal").on("click", function () {
			const route = $(this).data("route");
			if (route && route !== "#") frappe.set_route(route.replace(/^\/app\//, ""));
		});

		$body.find(".btn-seed-roles").on("click", () => {
			frappe.confirm(
				t("سيتم إنشاء workspaces ومستخدمي الديمو. متابعة؟", "This will create demo workspaces and users. Continue?"),
				() => {
					frappe.call({
						method: "omnexa_core.omnexa_core.finance_demo.finance_role_demo.seed_finance_role_demo",
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
	}

	render().catch((e) => frappe.msgprint({ title: __("Error"), message: e.message || String(e), indicator: "red" }));
};
