// Omnexa User Assistant: navbar + workspace/list sidebars + FAB on all Desk screens; contextual tips and search.
(function () {
	const LS_AUTO = "omnexa_wh_auto_open";
	const BRAND = "👉 User Assistant";

	function base_tips() {
		return [
			{
				id: "context",
				t: "الشاشة الحالية / Current screen",
				k: "route list form workspace report screen",
				b: "يتغير السطر أعلى اللوحة حسب مكانك في النظام (قائمة، نموذج، مساحة عمل، …). The line above updates based on where you are.",
			},
			{
				id: "awesome",
				t: "البحث السريع (شريط الأوامر) / Awesome Bar",
				k: "search awesome bar keyboard filter list",
				b: "اضغط / أو Ctrl+G لفتح البحث، ثم اكتب اسم النموذج أو الأمر. Press / or Ctrl+G, then type a DocType or command.",
			},
			{
				id: "help",
				t: "مقالات المساعدة / Help",
				k: "help article documentation",
				b: "إن وُجدت «مقالات المساعدة» ابحث عنها من القائمة أو البحث. Use Help Articles from menu or search if enabled.",
			},
		];
	}

	function tips_for_route() {
		const r = frappe.get_route() || [];
		const head = [];

		if (r[0] === "Workspaces") {
			head.push({
				id: "ws",
				t: "مساحة العمل / Workspace",
				k: "workspace shortcuts cards onboarding",
				b: "استخدم الاختصارات والبطاقات للوصول السريع (إنشاء/قوائم/تقارير). Use shortcuts/cards to jump into work (new/list/reports).",
			});
		} else if (r[0] === "List") {
			head.push({
				id: "list",
				t: "قائمة السجلات / List view",
				k: "filter sort columns bulk export print tags assign",
				b: "من الأعلى: الفلاتر/الترتيب/الأعمدة. ومن الإجراءات: تصدير، طباعة، إجراءات جماعية. Use filters/sort/columns, then export/print/bulk actions.",
			});
		} else if (r[0] === "Form") {
			head.push({
				id: "form",
				t: "نموذج / Form",
				k: "save submit workflow attachments comments timeline",
				b: "احفظ أولاً، ثم نفّذ إجراءات سير العمل حسب صلاحيتك. المرفقات/التعليقات/التاريخ بالأسفل. Save first, then workflow actions; attachments/comments/timeline below.",
			});
		} else if (r[0] === "query-report" || r[0] === "Report") {
			head.push({
				id: "report",
				t: "تقرير / Report",
				k: "filters refresh export chart",
				b: "اضبط المرشحات ثم اضغط تحديث. يمكن التصدير أو عرض الرسم. Set filters then refresh; export or view chart when available.",
			});
		} else {
			head.push({
				id: "desk",
				t: "داخل النظام / Desk",
				k: "search navigate shortcuts",
				b: "استخدم الزر العائم أو زر الشريط العلوي لفتح المساعد. Use the floating button or top button to open the assistant anytime.",
			});
		}

		// keep a sidebar tip for discoverability
		head.push({
			id: "sidebar",
			t: "القائمة الجانبية / Sidebar",
			k: "sidebar menu workspace links filters",
			b: "في مساحة العمل: اختصارات ومجموعات. في القوائم: عوامل تصفية وإحصاءات. In workspaces: shortcuts; in lists: filters and stats.",
		});

		return head.concat(base_tips());
	}

	function is_desk_app() {
		return (window.location.pathname || "").indexOf("/app") === 0;
	}

	function is_workspace_route() {
		const r = frappe.get_route() || [];
		return r[0] === "Workspaces" && Boolean(r[1] === "private" ? r[2] : r[1]);
	}

	function workspace_title() {
		const r = frappe.get_route() || [];
		if (r[0] !== "Workspaces") return "";
		if (r[1] === "private") return r[2] || "";
		return r[1] || "";
	}

	function route_context_line() {
		const r = frappe.get_route() || [];
		const g = (s) => frappe.utils.xss_sanitise ? frappe.utils.xss_sanitise(String(s)) : String(s);
		if (r[0] === "Workspaces") {
			const t = workspace_title();
			return t
				? `${__("Workspace")}: ${g(__(t))}`
				: __("Workspace");
		}
		if (r[0] === "List" && r[1]) return `${__("List")}: ${g(r[1])}`;
		if (r[0] === "Form" && r[1]) {
			const doc = r[2] ? ` — ${g(r[2])}` : "";
			return `${__("Form")}: ${g(r[1])}${doc}`;
		}
		if (r[0] === "query-report" && r[1]) return `${__("Report")}: ${g(r[1])}`;
		if (r[0] === "dashboard-view" && r[1]) return `${__("Dashboard")}: ${g(r[1])}`;
		if (r[0] === "Tree" && r[1]) return `${__("Tree")}: ${g(r[1])}`;
		return frappe.get_route_str() || __("Desk");
	}

	function read_ls(key, def) {
		try {
			const v = localStorage.getItem(key);
			if (v === null || v === undefined) return def;
			return v;
		} catch (e) {
			return def;
		}
	}

	class OmnexaUserAssistant {
		constructor() {
			this.$root = null;
			this.$fab = null;
			this.$panel = null;
			this.$backdrop = null;
			this.$search = null;
			this.$tips = null;
			this.$context = null;
			this.$cbAuto = null;
			this._tips = [];
			this.open = false;
			this._rtl = false;
			this._last_workspace_key = null;
			this._open_timer = null;
		}

		init() {
			this._rtl = Boolean(frappe.utils && frappe.utils.is_rtl && frappe.utils.is_rtl());
			this.ensure_dom();
			frappe.router.on("change", () => this.on_route_change());
			$(document).on("toolbar_setup", () => this.inject_navbar_button());
			$(document).on("list_sidebar_setup", () => this.inject_list_sidebar_button());
			$(document).on("page-change", () => this.on_route_change());
			this.inject_navbar_button();
			this.on_route_change();
		}

		open_panel() {
			this.toggle_panel(true);
		}

		ensure_dom() {
			if (this.$root) return;
			this.$root = $('<div class="omnexa-wh-root"></div>').appendTo("body");
			if (this._rtl) this.$root.addClass("omnexa-wh--rtl");

			this.$fab = $(`
				<button type="button" class="omnexa-wh-fab" title="${__(BRAND)}" aria-label="${__(BRAND)}">
					<span class="fa fa-compass" style="font-size:1.15rem"></span>
				</button>
			`).appendTo(this.$root);
			this.$fab.on("click", () => this.toggle_panel(true));

			this.$backdrop = $('<div class="omnexa-wh-backdrop" />').appendTo(this.$root);
			this.$backdrop.on("click", () => {
				if (this._open_timer) clearTimeout(this._open_timer);
				this._open_timer = null;
				this.toggle_panel(false);
			});

			this.$panel = $(`
				<div class="omnexa-wh-panel" role="dialog" aria-modal="true">
					<div class="omnexa-wh-panel__head">
						<div>
							<p class="omnexa-wh-panel__title omnexa-wh-panel__title-text"></p>
							<p class="text-muted small mb-1 omnexa-ua-context"></p>
							<p class="text-muted small mb-0 omnexa-wh-panel__subtitle"></p>
						</div>
						<button type="button" class="omnexa-wh-panel__close" aria-label="${__("Close")}">&times;</button>
					</div>
					<div class="omnexa-wh-panel__body">
						<input type="search" class="form-control input-sm omnexa-wh-panel__search" placeholder="${__(
							"Search help…"
						)}" />
						<div class="omnexa-wh-tips"></div>
					</div>
					<div class="omnexa-wh-panel__foot">
						<label class="d-flex align-items-center gap-2 mb-0">
							<input type="checkbox" class="omnexa-wh-cb-auto" />
							<span>${__("Do not open automatically when I enter a workspace")}</span>
						</label>
						<div class="mt-2">
							<button type="button" class="btn btn-xs btn-default omnexa-wh-open-search">${__(
								"Open global search ( / )"
							)}</button>
						</div>
					</div>
				</div>
			`).appendTo(this.$root);

			this.$panel.find(".omnexa-wh-panel__title-text").text(__(BRAND));

			this.$panel.find(".omnexa-wh-panel__close").on("click", () => {
				if (this._open_timer) clearTimeout(this._open_timer);
				this._open_timer = null;
				this.toggle_panel(false);
			});
			this.$search = this.$panel.find(".omnexa-wh-panel__search");
			this.$search.on("input", () => this.filter_tips());
			this.$tips = this.$panel.find(".omnexa-wh-tips");
			this.$context = this.$panel.find(".omnexa-ua-context");
			this.$cbAuto = this.$panel.find(".omnexa-wh-cb-auto");
			this.$cbAuto.on("change", () => {
				localStorage.setItem(LS_AUTO, this.$cbAuto.prop("checked") ? "0" : "1");
			});

			this.$panel.find(".omnexa-wh-open-search").on("click", () => {
				const el = document.querySelector("#navbar-search");
				if (el) {
					el.focus();
					el.click();
				} else {
					frappe.show_alert({
						message: __("Search bar is not available on this screen."),
						indicator: "orange",
					});
				}
			});

			this.render_tips();
		}

		auto_open_enabled() {
			return read_ls(LS_AUTO, "1") !== "0";
		}

		update_header() {
			const ctx = route_context_line();
			this.$context.text(ctx);
			this.$panel
				.find(".omnexa-wh-panel__subtitle")
				.text(
					__(
						"Search the cards below for how lists, forms, workspaces, and search work — or use global search for any DocType."
					)
				);
		}

		inject_navbar_button() {
			if (!is_desk_app() || $("#omnexa-user-assistant-nav").length) return;
			let $helpLi = $("header .navbar-nav .dropdown-help").closest("li.nav-item");
			if (!$helpLi.length) {
				$helpLi = $("header .navbar-nav .dropdown-navbar-user").closest("li.nav-item");
			}
			if (!$helpLi.length) return;
			const $li = $(`
				<li class="nav-item d-none d-sm-flex align-items-center omnexa-user-assistant-nav-li" id="omnexa-user-assistant-nav">
					<button type="button" class="btn-reset nav-link text-muted omnexa-user-assistant-nav-btn" title="${__(BRAND)}">
						<span class="fa fa-compass" style="margin-inline-end:6px"></span>
						<span class="d-none d-xl-inline text-nowrap">${BRAND}</span>
					</button>
				</li>
			`);
			$li.find("button").on("click", () => this.toggle_panel(true));
			$helpLi.before($li);
		}

		inject_workspace_sidebar_button() {
			$("#body .desk-sidebar .omnexa-ua-workspace-sidebar").remove();
			const $sb = $("#body .desk-sidebar").first();
			if (!$sb.length) return;
			const $wrap = $(`
				<div class="sidebar-item-container omnexa-ua-workspace-sidebar" style="margin-bottom:8px;padding-bottom:8px;border-bottom:1px solid var(--border-color, #e8e8e8);">
					<div class="desk-sidebar-item standard-sidebar-item">
						<button type="button" class="btn-reset item-anchor omnexa-ua-ws-open" style="cursor:pointer;width:100%;text-align:inherit;">
							<span class="sidebar-item-icon"><span class="fa fa-compass" style="font-size:1rem"></span></span>
							<span class="sidebar-item-label">${BRAND}</span>
						</button>
					</div>
				</div>
			`);
			// place at the end of the workspace sidebar list
			$sb.append($wrap);
			$wrap.find(".omnexa-ua-ws-open").on("click", (e) => {
				e.preventDefault();
				this.toggle_panel(true);
			});
		}

		inject_list_sidebar_button() {
			$("#body .list-sidebar .omnexa-ua-list-sidebar").remove();
			const $sb = $("#body .list-sidebar").first();
			if (!$sb.length) return;
			const $b = $(`
				<div class="omnexa-ua-list-sidebar" style="padding:10px 12px;border-bottom:1px solid var(--border-color, #e8e8e8);">
					<button type="button" class="btn btn-default btn-sm btn-block omnexa-ua-list-open text-nowrap" style="overflow:hidden;text-overflow:ellipsis;">
						<span class="fa fa-compass" style="margin-inline-end:6px"></span>${BRAND}
					</button>
				</div>
			`);
			// keep list helpers near top, but after the default header area if any
			$sb.prepend($b);
			$b.find(".omnexa-ua-list-open").on("click", () => this.toggle_panel(true));
		}

		on_route_change() {
			if (!this.$root) return;

			if (!is_desk_app()) {
				this._last_workspace_key = null;
				this.$fab.hide();
				this.toggle_panel(false);
				return;
			}

			this.$fab.show();
			this.update_header();
			this.$cbAuto.prop("checked", !this.auto_open_enabled());

			// refresh tips for current screen
			this._tips = tips_for_route();
			this.render_tips();

			setTimeout(() => {
				this.inject_workspace_sidebar_button();
				this.inject_list_sidebar_button();
			}, 80);

			if (is_workspace_route()) {
				const key = `${frappe.get_route().join("/")}`;
				const changed = key !== this._last_workspace_key;
				this._last_workspace_key = key;

				if (this._open_timer) clearTimeout(this._open_timer);
				this._open_timer = null;

				if (this.auto_open_enabled() && changed) {
					this._open_timer = setTimeout(() => {
						this._open_timer = null;
						if (is_workspace_route()) this.toggle_panel(true);
					}, 350);
				} else if (!this.auto_open_enabled()) {
					this.toggle_panel(false);
				}
			} else {
				this._last_workspace_key = null;
				if (this._open_timer) clearTimeout(this._open_timer);
				this._open_timer = null;
				this.toggle_panel(false);
			}
		}

		toggle_panel(show) {
			if (!is_desk_app()) return;
			this.open = Boolean(show);
			this.$panel.toggleClass("omnexa-wh-panel--open", this.open);
			this.$backdrop.toggleClass("omnexa-wh-backdrop--open", this.open);
			if (this.open) {
				this.update_header();
				this._tips = tips_for_route();
				this.render_tips();
				this.$search.val("");
				this.filter_tips();
				setTimeout(() => this.$search.trigger("focus"), 100);
			}
		}

		render_tips() {
			this.$tips.empty();
			(this._tips || []).forEach((tip) => {
				const $t = $(`
					<div class="omnexa-wh-tip" data-id="${tip.id}">
						<div class="omnexa-wh-tip__t"></div>
						<div class="omnexa-wh-tip__b text-muted"></div>
					</div>
				`);
				$t.find(".omnexa-wh-tip__t").text(tip.t);
				$t.find(".omnexa-wh-tip__b").text(tip.b);
				this.$tips.append($t);
			});
		}

		filter_tips() {
			const q = (this.$search.val() || "").toLowerCase().trim();
			this.$tips.find(".omnexa-wh-tip").each(function () {
				const $el = $(this);
				const id = $el.attr("data-id");
				const tip = (frappe.omnexa_user_assistant && frappe.omnexa_user_assistant._tips
					? frappe.omnexa_user_assistant._tips
					: []
				).find((t) => t.id === id);
				if (!tip) return;
				const hay = (tip.t + " " + tip.k + " " + tip.b).toLowerCase();
				const ok = !q || hay.includes(q);
				$el.toggleClass("omnexa-wh-tip--hidden", !ok);
			});
		}
	}

	frappe.ready(() => {
		if (!frappe.boot || frappe.session.user === "Guest") return;
		const p = new OmnexaUserAssistant();
		p.init();
		frappe.omnexa_user_assistant = p;
		frappe.omnexa_workspace_help = p;
		window.omnexaUserAssistant = {
			openPanel: () => p.open_panel(),
			toggle: (show) => p.toggle_panel(show !== false),
		};
	});
})();
