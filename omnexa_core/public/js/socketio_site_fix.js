/**
 * Socket.IO LAN fix: send x-frappe-site-name on connect when desk is opened via IP.
 * Must replace init before io() runs (extraHeaders are not applied after connect).
 */
(function () {
	function patchRealtime() {
		const rt = frappe.realtime;
		if (!rt || rt.__omnexa_socket_patched) return;

		const proto = Object.getPrototypeOf(rt);
		const origInit = proto.init;
		if (typeof origInit !== "function") return;

		proto.init = function (port, lazy_connect) {
			if (frappe.boot.disable_async) return;
			if (this.socket) return;

			const me = this;
			const sitename = frappe.boot.sitename;
			me.lazy_connect = lazy_connect;

			const connectWithHeaders = (ioFn) => {
				let socketPort = port || 9000;
				let host = window.location.origin;
				if (window.dev_server) {
					const parts = host.split(":");
					socketPort = frappe.boot.socketio_port || socketPort.toString() || "9000";
					if (parts.length > 2) host = parts[0] + ":" + parts[1];
					host = host + ":" + socketPort;
				}
				const url = host + "/" + sitename;
				const opts = {
					withCredentials: true,
					reconnectionAttempts: 3,
					autoConnect: !lazy_connect,
					extraHeaders: sitename ? { "x-frappe-site-name": sitename } : {},
				};
				if (window.location.protocol === "https:") opts.secure = true;

				me.socket = ioFn(url, opts);
				if (!me.socket) return false;

				me.socket.on("connect_error", function (err) {
					console.error("Error connecting to socket.io:", err.message);
				});
				me.socket.on("msgprint", function (message) {
					frappe.msgprint(message);
				});
				me.socket.on("progress", function (data) {
					if (data.progress) {
						data.percent = (flt(data.progress[0]) / data.progress[1]) * 100;
					}
					if (data.percent) {
						frappe.show_progress(
							data.title || __("Progress"),
							data.percent,
							100,
							data.description,
							true
						);
					}
				});
				if (typeof me.setup_listeners === "function") me.setup_listeners();

				$(document).on("form-load form-rename", function (e, frm) {
					if (!frm.doc || frm.is_new()) return;
					me.doc_subscribe(frm.doctype, frm.docname);
				});
				$(document).on("form-refresh", function (e, frm) {
					if (!frm.doc || frm.is_new()) return;
					me.doc_open(frm.doctype, frm.docname);
				});
				$(document).on("form-unload", function (e, frm) {
					if (!frm.doc || frm.is_new()) return;
					me.doc_close(frm.doctype, frm.docname);
				});
				return true;
			};

			if (typeof window.io === "function" && connectWithHeaders(window.io)) {
				return;
			}

			frappe.require("/assets/frappe/node_modules/socket.io-client/dist/socket.io.min.js", () => {
				if (me.socket) return;
				if (typeof window.io === "function" && connectWithHeaders(window.io)) return;
				origInit.call(me, port, lazy_connect);
			});
		};

		rt.__omnexa_socket_patched = true;
	}

	if (typeof frappe !== "undefined") {
		if (frappe.realtime) patchRealtime();
		frappe.ready(patchRealtime);
	} else {
		document.addEventListener("DOMContentLoaded", () => {
			const wait = setInterval(() => {
				if (typeof frappe !== "undefined" && frappe.realtime) {
					clearInterval(wait);
					patchRealtime();
					frappe.ready(patchRealtime);
				}
			}, 20);
		});
	}
})();
