# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

DOC_STATUS_DRAFT = "Draft"
DOC_STATUS_QUEUED = "Queued"
DOC_STATUS_SENT = "Sent"
DOC_STATUS_SUBMITTED = "Submitted"
DOC_STATUS_ACCEPTED = "Accepted"
DOC_STATUS_REJECTED = "Rejected"

OPEN_PIPELINE_STAGES = ("Prospecting", "Qualified", "Proposal", "Negotiation")
CLOSED_PIPELINE_STAGES = ("Won", "Lost")

PIPELINE_STAGE_ORDER = {
	"Prospecting": 1,
	"Qualified": 2,
	"Proposal": 3,
	"Negotiation": 4,
	"Won": 5,
	"Lost": 5,
}
