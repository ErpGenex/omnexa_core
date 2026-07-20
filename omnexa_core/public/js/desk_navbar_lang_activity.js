/* global frappe */
// Desk navbar: business activity badge beside language switch; updates when company changes.

(function () {
	"use strict";

	const LANG_NAV_ID = "oj-navbar-lang-switch";
	const ACTIVITY_ID = "omnexa-navbar-activity";

	let companyActivities = {};

	function currentLang() {
		const bootLang = frappe.boot && frappe.boot.lang;
		if (bootLang === "ar" || bootLang === "en") return bootLang;
		return document.documentElement.lang === "ar" ? "ar" : "en";
	}

	function switchLanguage(langCode) {
		if (!langCode || langCode === currentLang()) return;
		frappe.call({
			method: "frappe.client.set_value",
			args: {
				doctype: "User",
				name: frappe.session.user,
				fieldname: "language",
				value: langCode,
			},
			callback() {
				window.location.reload();
			},
		});
	}

	function langMenuHtml() {
		const lang = currentLang();
		return `<li class="nav-item dropdown dropdown-navbar-lang dropdown-mobile d-none d-lg-block" id="${LANG_NAV_ID}">
			<button
				type="button"
				class="btn-reset nav-link"
				data-toggle="dropdown"
				aria-controls="oj-toolbar-lang"
				aria-label="${frappe.utils.escape_html(__("Language"))}"
				title="${frappe.utils.escape_html(__("Language"))}"
			>
				<svg class="es-icon icon-sm" aria-hidden="true"><use href="#es-line-globe"></use></svg>
			</button>
			<div class="dropdown-menu dropdown-menu-right" id="oj-toolbar-lang" role="menu">
				<button type="button" class="btn-reset dropdown-item ${lang === "ar" ? "active" : ""}" data-oj-lang="ar" role="menuitem">
					<span class="oj-lang-flag" aria-hidden="true">🇸🇦</span> ${frappe.utils.escape_html(__("Arabic"))}
				</button>
				<button type="button" class="btn-reset dropdown-item ${lang === "en" ? "active" : ""}" data-oj-lang="en" role="menuitem">
					<span class="oj-lang-flag" aria-hidden="true">🇬🇧</span> English
				</button>
			</div>
		</li>`;
	}

	function activityBadgeHtml(label) {
		const text = (label || "").trim();
		const hidden = text ? "" : " is-empty";
		return `<li class="nav-item d-none d-lg-flex align-items-center omnexa-navbar-activity${hidden}" id="${ACTIVITY_ID}" title="${frappe.utils.escape_html(__("Business Activity"))}">
			<span class="omnexa-activity-pill">${frappe.utils.escape_html(text)}</span>
		</li>`;
	}

	function bindLangMenu($li) {
		$li.find("[data-oj-lang]").on("click", function (e) {
			e.preventDefault();
			e.stopPropagation();
			switchLanguage($(this).attr("data-oj-lang"));
		});
	}

	function resolveCompany() {
		const ctx = (frappe.boot && frappe.boot.omnexa_view_context) || {};
		if (ctx.company) return ctx.company;
		return (
			frappe.defaults.get_user_default("company") ||
			frappe.defaults.get_user_default("Company") ||
			""
		);
	}

	function updateActivityBadge(company) {
		const co = company || resolveCompany();
		const $badge = $(`#${ACTIVITY_ID}`);
		if (!$badge.length) return;

		let label = "";
		if (co && companyActivities[co]) {
			label = companyActivities[co].label || companyActivities[co].activity || "";
		} else if (co && frappe.boot.omnexa_view_context && frappe.boot.omnexa_view_context.company === co) {
			label = frappe.boot.omnexa_view_context.activity_label || "";
		}

		if (!label && co) {
			frappe.call({
				method: "omnexa_core.omnexa_core.activity_labels.get_company_activity_info_api",
				args: { company: co },
				async: false,
				callback(r) {
					if (r.message) {
						companyActivities[co] = r.message;
						label = r.message.label || r.message.activity || "";
					}
				},
			});
		}

		$badge.find(".omnexa-activity-pill").text(label || "");
		$badge.toggleClass("is-empty", !label);
	}

	function injectNavbarExtras(tries) {
		if (document.getElementById(LANG_NAV_ID)) {
			updateActivityBadge();
			return;
		}
		const helpLi = document.querySelector("li.dropdown-help");
		if (!helpLi || !helpLi.parentElement) {
			if ((tries || 0) > 40) return;
			setTimeout(() => injectNavbarExtras((tries || 0) + 1), 250);
			return;
		}

		const $activity = $(activityBadgeHtml(""));
		const $lang = $(langMenuHtml());
		bindLangMenu($lang);
		helpLi.parentElement.insertBefore($activity.get(0), helpLi);
		helpLi.parentElement.insertBefore($lang.get(0), helpLi);
		updateActivityBadge();
	}

	function loadActivities(callback) {
		frappe.call({
			method: "omnexa_core.omnexa_core.session_context.get_view_context_options",
			callback(r) {
				if (r.message && r.message.company_activities) {
					companyActivities = r.message.company_activities;
				}
				if (typeof callback === "function") callback();
			},
		});
	}

	window.omnexaUpdateActivityBadge = updateActivityBadge;
	window.omnexaSetCompanyActivities = function (map) {
		if (map && typeof map === "object") {
			companyActivities = map;
		}
		updateActivityBadge();
	};

	function init() {
		if (!window.frappe || frappe.session.user === "Guest") return;
		loadActivities(() => injectNavbarExtras(0));
		$(document).on("toolbar_setup", () => injectNavbarExtras(0));
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", init);
	} else {
		init();
	}
	$(window).on("load", init);
})();
