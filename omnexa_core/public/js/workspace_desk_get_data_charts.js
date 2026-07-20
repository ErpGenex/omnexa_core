// When a workspace has no Dashboard Chart rows, Frappe's Workspace#get_data returns early and skips
// merging chart_settings — some builds then render an empty main area. Still merge settings (no-op
// on empty items) so shortcuts / number cards / headers render (Omnexa / ERPGENEX).
frappe.ready(() => {
	if (!frappe.views || !frappe.views.Workspace || !frappe.views.Workspace.prototype) {
		return;
	}
	const orig = frappe.views.Workspace.prototype.get_data;
	frappe.views.Workspace.prototype.get_data = function (page) {
		return orig.call(this, page).then((result) => {
			try {
				if (
					this.page_data &&
					this.page_data.charts &&
					Array.isArray(this.page_data.charts.items) &&
					this.page_data.charts.items.length === 0
				) {
					return frappe.dashboard_utils.get_dashboard_settings().then((settings) => {
						if (settings && this.page_data && this.page_data.charts) {
							const chart_config = settings.chart_config
								? JSON.parse(settings.chart_config)
								: {};
							(this.page_data.charts.items || []).forEach((chart) => {
								chart.chart_settings = chart_config[chart.chart_name] || {};
							});
							if (page && this.pages) {
								this.pages[page.name] = this.page_data;
							}
						}
						return result;
					});
				}
			} catch (e) {
				if (console && console.error) {
					console.error("omnexa_core workspace_desk_get_data_charts", e);
				}
			}
			return result;
		});
	};
});
