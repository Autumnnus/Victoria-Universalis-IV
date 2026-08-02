#!/usr/bin/env python3
"""How a file is cut into requests.

One rule matters more than size: an event's title, description, options and
option tooltips must travel together. Split them and the options come back in a
different voice from the description, which is exactly how the old pipeline
produced text that reads like a machine wrote it.
"""
from __future__ import annotations

import re

# ve_rel_evt.7.a.tt -> ve_rel_evt.7 ; dev.3.b -> dev.3 ; ve_gui_something -> itself
EVENT_PREFIX = re.compile(r"^(.*?\.\d+)(?:\.|$)")

MAX_KEYS = 40
MAX_CHARS = 6000


def group_of(key: str) -> str:
    match = EVENT_PREFIX.match(key)
    return match.group(1) if match else key


def chunks(
    items: list[dict[str, object]],
    max_keys: int = MAX_KEYS,
    max_chars: int = MAX_CHARS,
) -> list[list[dict[str, object]]]:
    """Group items by event, then pack groups into requests.

    A single group larger than the budget is sent alone rather than split, so an
    event is never broken across two requests.
    """
    groups: dict[str, list[dict[str, object]]] = {}
    for item in items:
        groups.setdefault(group_of(str(item["key"])), []).append(item)

    batches: list[list[dict[str, object]]] = []
    current: list[dict[str, object]] = []
    current_chars = 0
    for group in groups.values():
        size = sum(len(str(item["english"])) for item in group) + 40 * len(group)
        if current and (len(current) + len(group) > max_keys or current_chars + size > max_chars):
            batches.append(current)
            current, current_chars = [], 0
        current.extend(group)
        current_chars += size
    if current:
        batches.append(current)
    return batches
