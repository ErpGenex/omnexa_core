// Omnexa User Assistant: navbar + workspace/list sidebars + FAB on all Desk screens; contextual tips and search.
(function () {
	const LS_AUTO = "omnexa_wh_auto_open";
	const BRAND = "👉 User Assistant";

	// Guard against transient null route during desk bootstrap.
	// Some environments trigger route-change before router state is ready.
	if (window.frappe && typeof frappe.get_route_str === "function" && !frappe.__omnexa_safe_route_str) {
		frappe.__omnexa_safe_route_str = true;
		frappe.get_route_str = function () {
			const r = frappe.get_route && frappe.get_route();
			return Array.isArray(r) ? r.join("/") : "";
		};
	}

	function base_tips() {
		return [
			{
				id: "context",
				t: "الشاشة الحالية / Current screen",
				k: "route list form workspace report screen",
				b: "يتغير السطر أعلى اللوحة حسب مكانك في النظام (قائمة، نموذج، مساحة عمل، …). The line above updates based on where you are.",
				d: "هذا يضمن أن الشرح يتبدل تلقائيًا حسب الشاشة الفعلية التي تعمل عليها الآن.",
			},
			{
				id: "awesome",
				t: "البحث السريع (شريط الأوامر) / Awesome Bar",
				k: "search awesome bar keyboard filter list",
				b: "اضغط / أو Ctrl+G لفتح البحث، ثم اكتب اسم النموذج أو الأمر. Press / or Ctrl+G, then type a DocType or command.",
				d: "اكتب جزءًا من اسم الشاشة أو العملية ثم اختر من النتائج للتنقل السريع بدون الرجوع للقوائم.",
			},
			{
				id: "help",
				t: "مقالات المساعدة / Help",
				k: "help article documentation",
				b: "إن وُجدت «مقالات المساعدة» ابحث عنها من القائمة أو البحث. Use Help Articles from menu or search if enabled.",
				d: "اضغط على أي عنصر مساعدة لفتح شرحه التفصيلي داخل اللوحة.",
			},
		];
	}

	function tips_for_route() {
		const r = frappe.get_route() || [];
		const head = [];
		const doctypeName = r[1] || __("this screen");
		const recordName = r[2] || __("current record");

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
				d: `هذه الشاشة لإدارة سجلات ${doctypeName} بسرعة، وليست للتفاصيل الداخلية لسجل واحد.`,
				steps: [
					"ابدأ بإضافة فلتر لتحديد السجلات المطلوبة فقط.",
					"استخدم Sort للترتيب حسب التاريخ أو الحالة.",
					"اختر عدة سجلات ثم نفذ الإجراء الجماعي المناسب.",
					"استخدم Export عند الحاجة لمراجعة خارج النظام.",
				],
			});
			head.push({
				id: "list-create",
				t: "إنشاء سجل جديد من القائمة",
				k: "list new add create",
				b: `لإضافة ${doctypeName} جديد: اضغط New ثم املأ الحقول المطلوبة ثم اضغط Save.`,
				d: "إذا لم يظهر زر New فغالبًا لا توجد صلاحية إنشاء (Create) لهذا المستخدم.",
				steps: [
					"اضغط زر New.",
					"املأ الحقول الإلزامية أولًا (التي تظهر بعلامة إلزامية).",
					"أكمل الحقول الأساسية مثل الاسم/التصنيف/السعر حسب نوع البيانات.",
					"اضغط Save لحفظ السجل.",
				],
			});
			head.push({
				id: "list-edit-delete",
				t: "التعديل والحذف من القائمة (مع الشروط)",
				k: "edit delete permission submitted cancel amend list",
				b: "يمكن فتح أي سجل للتعديل، ويمكن الحذف فقط إذا الحالة تسمح والصلاحية متاحة.",
				d: "بعض السجلات المعتمدة (Submitted) لا تُحذف مباشرة، وقد تحتاج Cancel ثم تعديل أو إنشاء نسخة.",
				steps: [
					"للتعديل: افتح السجل المطلوب ثم عدل الحقول واضغط Save.",
					"للحذف: من القائمة أو داخل السجل اختر Delete إذا كان الزر متاحًا.",
					"إذا لم يظهر Delete: السبب غالبًا صلاحيات، أو أن السجل مرتبط بقيود أخرى.",
					"في المستندات المعتمدة: قد يلزم Cancel أولًا حسب قواعد النشاط.",
				],
			});
		} else if (r[0] === "Form") {
			head.push({
				id: "form",
				t: "نموذج / Form",
				k: "save submit workflow attachments comments timeline",
				b: `أنت داخل نموذج ${doctypeName}. احفظ أولاً، ثم نفّذ إجراءات سير العمل حسب صلاحيتك.`,
				d: "هذا هو المكان الأساسي للإضافة والتعديل والمراجعة والاعتماد.",
				steps: [
					"املأ الحقول الإلزامية أولًا.",
					"اضغط Save لحفظ المسودة.",
					"راجع الأخطاء الظاهرة أعلى النموذج إن وجدت.",
					"بعد التحقق، نفذ Submit أو إجراء Workflow المناسب.",
				],
			});
			head.push({
				id: "form-beginner-guide",
				t: "شرح مبسط للمستخدم الجديد",
				k: "beginner how to add edit delete simple guide",
				b: `لإضافة سجل جديد: New -> املأ النموذج -> Save. للتعديل: افتح ${recordName} -> عدّل -> Save.`,
				d: "للحذف: افتح السجل ثم Menu/Actions -> Delete (إذا كانت الصلاحية والحالة تسمح).",
				steps: [
					"إضافة: اضغط New ثم أدخل البيانات الأساسية ثم Save.",
					"تعديل: افتح السجل المطلوب، غيّر الحقول، ثم Save.",
					"حذف: استخدم Delete عند الحاجة، وتأكد أن السجل غير معتمد أو غير مرتبط.",
					"لو العملية غير متاحة: راجع الصلاحيات أو حالة المستند.",
				],
			});
			head.push({
				id: "form-attachments",
				t: "المرفقات والتعليقات",
				k: "form attachments comments timeline communication",
				b: "أسفل النموذج تجد المرفقات، التعليقات، وسجل الحركة.",
				d: "استخدم هذه المنطقة لتوثيق المستندات والمراجعات المرتبطة بنفس العملية.",
			});
			head.push({
				id: "form-conditions",
				t: "شروط العمليات (مهم جدًا)",
				k: "conditions permissions docstatus workflow linked records",
				b: "نجاح الإضافة/التعديل/الحذف يعتمد على الصلاحيات، حالة المستند، وسير العمل.",
				d: "إذا ظهر منع للعمليات فغالبًا السبب: صلاحيات غير كافية، أو مستند معتمد، أو ارتباطات محاسبية/مخزنية.",
				steps: [
					"تحقق من حالة المستند: Draft / Submitted / Cancelled.",
					"تحقق من دور المستخدم وصلاحياته (Create/Write/Delete/Submit).",
					"تحقق من الارتباطات: قد يمنع النظام حذف سجل مرتبط بسجلات أخرى.",
					"اتبع Workflow المعتمد بدل التعديل المباشر عندما يكون مطلوبًا.",
				],
			});
		} else if (r[0] === "query-report" || r[0] === "Report") {
			head.push({
				id: "report",
				t: "تقرير / Report",
				k: "filters refresh export chart",
				b: "اضبط المرشحات ثم اضغط تحديث. يمكن التصدير أو عرض الرسم. Set filters then refresh; export or view chart when available.",
				d: "دقة التقرير تعتمد على المرشحات، لذلك تأكد من التاريخ والفرع/الشركة قبل التصدير.",
				steps: [
					"حدد نطاق التاريخ والمرشحات الأساسية.",
					"اضغط Refresh لتحديث البيانات.",
					"راجع النتائج ثم استخدم Export إذا أردت مشاركة التقرير.",
				],
			});
		} else {
			head.push({
				id: "desk",
				t: "داخل النظام / Desk",
				k: "search navigate shortcuts",
				b: "استخدم زر الشريط العلوي بجانب Help لفتح المساعد في أي وقت. Use the topbar button next to Help to open the assistant anytime.",
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

	function safe_route_parts() {
		const r = frappe.get_route();
		return Array.isArray(r) ? r : [];
	}

	function safe_route_str() {
		const parts = safe_route_parts();
		return parts.length ? parts.join("/") : "";
	}

	function route_context_line() {
		const r = safe_route_parts();
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
		return safe_route_str() || __("Desk");
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
			this.$panel = null;
			this.$backdrop = null;
			this.$search = null;
			this.$tips = null;
			this.$context = null;
			this.$cbAuto = null;
			this._tips = [];
			this._db_tips = [];
			this.open = false;
			this.panelSize = "normal";
			this._rtl = false;
			this._last_workspace_key = null;
			this._open_timer = null;
			this._load_seq = 0;
		}

		init() {
			this._rtl = Boolean(frappe.utils && frappe.utils.is_rtl && frappe.utils.is_rtl());
			this.ensure_dom();
			frappe.router.on("change", () => this.on_route_change());
			$(document).on("toolbar_setup", () => this.inject_navbar_button());
			$(document).on("page-change", () => this.on_route_change());
			this.inject_navbar_button();
			this.on_route_change();
		}

		open_panel() {
			this.toggle_panel(true);
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
						<span class="fa fa-question-circle" style="margin-inline-end:6px"></span>
						<span class="d-none d-xl-inline text-nowrap">${BRAND}</span>
					</button>
				</li>
			`);
			$li.find("button").on("click", () => this.toggle_panel(true));
			$helpLi.before($li);
		}

		ensure_dom() {
			if (this.$root) return;
			this.$root = $('<div class="omnexa-wh-root"></div>').appendTo("body");
			if (this._rtl) this.$root.addClass("omnexa-wh--rtl");

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
						<div class="omnexa-wh-panel__head-actions">
							<button type="button" class="omnexa-wh-panel__resize" aria-label="${__("Resize")}">
								<span class="fa fa-expand"></span>
							</button>
							<button type="button" class="omnexa-wh-panel__close" aria-label="${__("Close")}">&times;</button>
						</div>
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
			this.$panel.find(".omnexa-wh-panel__resize").on("click", () => this.toggle_size());
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
						"Dynamic guidance for this screen: click any card to open full details and steps."
					)
				);
		}

		collect_dynamic_tips() {
			const out = [];
			try {
				const actionTexts = [];
				$(".page-head .btn:visible, .layout-main-section .btn:visible, .form-page .btn:visible")
					.slice(0, 10)
					.each(function () {
						const txt = ($(this).text() || "").replace(/\s+/g, " ").trim();
						if (!txt || txt.length < 2) return;
						if (actionTexts.includes(txt)) return;
						actionTexts.push(txt);
					});

				if (actionTexts.length) {
					out.push({
						id: "dynamic-actions",
						t: "العمليات المتاحة الآن / Available actions now",
						k: "current screen actions buttons workflow operations",
						b: "تم استخراج الأزرار والعمليات الظاهرة حاليًا من نفس الشاشة.",
						d: "هذه القائمة تتغير تلقائيًا حسب الشاشة والصلاحيات، لذلك المعلومات ليست ثابتة.",
						steps: actionTexts.slice(0, 8).map((a) => `إجراء متاح الآن: ${a}`),
					});
				}
			} catch (e) {
				// ignore dynamic extraction errors
			}

			try {
				if (window.cur_frm && cur_frm.meta && Array.isArray(cur_frm.meta.fields)) {
					const reqd = cur_frm.meta.fields
						.filter((f) => f && f.reqd && f.label)
						.slice(0, 8)
						.map((f) => f.label);
					if (reqd.length) {
						out.push({
							id: "dynamic-required",
							t: "الحقول الإلزامية / Required fields",
							k: "mandatory required fields form validation",
							b: "هذه الحقول يجب تعبئتها قبل الحفظ/الاعتماد.",
							d: "تم التقاطها من تعريف النموذج الحالي مباشرة.",
							steps: reqd.map((label) => `حقل إلزامي: ${label}`),
						});
					}
				}
			} catch (e) {
				// ignore form metadata errors
			}

			return out;
		}

		current_context_args() {
			const r = safe_route_parts();
			const map = {
				Workspaces: "Workspace",
				List: "List",
				Form: "Form",
				Report: "Report",
				"query-report": "Report",
			};
			return {
				context_type: map[r[0]] || "Desk",
				reference_doctype: r[1] || "",
				workspace_name: r[0] === "Workspaces" ? (r[1] === "private" ? r[2] || "" : r[1] || "") : "",
				route_str: safe_route_str(),
			};
		}

		current_tips() {
			return tips_for_route().concat(this.collect_dynamic_tips(), this._db_tips || []);
		}

		async load_db_tips() {
			if (!window.frappe || typeof frappe.call !== "function") {
				this._db_tips = [];
				return;
			}

			const seq = ++this._load_seq;
			try {
				const args = this.current_context_args();
				const res = await frappe.call({
					method: "omnexa_user_academy.api.get_user_assistant_guides",
					args,
					quiet: true,
				});
				if (seq !== this._load_seq) return;
				this._db_tips = Array.isArray(res && res.message) ? res.message : [];
			} catch (e) {
				if (seq !== this._load_seq) return;
				this._db_tips = [];
			}
		}

		async refresh_tips() {
			this._tips = this.current_tips();
			this.render_tips();
			this.apply_smart_panel_size();

			await this.load_db_tips();
			this._tips = this.current_tips();
			this.render_tips();
			this.apply_smart_panel_size();
		}

		compute_content_score() {
			let score = 0;
			(this._tips || []).forEach((tip) => {
				score += (tip.t || "").length;
				score += (tip.b || "").length;
				score += (tip.d || "").length;
				(tip.steps || []).forEach((s) => {
					score += (s || "").length;
				});
			});
			return score;
		}

		apply_smart_panel_size() {
			if (!this.$panel) return;
			const score = this.compute_content_score();
			const manyCards = (this._tips || []).length >= 8;
			const veryLong = score > 2200;
			const long = score > 1200 || manyCards;

			const autoSize = veryLong ? "xl" : long ? "wide" : "normal";
			if (this.panelSize === "normal") {
				this.set_panel_size(autoSize);
			}
		}

		on_route_change() {
			if (!this.$root) return;

			if (!is_desk_app()) {
				this._last_workspace_key = null;
				this.toggle_panel(false);
				return;
			}

			this.update_header();
			this.$cbAuto.prop("checked", !this.auto_open_enabled());

			// refresh tips for current screen (static + dynamic + db guides)
			this.refresh_tips();

			if (is_workspace_route()) {
				const key = safe_route_str();
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
			}
		}

		toggle_panel(show) {
			if (!is_desk_app()) return;
			this.open = Boolean(show);
			this.$panel.toggleClass("omnexa-wh-panel--open", this.open);
			this.$backdrop.toggleClass("omnexa-wh-backdrop--open", this.open);
			if (this.open) {
				this.update_header();
				this.refresh_tips();
				this.$search.val("");
				this.filter_tips();
				setTimeout(() => this.$search.trigger("focus"), 100);
			}
		}

		set_panel_size(size) {
			this.panelSize = size;
			this.$panel.toggleClass("omnexa-wh-panel--wide", size === "wide" || size === "xl");
			this.$panel.toggleClass("omnexa-wh-panel--xl", size === "xl");
			const icon = size === "normal" ? "fa-expand" : "fa-compress";
			this.$panel.find(".omnexa-wh-panel__resize .fa").attr("class", `fa ${icon}`);
		}

		toggle_size() {
			if (this.panelSize === "normal") this.set_panel_size("wide");
			else if (this.panelSize === "wide") this.set_panel_size("xl");
			else this.set_panel_size("normal");
		}

		render_tips() {
			this.$tips.empty();
			(this._tips || []).forEach((tip) => {
				const $t = $(`
					<div class="omnexa-wh-tip" data-id="${tip.id}">
						<button type="button" class="omnexa-wh-tip__head">
							<span class="omnexa-wh-tip__t"></span>
							<span class="omnexa-wh-tip__chev fa fa-angle-down"></span>
						</button>
						<div class="omnexa-wh-tip__b text-muted"></div>
						<div class="omnexa-wh-tip__detail text-muted"></div>
						<ul class="omnexa-wh-tip__steps text-muted"></ul>
					</div>
				`);
				$t.find(".omnexa-wh-tip__t").text(tip.t);
				$t.find(".omnexa-wh-tip__b").text(tip.b);
				$t.find(".omnexa-wh-tip__detail").text(tip.d || "");

				const $steps = $t.find(".omnexa-wh-tip__steps");
				(tip.steps || []).forEach((step) => {
					const $li = $("<li></li>").text(step);
					$steps.append($li);
				});
				if (!(tip.steps || []).length) $steps.hide();
				if (!tip.d) $t.find(".omnexa-wh-tip__detail").hide();

				$t.find(".omnexa-wh-tip__head").on("click", () => {
					const open = $t.hasClass("omnexa-wh-tip--open");
					$t.toggleClass("omnexa-wh-tip--open", !open);
				});

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
				const detailText = tip.d || "";
				const stepsText = (tip.steps || []).join(" ");
				const hay = (tip.t + " " + tip.k + " " + tip.b + " " + detailText + " " + stepsText).toLowerCase();
				const ok = !q || hay.includes(q);
				$el.toggleClass("omnexa-wh-tip--hidden", !ok);
			});
		}
	}

	function mount_user_assistant() {
		if (!window.frappe || !frappe.boot || frappe.session.user === "Guest") return;
		if (window.__omnexa_user_assistant_mounted) return;
		window.__omnexa_user_assistant_mounted = true;
		const p = new OmnexaUserAssistant();
		p.init();
		frappe.omnexa_user_assistant = p;
		frappe.omnexa_workspace_help = p;
		window.omnexaUserAssistant = {
			openPanel: () => p.open_panel(),
			toggle: (show) => p.toggle_panel(show !== false),
		};
	}

	// Robust bootstrap for varying load order in Desk.
	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", mount_user_assistant);
	} else {
		mount_user_assistant();
	}
	$(window).on("load", mount_user_assistant);
})();
