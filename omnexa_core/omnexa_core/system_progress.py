from __future__ import annotations

import frappe
from frappe.utils.background_jobs import get_queues


def _site_job_ids(registry) -> list[str]:
	site_prefix = f"{frappe.local.site}::"
	return [job_id for job_id in (registry.get_job_ids() or []) if isinstance(job_id, str) and job_id.startswith(site_prefix)]


@frappe.whitelist()
def get_system_long_ops_status() -> dict:
	"""Return aggregated queued/running long operations for current site."""
	frappe.only_for(("System Manager", "Administrator"))

	queued = 0
	started = 0
	failed = 0

	for queue in get_queues():
		queued += len(_site_job_ids(queue))
		started += len(_site_job_ids(queue.started_job_registry))
		failed += len(_site_job_ids(queue.failed_job_registry))

	total_active = queued + started
	# Heuristic progress ratio (started over active backlog). Indeterminate if no active jobs.
	progress_ratio = int((started / total_active) * 100) if total_active > 0 else 0

	return {
		"ok": True,
		"site": frappe.local.site,
		"queued": queued,
		"started": started,
		"failed": failed,
		"total_active": total_active,
		"progress_ratio": progress_ratio,
	}

