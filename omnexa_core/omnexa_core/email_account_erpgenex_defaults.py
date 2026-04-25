# Copyright (c) 2026, ErpGenEx and contributors
# SPDX-License-Identifier: MIT
"""Apply transport defaults for mail.erpgenex.com (IMAP 993 SSL + SMTP 465 SSL).

Password is **not** stored here. Run after setting the mailbox password in Desk::

    bench --site <site> execute omnexa_core.omnexa_core.email_account_erpgenex_defaults.apply_erpgenex_mail_transport_defaults

Optional kwargs: ``{"email_account_name": "ERPGENEX"}``

Uses ``frappe.db.set_value`` (not ``doc.save``): if **Email Account** has **Domain**
set, Frappe's ``fetch_from`` overwrites ``use_imap`` / ``use_ssl`` from that
domain on save, which kept IMAP disabled. This helper clears **domain** so
incoming settings are standalone; use Desk **Test connection** after running.
"""

from __future__ import annotations

from typing import Any

import frappe

_IMAP_HOST = "mail.erpgenex.com"
_IMAP_PORT = 993
_SMTP_HOST = "mail.erpgenex.com"
_SMTP_PORT = 465


@frappe.whitelist()
def apply_erpgenex_mail_transport_defaults(email_account_name: str = "ERPGENEX") -> dict[str, Any]:
	frappe.only_for("System Manager")

	if not frappe.db.exists("Email Account", email_account_name):
		frappe.throw(frappe._("Email Account {0} not found").format(frappe.bold(email_account_name)))

	# Only one default outgoing account
	for other in frappe.get_all("Email Account", filters={"default_outgoing": 1}, pluck="name"):
		if other != email_account_name:
			frappe.db.set_value("Email Account", other, "default_outgoing", 0, update_modified=False)

	updates: dict[str, Any] = {
		# Clear link so fetch_from (domain.use_imap / domain.use_ssl) does not reset IMAP on save
		"domain": None,
		"email_server": _IMAP_HOST,
		"use_imap": 1,
		"use_ssl": 1,
		"incoming_port": str(_IMAP_PORT),
		"enable_incoming": 1,
		"smtp_server": _SMTP_HOST,
		"smtp_port": str(_SMTP_PORT),
		"use_tls": 0,
		"use_ssl_for_outgoing": 1,
		"enable_outgoing": 1,
		"default_outgoing": 1,
	}

	frappe.db.set_value("Email Account", email_account_name, updates)
	frappe.clear_document_cache("Email Account", email_account_name)

	# Ensure at least one IMAP folder (validate requires it when IMAP is on)
	if not frappe.db.count("IMAP Folder", {"parent": email_account_name}):
		parent = frappe.get_doc("Email Account", email_account_name)
		parent.append("imap_folder", {"folder_name": "INBOX"})
		parent.flags.ignore_validate = True
		parent.save(ignore_permissions=True)

	row = frappe.db.get_value(
		"Email Account",
		email_account_name,
		[
			"email_id",
			"email_server",
			"incoming_port",
			"use_imap",
			"use_ssl",
			"smtp_server",
			"smtp_port",
			"use_tls",
			"use_ssl_for_outgoing",
			"domain",
		],
		as_dict=True,
	)

	return {
		"ok": True,
		"email_account": email_account_name,
		"email_id": row.email_id,
		"incoming": {
			"server": row.email_server,
			"port": row.incoming_port,
			"use_imap": int(row.use_imap or 0),
			"use_ssl": int(row.use_ssl or 0),
		},
		"outgoing": {
			"server": row.smtp_server,
			"port": row.smtp_port,
			"use_tls": int(row.use_tls or 0),
			"use_ssl_for_outgoing": int(row.use_ssl_for_outgoing or 0),
		},
		"domain_cleared": not row.domain,
	}
