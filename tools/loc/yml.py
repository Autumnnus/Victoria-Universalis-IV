#!/usr/bin/env python3
"""Reading and writing Victoria 3 localization files.

Every other module in the pipeline goes through here, so encoding rules live in
one place: UTF-8 with BOM, CRLF line endings, the language header on line one,
and the original key order preserved. Non-entry lines (comments, blank lines)
are carried through untouched.

The entry pattern accepts both `key:0 "value"` and `key: "value"`, with or
without leading whitespace - vanilla and this mod both use all four shapes.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

ENTRY = re.compile(
    r'^(?P<indent>[ \t]*)(?P<key>[A-Za-z0-9_.\-]+):(?P<version>\d*)[ \t]+"(?P<value>.*)"[ \t]*$'
)
HEADER = re.compile(r"^﻿?l_(?P<language>[a-z_]+):\s*$")


@dataclass
class Entry:
    key: str
    value: str
    line: int
    indent: str = " "
    version: str = "0"


@dataclass
class LocFile:
    path: Path
    language: str
    lines: list[str] = field(default_factory=list)  # without line endings
    entries: dict[str, Entry] = field(default_factory=dict)

    @property
    def order(self) -> list[str]:
        return list(self.entries)

    def values(self) -> dict[str, str]:
        return {key: entry.value for key, entry in self.entries.items()}


def read(path: Path) -> LocFile:
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    language = ""
    if lines:
        header = HEADER.match(lines[0])
        if header:
            language = header.group("language")
    loc = LocFile(path=path, language=language, lines=lines)
    for index, line in enumerate(lines):
        match = ENTRY.match(line)
        if not match:
            continue
        key = match.group("key")
        loc.entries[key] = Entry(
            key=key,
            value=match.group("value"),
            line=index,
            indent=match.group("indent") or " ",
            version=match.group("version") or "0",
        )
    return loc


def escape(value: str) -> str:
    """Escape bare double quotes without doubling an existing escape."""
    return re.sub(r'(?<!\\)"', r'\\"', value)


def format_entry(entry: Entry, value: str | None = None) -> str:
    text = escape(value if value is not None else entry.value)
    return f'{entry.indent}{entry.key}:{entry.version} "{text}"'


def write(path: Path, language: str, lines: list[str]) -> None:
    """Write a localization file with the mod's encoding conventions."""
    body = "\r\n".join(lines)
    if not body.endswith("\r\n"):
        body += "\r\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes("﻿".encode("utf-8") + body.encode("utf-8"))


def build_target(source: LocFile, language: str, values: dict[str, str]) -> list[str]:
    """Render a target-language file from the English source layout.

    Keys missing from `values` are dropped rather than left in English, so the
    game falls back to English for them instead of showing a stale translation.
    Comments and blank lines from the source are kept for reviewer orientation.
    """
    out: list[str] = [f"l_{language}:"]
    for index, line in enumerate(source.lines):
        if index == 0 and HEADER.match(line):
            continue
        match = ENTRY.match(line)
        if not match:
            out.append(line)
            continue
        key = match.group("key")
        if key not in values:
            continue
        entry = source.entries[key]
        out.append(format_entry(entry, values[key]))
    return out


def english_files(english_dir: Path) -> list[Path]:
    return sorted(english_dir.glob("*_l_english.yml"))


def target_path(loc_dir: Path, source_name: str, language: str) -> Path:
    return loc_dir / language / source_name.replace("_l_english", f"_l_{language}")
