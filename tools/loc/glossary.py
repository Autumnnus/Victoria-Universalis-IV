#!/usr/bin/env python3
"""The mod's termbase: canonical terms and their locked per-language decisions.

Two layers feed a translation request:

* `localization/glossary/terms.tsv` - the mod's own vocabulary, with a definition
  and a recorded mistranslation to avoid.
* `localization/glossary/vanilla/<language>.json` - Victoria 3's own vocabulary,
  extracted from the installed game by tools/loc/vanilla_terms.py.

A per-language decision has a status. `locked` means a human accepted it and no
translation run may contradict it. `candidate` means a model proposed it and it
is in use but still open to review. `todo` means nothing has been decided yet.

Usage:
    python -m tools.loc.glossary --init              # create missing language files
    python -m tools.loc.glossary --check             # coverage and consistency
    python -m tools.loc.glossary --show german       # print the German termbase
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.loc import config

TERMS_HEADER = ("id", "english", "category", "definition", "avoid")
LANG_HEADER = ("id", "translation", "status", "note")
STATUSES = ("locked", "candidate", "todo")


@dataclass
class Term:
    id: str
    english: str
    category: str
    definition: str
    avoid: str


@dataclass
class Decision:
    id: str
    translation: str
    status: str
    note: str = ""


def _rows(path: Path, header: tuple[str, ...]) -> list[list[str]]:
    if not path.exists():
        return []
    rows: list[list[str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        cells = line.split("\t")
        if [cell.strip() for cell in cells[: len(header)]] == list(header):
            continue
        cells += [""] * (len(header) - len(cells))
        rows.append([cell.strip() for cell in cells[: len(header)]])
    return rows


def load_terms() -> dict[str, Term]:
    terms: dict[str, Term] = {}
    for row in _rows(config.TERMS_FILE, TERMS_HEADER):
        terms[row[0]] = Term(id=row[0], english=row[1], category=row[2], definition=row[3], avoid=row[4])
    return terms


def load_decisions(language: str) -> dict[str, Decision]:
    path = config.GLOSSARY_DIR / f"{language}.tsv"
    decisions: dict[str, Decision] = {}
    for row in _rows(path, LANG_HEADER):
        decisions[row[0]] = Decision(id=row[0], translation=row[1], status=row[2] or "todo", note=row[3])
    return decisions


def save_decisions(language: str, terms: dict[str, Term], decisions: dict[str, Decision]) -> Path:
    path = config.GLOSSARY_DIR / f"{language}.tsv"
    name = config.LANGUAGES[language][0]
    lines = [
        f"### Victoria Universalis IV - {name} termbase.",
        "### Tab-separated: id, translation, status, note",
        "### status: locked (human-approved, never re-translated) | candidate (model "
        "proposal in use) | todo (undecided)",
        "### Term ids and their English source live in localization/glossary/terms.tsv.",
        "\t".join(LANG_HEADER),
    ]
    for term_id in terms:
        decision = decisions.get(term_id, Decision(id=term_id, translation="", status="todo"))
        lines.append("\t".join((term_id, decision.translation, decision.status, decision.note)))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def load_vanilla(language: str) -> dict[str, dict[str, str]]:
    path = config.VANILLA_GLOSSARY_DIR / f"{language}.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))["terms"]


def _mentions(english: str, haystack: str) -> bool:
    return bool(re.search(r"\b" + re.escape(english.lower()) + r"\b", haystack))


def subset_for(
    values: list[str],
    language: str,
    terms: dict[str, Term] | None = None,
) -> dict[str, list[dict[str, str]]]:
    """The glossary slice relevant to one batch of English values.

    Sending the whole termbase with every request wastes context and dilutes the
    instruction; sending only the terms that actually occur keeps it sharp.
    """
    terms = terms if terms is not None else load_terms()
    decisions = load_decisions(language)
    vanilla = load_vanilla(language)
    haystack = " ".join(values).lower()
    references = {name for value in values for name in re.findall(r"\[([a-z0-9_]+)\]|\$([a-z0-9_]+)\$", value.lower()) for name in name if name}

    mod_slice: list[dict[str, str]] = []
    for term in terms.values():
        if not _mentions(term.english, haystack):
            continue
        decision = decisions.get(term.id)
        mod_slice.append(
            {
                "english": term.english,
                "use": decision.translation if decision and decision.translation else "",
                "status": decision.status if decision else "todo",
                "definition": term.definition,
                "avoid": term.avoid,
            }
        )

    vanilla_slice: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for key, pair in vanilla.items():
        if key not in references and not _mentions(pair["en"], haystack):
            continue
        # Several keys resolve to the same word; the translator needs it once.
        signature = (pair["en"], pair["target"])
        if signature in seen:
            continue
        seen.add(signature)
        vanilla_slice.append({"english": pair["en"], "use": pair["target"], "source": key})

    return {"mod": mod_slice, "vanilla": vanilla_slice}


def violations(english: str, translated: str, language: str, terms: dict[str, Term] | None = None) -> list[str]:
    """Locked terms whose English appears in the source but whose translation is missing."""
    terms = terms if terms is not None else load_terms()
    decisions = load_decisions(language)
    problems: list[str] = []
    lowered_source = english.lower()
    lowered_target = translated.lower()
    for term in terms.values():
        decision = decisions.get(term.id)
        if not decision or decision.status != "locked" or not decision.translation:
            continue
        if not _mentions(term.english, lowered_source):
            continue
        if decision.translation.lower() not in lowered_target:
            problems.append(f"locked term missing: {term.english!r} -> {decision.translation!r}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--init", action="store_true", help="Create or normalise every language file.")
    parser.add_argument("--check", action="store_true", help="Report coverage and duplicate translations.")
    parser.add_argument("--show", choices=sorted(config.LANGUAGES))
    args = parser.parse_args()

    terms = load_terms()
    if not terms:
        raise SystemExit(f"No terms found in {config.TERMS_FILE}")

    if args.init:
        for language in sorted(config.LANGUAGES):
            path = save_decisions(language, terms, load_decisions(language))
            print(f"{language}: {len(terms)} terms -> {path.relative_to(config.MOD_ROOT)}")
        return 0

    if args.show:
        decisions = load_decisions(args.show)
        for term in terms.values():
            decision = decisions.get(term.id)
            print(f"{term.english:<34} {decision.translation if decision else '':<40} {decision.status if decision else 'todo'}")
        return 0

    if args.check:
        print(f"{len(terms)} canonical terms\n")
        failures = 0
        for language in sorted(config.LANGUAGES):
            decisions = load_decisions(language)
            locked = sum(1 for d in decisions.values() if d.status == "locked" and d.translation)
            candidate = sum(1 for d in decisions.values() if d.status == "candidate" and d.translation)
            missing = [t for t in terms if not decisions.get(t) or not decisions[t].translation]
            unknown = [i for i in decisions if i not in terms]
            bad_status = [i for i, d in decisions.items() if d.status not in STATUSES]
            collisions: dict[str, list[str]] = {}
            for term_id, decision in decisions.items():
                if decision.translation:
                    collisions.setdefault(decision.translation.lower(), []).append(term_id)
            duplicates = {value: ids for value, ids in collisions.items() if len(ids) > 1}
            vanilla = load_vanilla(language)
            print(
                f"{language:<14} locked={locked:<4} candidate={candidate:<4} "
                f"missing={len(missing):<4} vanilla_ref={len(vanilla)}"
            )
            for problem, items in (("unknown ids", unknown), ("bad status", bad_status)):
                if items:
                    failures += 1
                    print(f"  ! {problem}: {', '.join(items[:8])}")
            for value, ids in duplicates.items():
                print(f"  ~ same translation for {', '.join(ids)}: {value!r}")
        return 1 if failures else 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
