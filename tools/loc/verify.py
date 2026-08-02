#!/usr/bin/env python3
"""Quality gate for the localization folder. Run before packaging a release.

Replaces tools/verify_localization.py and adds the checks the old pipeline had
no way to make: whitespace and quoting hygiene, frame-length budgets, and locked
glossary terms.

Exit code 1 means at least one blocking problem was found.

Usage:
    python -m tools.loc.verify
    python -m tools.loc.verify --language turkish --file ve_gui_l_english.yml
    python -m tools.loc.verify --strict          # treat warnings as failures too
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from collections import Counter

from tools.loc import config, glossary, state as state_module, tokens, yml

# Values that are legitimately identical to English: the mod's own name, pure
# variable payloads, and short cognates.
ALLOWED_EQUAL_KEYS = {
    "VE_TEXT_MENU_TITLE",
    "VE_BTN",
    "VE_RELIGION",
    "VE_RELIGION_SELECTED",
    "VE_IDEAS",
    "VE_IDEAS_SELECTED",
    "event_mod_name",
    "dev.3.b",
    "ve_ambition",
    "ve_bonus",
    "VE_LG_PAGE_INFO",
    "VE_CP_IDEAS_TITLE",
    "ve_welcome.1.t",
}


def check_source(source: Path) -> tuple[list[str], list[str]]:
    """English-side hygiene: encoding (blocking), and keys defined twice (warning)."""
    problems: list[str] = []
    warnings: list[str] = []
    # A source file without a BOM ships mojibake to every player, and one command
    # repairs it, so it blocks rather than warns.
    for problem in yml.encoding_problems(source):
        problems.append(f"english/{source.name}: {problem}  (fix with `loc verify --fix-encoding`)")
    lines = source.read_text(encoding="utf-8-sig").splitlines()
    keys = [match.group("key") for match in (yml.ENTRY.match(line) for line in lines) if match]
    duplicates = {key: count for key, count in Counter(keys).items() if count > 1}
    if duplicates:
        total = sum(count - 1 for count in duplicates.values())
        warnings.append(
            f"english/{source.name}: {len(duplicates)} key(s) defined more than once "
            f"({total} dead line(s)), e.g. {', '.join(list(duplicates)[:4])}"
        )
    return problems, warnings


def check_state(source: Path, language: str, state: state_module.State) -> list[str]:
    """A key recorded as translated must exist in the file, or it is skipped forever."""
    target = yml.target_path(config.LOC_DIR, source.name, language)
    if not target.exists():
        return []
    present = set(yml.read(target).entries)
    recorded = {
        key
        for key, entry in state.data.get("files", {}).get(source.name, {}).items()
        if language in entry.get("langs", {})
    }
    ghosts = sorted(recorded - present)
    if ghosts:
        return [
            f"{language}/{target.name}: {len(ghosts)} key(s) recorded as translated but absent "
            f"from the file: {', '.join(ghosts[:4])} (the next translate run drops the record)"
        ]
    return []


def check_language(
    source: Path,
    language: str,
    terms: dict[str, glossary.Term],
) -> tuple[list[str], list[str]]:
    """Return (blocking problems, warnings) for one file in one language."""
    problems: list[str] = []
    warnings: list[str] = []
    tier = config.profile(source.name)["tier"]
    target = yml.target_path(config.LOC_DIR, source.name, language)
    label = f"{language}/{target.name}"

    if not target.exists():
        return [f"{label}: file missing"], warnings

    english = yml.read(source)
    translated = yml.read(target)

    if translated.language != language:
        problems.append(f"{label}: header is l_{translated.language or '?'}, expected l_{language}")
    for problem in yml.encoding_problems(target):
        problems.append(f"{label}: {problem}  (fix with `loc verify --fix-encoding`)")

    missing = [key for key in english.entries if key not in translated.entries]
    extra = [key for key in translated.entries if key not in english.entries]
    if missing:
        warnings.append(f"{label}: {len(missing)} keys fall back to English")
    if extra:
        problems.append(f"{label}: {len(extra)} keys not in the English source: {', '.join(extra[:5])}")

    if tier == "X":
        return problems, warnings

    for key, entry in english.entries.items():
        if key not in translated.entries:
            continue
        value = translated.entries[key].value
        kind = config.key_kind(key, entry.value)
        budget = config.max_chars(key, kind, len(tokens.visible(entry.value)))
        for severity, message in tokens.validate(key, entry.value, value, budget):
            (problems if severity == "error" else warnings).append(f"{label}: {key}: {message}")
        if key not in ALLOWED_EQUAL_KEYS and tokens.looks_untranslated(entry.value, value):
            warnings.append(f"{label}: {key}: still English")
        for violation in glossary.violations(entry.value, value, language, terms):
            warnings.append(f"{label}: {key}: {violation}")

    return problems, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--language", choices=sorted(config.LANGUAGES), action="append")
    parser.add_argument("--file", action="append", help="English filename, e.g. ve_gui_l_english.yml")
    parser.add_argument("--strict", action="store_true", help="Fail on warnings as well.")
    parser.add_argument(
        "--fix-encoding",
        action="store_true",
        help="Rewrite files that lack the UTF-8 BOM or use the wrong line endings.",
    )
    args = parser.parse_args()

    if args.fix_encoding:
        fixed = 0
        for path in sorted(config.LOC_DIR.glob("*/*.yml")):
            changes = yml.fix_encoding(path)
            if not changes:
                continue
            fixed += 1
            refused = any(change.startswith("not valid UTF-8") for change in changes)
            print(f"{'SKIP ' if refused else 'fixed'} {path.relative_to(config.MOD_ROOT)}: {', '.join(changes)}")
        print(
            f"\n{fixed} file(s) needed repair."
            if fixed
            else "\nEvery localization file is UTF-8 with a BOM and CRLF line endings."
        )
        return 0

    sources = yml.english_files(config.ENGLISH_DIR)
    if args.file:
        wanted = set(args.file)
        unknown = wanted - {source.name for source in sources}
        if unknown:
            raise SystemExit(f"Unknown English file(s): {', '.join(sorted(unknown))}")
        sources = [source for source in sources if source.name in wanted]

    terms = glossary.load_terms()
    state = state_module.State.load()
    problems: list[str] = []
    warnings: list[str] = []
    for source in sources:
        source_problems, source_warnings = check_source(source)
        problems += source_problems
        warnings += source_warnings
        for language in args.language or sorted(config.LANGUAGES):
            file_problems, file_warnings = check_language(source, language, terms)
            problems += file_problems
            warnings += file_warnings + check_state(source, language, state)

    for warning in warnings:
        print(f"warn  {warning}")
    for problem in problems:
        print(f"FAIL  {problem}")
    print(f"\n{len(problems)} blocking problem(s), {len(warnings)} warning(s)")
    if problems or (args.strict and warnings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
