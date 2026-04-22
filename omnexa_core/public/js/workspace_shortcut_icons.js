// Copyright (c) 2026, Omnexa and contributors
// License: MIT. See license.txt
// Desk: show a leading SVG icon on workspace shortcut tiles (Frappe core stores icon but does not render it).

(function () {
	"use strict";

	function patch_shortcut_icons() {
		const WF = frappe.widget && frappe.widget.widget_factory;
		if (!WF || !WF.shortcut || WF.shortcut.__omnexa_ws_icon_patched) {
			return true;
		}
		const Base = WF.shortcut;

		class ShortcutWithLeadingIcon extends Base {
			set_title(max_chars) {
				let base = this.title || this.label || this.name;
				let title = max_chars ? frappe.ellipsis(base, max_chars) : base;
				const icon_name = this._omnexa_ws_leading_icon();
				const lead = icon_name
					? frappe.utils.icon(icon_name, "sm", "", "", "omnexa-ws-sc-ic")
					: "";
				const esc = frappe.utils.escape_html(__(title));
				this.title_field[0].innerHTML = `${lead}<span class="ellipsis" title="${esc}">${__(title)}</span>`;
				if (max_chars) {
					this.title_field[0].setAttribute("title", this.title || this.label);
				}
				if (this.subtitle) {
					this.subtitle_field.html(this.subtitle);
				}
			}

			_omnexa_ws_leading_icon() {
				if (this.icon) {
					return this.icon;
				}
				const t = (this.type || "").toLowerCase();
				if (t === "report") {
					return "es-line-reports";
				}
				if (t === "url") {
					return "es-line-link";
				}
				if (t === "dashboard") {
					return "es-line-dashboard";
				}
				if (t === "page") {
					return "es-line-filetype";
				}
				return "es-line-filetype";
			}
		}

		Object.defineProperty(ShortcutWithLeadingIcon, "__omnexa_ws_icon_patched", { value: true });
		WF.shortcut = ShortcutWithLeadingIcon;
		return true;
	}

	function try_patch(attempts) {
		if (patch_shortcut_icons()) {
			return;
		}
		if (attempts > 80) {
			return;
		}
		setTimeout(() => try_patch(attempts + 1), 50);
	}

	function mount_workspace_shortcut_icons() {
		if (!window.frappe || !frappe.boot || frappe.session.user === "Guest") return;
		if (window.__workspace_shortcut_icons_mounted) return;
		window.__workspace_shortcut_icons_mounted = true;
		try_patch(0);
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", mount_workspace_shortcut_icons);
	} else {
		mount_workspace_shortcut_icons();
	}
	$(window).on("load", mount_workspace_shortcut_icons);
})();
