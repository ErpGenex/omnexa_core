# Copyright (c) 2026, ErpGenEx
"""Serialize portal dataclasses for API responses."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any


def to_serializable(value: Any) -> Any:
	if is_dataclass(value):
		return {key: to_serializable(item) for key, item in asdict(value).items()}
	if isinstance(value, dict):
		return {key: to_serializable(item) for key, item in value.items()}
	if isinstance(value, list):
		return [to_serializable(item) for item in value]
	return value
