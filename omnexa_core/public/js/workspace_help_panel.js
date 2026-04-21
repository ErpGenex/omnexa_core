// Omnexa: contextual help when opening any Desk workspace — close anytime, toggle auto-open, search tips, open global search.
(function () {
	const LS_AUTO = "omnexa_wh_auto_open";

	const TIPS = [
		{
			id: "awesome",
			t: "البحث السريع (شريط الأوامر) / Awesome Bar",
			k: "search awesome bar keyboard filter list",
			b: "اضغط / أو Ctrl+K لفتح البحث، ثم اكتب اسم النموذج أو الصفحة. Press / or Ctrl+K to open search, then type a DocType or page name.",
		},
		{
			id: "sidebar",
			t: "القائمة الجانبية / Sidebar",
			k: "sidebar menu workspace links",
			b: "من الجانب تختار مساحة العمل أو التوسيع لرؤية الاختصارات. Use the sidebar to switch workspaces or expand items for shortcuts.",
		},
		{
			id: "list",
			t: "قوائم السجلات / List views",
			k: "list filter sort export print assign tag",
			b: "من القائمة: تصفية، ترتيب، أعمدة، تصدير، طباعة، إسناد، وسوم. In lists: filter, sort, columns, export, print, assign, and tags.",
		},
		{
			id: "form",
			t: "النماذج (إنشاء وتعديل) / Forms",
			k: "form save submit cancel amend duplicate attach comment timeline",
			b: "احفظ، أرسل إن وُجد سير عمل، ألغِ، أو عدّل حسب صلاحياتك. المرفقات والتعليقات في الأسفل. Save, workflow actions, cancel, or amend per your role. Attachments and comments below.",
		},
		{
			id: "workspace",
			t: "مساحات العمل / Workspaces",
			k: "workspace cards shortcuts dashboard",
			b: "كل مساحة تجمع روابط واختصارات لمجال عمل. Each workspace groups links and shortcuts for one business area.",
		},
		{
			id: "report",
			t: "التقارير / Reports",
			k: "report query builder chart",
			b: "افتح التقرير من الاختصار أو القائمة، وعدّل المرشحات ثم حدّث. Open a report from a shortcut or menu, set filters, then refresh.",
		},
		{
			id: "help",
			t: "مقالات المساعدة / Help articles",
			k: "help article documentation",
			b: "إن فعّل المسؤول «مقالات المساعدة» ستجدها من القائمة أو البحث. If Help Article is enabled, find it from the menu or search.",
		},
		{
			id: "rtl",
			t: "اللغة والاتجاه / Language",
			k: "rtl arabic english translate",
			b: "يمكن تغيير لغة الواجهة من ملف المستخدم. Interface language is set in your user profile.",
		},
	];

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

	function read_ls(key, def) {
		try {
			const v = localStorage.getItem(key);
			if (v === null || v === undefined) return def;
			return v;
		} catch (e) {
			return def;
		}
	}

	class OmnexaWorkspaceHelpPanel {
		constructor() {
			this.$root = null;
			this.$fab = null;
			this.$panel = null;
			this.$backdrop = null;
			this.$search = null;
			this.$tips = null;
			this.$cbAuto = null;
			this.open = false;
			this._rtl = false;
			this._last_workspace_key = null;
			this._open_timer = null;
		}

		init() {
			this._rtl = Boolean(frappe.utils && frappe.utils.is_rtl && frappe.utils.is_rtl());
			this.ensure_dom();
			frappe.router.on("change", () => this.on_route_change());
			this.on_route_change();
		}

		ensure_dom() {
			if (this.$root) return;
			this.$root = $('<div class="omnexa-wh-root"></div>').appendTo("body");
			if (this._rtl) this.$root.addClass("omnexa-wh--rtl");

			this.$fab = $(`
				<button type="button" class="omnexa-wh-fab" title="${__("Help for this workspace")}" aria-label="${__("Help")}">
					<span class="fa fa-question" style="font-size:1.1rem"></span>
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
							<span>${__("Do not open this panel automatically when I enter a workspace")}</span>
						</label>
						<div class="mt-2">
							<button type="button" class="btn btn-xs btn-default omnexa-wh-open-search">${__(
								"Open global search ( / )"
							)}</button>
						</div>
					</div>
				</div>
			`).appendTo(this.$root);

			this.$panel.find(".omnexa-wh-panel__close").on("click", () => {
				if (this._open_timer) clearTimeout(this._open_timer);
				this._open_timer = null;
				this.toggle_panel(false);
			});
			this.$search = this.$panel.find(".omnexa-wh-panel__search");
			this.$search.on("input", () => this.filter_tips());
			this.$tips = this.$panel.find(".omnexa-wh-tips");
			this.$cbAuto = this.$panel.find(".omnexa-wh-cb-auto");
			this.$cbAuto.on("change", () => {
				// checked = user does NOT want auto-open → store "0"
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

		on_route_change() {
			if (!this.$root) return;

			if (!is_workspace_route()) {
				this._last_workspace_key = null;
				this.$fab.hide();
				this.toggle_panel(false);
				return;
			}

			this.$fab.show();
			const title = workspace_title();
			const label = title ? __(title) : __("Workspace");
			this.$panel.find(".omnexa-wh-panel__title-text").text(__("How to use this area"));
			this.$panel.find(".omnexa-wh-panel__subtitle").text(`${__("Current workspace")}: ${label}`);

			this.$cbAuto.prop("checked", !this.auto_open_enabled());

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
		}

		toggle_panel(show) {
			this.open = Boolean(show);
			this.$panel.toggleClass("omnexa-wh-panel--open", this.open);
			this.$backdrop.toggleClass("omnexa-wh-backdrop--open", this.open);
			if (this.open) {
				this.$search.val("");
				this.filter_tips();
				setTimeout(() => this.$search.trigger("focus"), 100);
			}
		}

		render_tips() {
			this.$tips.empty();
			TIPS.forEach((tip) => {
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
				const tip = TIPS.find((t) => t.id === id);
				if (!tip) return;
				const hay = (tip.t + " " + tip.k + " " + tip.b).toLowerCase();
				const ok = !q || hay.includes(q);
				$el.toggleClass("omnexa-wh-tip--hidden", !ok);
			});
		}
	}

	frappe.ready(() => {
		if (!frappe.boot || frappe.session.user === "Guest") return;
		frappe.provide("omnexa_workspace_help");
		const p = new OmnexaWorkspaceHelpPanel();
		p.init();
		frappe.omnexa_workspace_help = p;
	});
})();
