frappe.listview_settings["Event Dead Letter"] = {
	onload(listview) {
		listview.page.add_action_item(__("Reprocess Selected"), async () => {
			const checked = listview.get_checked_items() || [];
			if (!checked.length) {
				frappe.msgprint(__("Select at least one dead letter row."));
				return;
			}

			const names = checked.map((row) => row.name).filter(Boolean);
			if (!names.length) {
				frappe.msgprint(__("No valid dead letter names found."));
				return;
			}

			const doDelete = await new Promise((resolve) => {
				frappe.confirm(
					__(
						"Reprocess {0} selected dead letters?\nChoose OK to reprocess and keep rows.\nUse 'Reprocess + Delete' action below if you want cleanup.",
						[names.length]
					),
					() => resolve(false),
					() => resolve(null)
				);
			});
			if (doDelete === null) return;

			const resp = await frappe.call({
				method: "omnexa_core.omnexa_core.event_dispatcher.reprocess_dead_letter_names",
				args: {
					names_json: JSON.stringify(names),
					delete_on_success: 0,
				},
				freeze: true,
				freeze_message: __("Reprocessing dead letters..."),
			});

			const out = resp.message || {};
			frappe.msgprint(
				__("Reprocess done. OK: {0}, Failed: {1}", [out.ok || 0, out.failed || 0])
			);
			listview.refresh();
		});

		listview.page.add_action_item(__("Reprocess + Delete Selected"), async () => {
			const checked = listview.get_checked_items() || [];
			if (!checked.length) {
				frappe.msgprint(__("Select at least one dead letter row."));
				return;
			}
			const names = checked.map((row) => row.name).filter(Boolean);
			if (!names.length) {
				frappe.msgprint(__("No valid dead letter names found."));
				return;
			}

			frappe.confirm(
				__("Reprocess and delete successful rows for {0} items?", [names.length]),
				async () => {
					const resp = await frappe.call({
						method: "omnexa_core.omnexa_core.event_dispatcher.reprocess_dead_letter_names",
						args: {
							names_json: JSON.stringify(names),
							delete_on_success: 1,
						},
						freeze: true,
						freeze_message: __("Reprocessing and cleaning dead letters..."),
					});

					const out = resp.message || {};
					frappe.msgprint(
						__("Reprocess done. OK: {0}, Failed: {1}", [out.ok || 0, out.failed || 0])
					);
					listview.refresh();
				}
			);
		});
	},
};
