#!/usr/bin/env python3
"""Check that VE localization targets retain English source keys and technical tokens."""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import re
import sys

LINE = re.compile(r'^\s*([^\s:#]+):\d+\s+"(.*)"\s*$')
TOKEN = re.compile(r"(\[[^\]]+\]|#[A-Za-z_]+|#!|\$[^$]+\$|£[^£]*£|@[^@!]+!)")
LANGUAGES = ("braz_por", "french", "german", "japanese", "korean", "polish", "russian", "simp_chinese", "spanish", "turkish")
# These keys are either the mod's proper name, a value made entirely from
# variables/numbers, or a legitimate identical cognate in one or more targets.
ALLOWED_EQUAL_KEYS = {
    "VE_TEXT_MENU_TITLE", "VE_BTN", "VE_RELIGION", "VE_RELIGION_SELECTED",
    "VE_IDEAS", "VE_IDEAS_SELECTED", "event_mod_name", "dev.3.b",
    "ve_ambition", "ve_bonus", "VE_LG_PAGE_INFO", "VE_CP_IDEAS_TITLE",
}


def entries(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        match = LINE.match(line)
        if match:
            result[match.group(1)] = match.group(2)
    return result


def main() -> int:
    root = Path(__file__).resolve().parents[1] / "localization"
    failures: list[str] = []
    for source in sorted((root / "english").glob("*.yml")):
        source_entries = entries(source)
        for language in LANGUAGES:
            target = root / language / source.name.replace("_l_english", f"_l_{language}")
            target_entries = entries(target)
            missing = source_entries.keys() - target_entries.keys()
            extra = target_entries.keys() - source_entries.keys()
            if missing or extra:
                failures.append(f"{language}/{target.name}: missing={len(missing)}, extra={len(extra)}")
            for key, source_value in source_entries.items():
                if key in target_entries and Counter(TOKEN.findall(source_value)) != Counter(TOKEN.findall(target_entries[key])):
                    failures.append(f"{language}/{target.name}: token mismatch in {key}")
                # Texticon carriers intentionally equal their key and must remain so.
                if (
                    source.name != "ve_religion_aspect_icons_l_english.yml"
                    and key in target_entries
                    and key not in ALLOWED_EQUAL_KEYS
                    and source_value == target_entries[key]
                    and re.search(r"[A-Za-z]{4}", TOKEN.sub("", source_value))
                ):
                    failures.append(f"{language}/{target.name}: untranslated visible value in {key}")
    if failures:
        print("\n".join(failures))
        return 1
    print("All target localization keys and technical tokens match English sources.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
