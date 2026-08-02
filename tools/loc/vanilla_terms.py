#!/usr/bin/env python3
"""Extract Victoria 3's own vocabulary, per language, as a translation reference.

Half of this mod's text talks about vanilla concepts - Bureaucracy, Authority,
Legitimacy, Literacy, Migration Attraction, the Devout, Turmoil. Inventing new
words for those is the single largest source of "this reads like a bad machine
translation": the player sees one name in the mod panel and a different one in
the game's own interface. So we do not invent them. We read them out of the
installed game.

The game directory is opened read-only. Output goes to
localization/glossary/vanilla/<language>.json and is committed, so a translation
run does not depend on the game being installed.

Usage:
    python -m tools.loc.vanilla_terms                # all languages
    python -m tools.loc.vanilla_terms --language german
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

if __package__ in (None, ""):  # allow `python tools/loc/vanilla_terms.py`
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.loc import config, fs, yml
from tools.loc.tokens import TOKEN

# Concept keys carry the player-facing name of a game concept. The variants
# below are explanatory bodies, not names, and are not part of the vocabulary.
SKIP_SUFFIXES = (
    "_desc",
    "_desc_added",
    "_tooltip",
    "_tt",
    "_hint",
    "_effects",
    "_intro",
    "_short",  # abbreviated UI variants are cut to fit, not proper names
    "_short_desc",
)
CONCEPT_KEY = re.compile(r"^concept_[a-z0-9_]+$")
# Generic interface words carry no domain meaning and their vanilla translation is
# often the wrong sense in context ("Default" is rendered as debt default), so they
# are kept out of the reference entirely.
STOPWORDS = {
    "all", "and", "countries", "country", "day", "days", "default", "group", "groups",
    "level", "levels", "month", "months", "name", "national", "no", "none", "open", "or",
    "order", "other", "progress", "tier", "time", "total", "type", "value", "year",
    "years", "yes",
}
# Interest groups, institutions, laws, buildings and building groups are named
# just as often as concepts in this mod's text ("Devout approval", "the Schools
# institution", "Church and State", "Manufacturing levels").
NAMED_ENTITY_KEY = re.compile(r"^(ig_|institution_|law_|building_|bg_|technology_|goods_)[a-z0-9_]+$")
REFERENCE = re.compile(r"\[([A-Za-z0-9_]+)\]|\$([A-Za-z0-9_]+)\$")

# Modifier types the mod actually writes, so the reference stays focused on
# vocabulary the translator will really meet.
MODIFIER_TYPE = re.compile(r"^\s*([a-z][a-z0-9_]*(?:_add|_mult|_max|_min))\s*=", re.MULTILINE)


def _language_files(language: str) -> list[Path]:
    base = config.VANILLA_GAME_DIR / "localization"
    files = sorted((base / language).rglob("*.yml"))
    files += sorted((base / "modifiers").glob(f"*_l_{language}.yml"))
    return files


def _raw_entries(language: str) -> dict[str, str]:
    entries: dict[str, str] = {}
    for path in _language_files(language):
        try:
            loc = yml.read(path)
        except (OSError, UnicodeDecodeError):
            continue
        for key, entry in loc.entries.items():
            entries.setdefault(key, entry.value)
    return entries


def _resolve(value: str, entries: dict[str, str], depth: int = 3) -> str:
    """Follow `[key]` / `$key$` indirection, then drop the remaining markup."""
    for _ in range(depth):
        def substitute(match: re.Match[str]) -> str:
            name = match.group(1) or match.group(2)
            if name in entries and name not in ("Nbsp",):
                return entries[name]
            return match.group(0)

        replaced = REFERENCE.sub(substitute, value)
        if replaced == value:
            break
        value = replaced
    plain = TOKEN.sub(" ", value)
    plain = plain.replace("\\n", " ")
    return re.sub(r"\s+", " ", plain).strip(" :,-")


def _mod_text() -> tuple[str, set[str]]:
    """All English mod prose, plus every concept key the mod references directly."""
    prose: list[str] = []
    referenced: set[str] = set()
    for path in yml.english_files(config.ENGLISH_DIR):
        loc = yml.read(path)
        for entry in loc.entries.values():
            prose.append(entry.value)
            for name in REFERENCE.findall(entry.value):
                referenced.add(name[0] or name[1])
    return " ".join(prose).lower(), referenced


def _mod_modifier_types() -> set[str]:
    found: set[str] = set()
    for path in (config.MOD_ROOT / "common" / "static_modifiers").glob("*.txt"):
        found.update(MODIFIER_TYPE.findall(path.read_text(encoding="utf-8-sig", errors="replace")))
    return found


def select(modifier_types: set[str]) -> dict[str, str]:
    """Pick the vanilla keys worth referencing, with their English names.

    Selection depends only on English, so it runs once and is reused for every
    target language.
    """
    english_entries = _raw_entries("english")
    mod_prose, mod_references = _mod_text()

    wanted: list[str] = [
        key
        for key in english_entries
        if (CONCEPT_KEY.match(key) or NAMED_ENTITY_KEY.match(key))
        and not key.endswith(SKIP_SUFFIXES)
    ]
    wanted += [key for key in sorted(modifier_types) if key in english_entries]

    selected: dict[str, str] = {}
    for key in wanted:
        english = _resolve(english_entries[key], english_entries)
        if not english or len(english) > 60:
            continue
        if english.lower() in STOPWORDS:
            continue
        # Keep the reference relevant: a vanilla term earns its place only if the
        # mod's own English text names it or references its key.
        if key not in mod_references and not re.search(
            r"\b" + re.escape(english.lower()) + r"\b", mod_prose
        ):
            continue
        selected[key] = english
    return selected


def build(language: str, selected: dict[str, str]) -> dict[str, object]:
    target_entries = _raw_entries(language)
    terms: dict[str, dict[str, str]] = {}
    for key, english in selected.items():
        if key not in target_entries:
            continue
        target = _resolve(target_entries[key], target_entries)
        if not target:
            continue
        terms[key] = {"en": english, "target": target}
    return {
        "language": language,
        "source": "Victoria 3 game localization (read-only reference)",
        "terms": dict(sorted(terms.items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--language", choices=sorted(config.LANGUAGES), action="append")
    args = parser.parse_args()

    if not (config.VANILLA_GAME_DIR / "localization" / "english").is_dir():
        raise SystemExit(
            f"Vanilla localization not found under {config.VANILLA_GAME_DIR}. "
            "Set VICTORIA3_GAME_DIR to the game directory."
        )

    selected = select(_mod_modifier_types())
    print(f"selected {len(selected)} vanilla keys from the English reference")
    config.VANILLA_GLOSSARY_DIR.mkdir(parents=True, exist_ok=True)
    for language in args.language or sorted(config.LANGUAGES):
        data = build(language, selected)
        path = config.VANILLA_GLOSSARY_DIR / f"{language}.json"
        fs.write_text(path, json.dumps(data, ensure_ascii=False, indent=1) + "\n")
        print(f"{language}: {len(data['terms'])} vanilla terms -> {path.relative_to(config.MOD_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
