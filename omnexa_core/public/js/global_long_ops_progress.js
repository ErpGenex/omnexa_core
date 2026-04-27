(() => {
	if (typeof frappe === "undefined") return;

	const POLL_MS = 5000;
	const WRAP_ID = "omnexa-global-long-ops-progress";

	let started = false;
	let timer = null;

	function ensureDom() {
		if (document.getElementById(WRAP_ID)) return document.getElementById(WRAP_ID);

		const el = document.createElement("div");
		el.id = WRAP_ID;
		el.style.position = "fixed";
		el.style.top = "0";
		el.style.left = "0";
		el.style.right = "0";
		el.style.zIndex = "1040";
		el.style.display = "none";
		el.style.background = "rgba(20, 27, 45, 0.95)";
		el.style.borderBottom = "1px solid rgba(255,255,255,0.12)";
		el.style.padding = "6px 12px";
		el.innerHTML = `
			<div style="display:flex;align-items:center;gap:10px;">
				<div id="${WRAP_ID}-label" style="color:#fff;font-size:12px;white-space:nowrap;"></div>
				<div style="flex:1;height:8px;background:rgba(255,255,255,0.18);border-radius:6px;overflow:hidden;">
					<div id="${WRAP_ID}-bar" style="height:100%;width:0%;background:linear-gradient(90deg,#2cc7ff,#29d17d);transition:width .3s ease;"></div>
				</div>
				<button id="${WRAP_ID}-open" class="btn btn-xs btn-default" style="height:24px;">${__("RQ Jobs")}</button>
			</div>
		`;
		document.body.appendChild(el);

		const openBtn = document.getElementById(`${WRAP_ID}-open`);
		openBtn?.addEventListener("click", () => frappe.set_route("List", "RQ Job"));

		return el;
	}

	function setVisible(state) {
		const wrap = ensureDom();
		wrap.style.display = state ? "block" : "none";
	}

	function render(status) {
		const total = cint(status?.total_active || 0);
		const running = cint(status?.started || 0);
		const queued = cint(status?.queued || 0);
		const pct = cint(status?.progress_ratio || 0);

		if (total <= 0) {
			setVisible(false);
			return;
		}

		setVisible(true);
		const label = document.getElementById(`${WRAP_ID}-label`);
		const bar = document.getElementById(`${WRAP_ID}-bar`);
		if (label) {
			label.textContent = __(
				"Long operations running: {0} running, {1} queued (active: {2})",
				[running, queued, total]
			);
		}
		if (bar) {
			bar.style.width = `${Math.max(8, Math.min(95, pct || 20))}%`;
		}
	}

	function cint(v) {
		const n = parseInt(v, 10);
		return Number.isNaN(n) ? 0 : n;
	}

	async function poll() {
		try {
			// Stop polling outside Desk routes.
			const route = frappe.get_route?.() || [];
			if (!route.length || route[0] === "login") {
				setVisible(false);
				return;
			}
			const status = await frappe.xcall("omnexa_core.omnexa_core.system_progress.get_system_long_ops_status");
			render(status || {});
		} catch (e) {
			// Keep silent for non-manager users / permission-denied paths.
			setVisible(false);
		}
	}

	function boot() {
		if (started) return;
		started = true;
		ensureDom();
		poll();
		timer = window.setInterval(poll, POLL_MS);
	}

	frappe.ready(() => {
		boot();
	});
})();

