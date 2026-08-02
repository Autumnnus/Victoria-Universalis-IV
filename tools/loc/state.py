#!/usr/bin/env python3
"""Per-key translation bookkeeping: what is current, what has gone stale, and why.

The unit is one localization key in one language - not a file. A typo fix in one
tooltip brings back exactly that tooltip in ten languages and nothing else.

A key is stale when any of three things changed since it was translated:

* the English value (compared by hash);
* a glossary term that its English text mentions (compared against a snapshot of
  the language's termbase, so locking `Ledger -> Doktrin Defteri` invalidates only
  the keys that actually say "Ledger");
* the prompt generation, when the caller asks for that (`--refresh-prompts`),
  since a reworded instruction does not make existing text wrong.

Usage:
    python -m tools.loc.state --status
    python -m tools.loc.state --pending turkish
    python -m tools.loc.state --why turkish ve_gui_l_english.yml
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.loc import config, fs, glossary, prompts, yml

VERSION = 2

CURRENT = "current"
NEW = "new"
ENGLISH_CHANGED = "english changed"
TERM_CHANGED = "glossary term changed"
PROMPT_CHANGED = "prompt generation changed"


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _mentions(english_term: str, value: str) -> bool:
    return bool(re.search(r"\b" + re.escape(english_term.lower()) + r"\b", value.lower()))


class State:
    def __init__(self, data: dict | None = None) -> None:
        self.data = data or {"version": VERSION, "files": {}, "glossary": {}}
        self.data.setdefault("files", {})
        self.data.setdefault("glossary", {})

    @classmethod
    def load(cls) -> "State":
        if config.STATE_FILE.exists():
            return cls(json.loads(config.STATE_FILE.read_text(encoding="utf-8")))
        return cls()

    def save(self) -> None:
        self.data["version"] = VERSION
        try:
            fs.write_text(
                config.STATE_FILE,
                json.dumps(self.data, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
            )
        except fs.WriteFailed as error:
            # Losing the bookkeeping means some keys get retranslated later; it is
            # not worth killing a ten-language run over.
            print(f"    ! could not save progress: {error}")
            print(f"      the data is in {error.kept.name}; rename it over the original")

    # -- per-key records ------------------------------------------------------

    def _file(self, filename: str) -> dict:
        return self.data["files"].setdefault(filename, {})

    def record(
        self,
        filename: str,
        key: str,
        english: str,
        language: str,
        model: str,
        reviewed: bool = False,
    ) -> None:
        entry = self._file(filename).setdefault(key, {})
        entry["en"] = digest(english)
        langs = entry.setdefault("langs", {})
        previous = langs.get(language, {})
        langs[language] = {
            "model": model,
            "pv": prompts.PROMPT_VERSION,
            "reviewed": reviewed or previous.get("reviewed", False),
        }

    def status_of(
        self,
        filename: str,
        key: str,
        english: str,
        language: str,
        dirty_terms: set[str] | None = None,
        prompt_generation: bool = False,
    ) -> str:
        entry = self._file(filename).get(key)
        if not entry:
            return NEW
        record = entry.get("langs", {}).get(language)
        if not record:
            return NEW
        if entry.get("en") != digest(english):
            return ENGLISH_CHANGED
        if dirty_terms and any(_mentions(term, english) for term in dirty_terms):
            return TERM_CHANGED
        if prompt_generation and record.get("pv") != prompts.PROMPT_VERSION:
            return PROMPT_CHANGED
        return CURRENT

    def is_current(
        self,
        filename: str,
        key: str,
        english: str,
        language: str,
        dirty_terms: set[str] | None = None,
        prompt_generation: bool = False,
    ) -> bool:
        return (
            self.status_of(filename, key, english, language, dirty_terms, prompt_generation)
            == CURRENT
        )

    def is_reviewed(self, filename: str, key: str, language: str) -> bool:
        entry = self._file(filename).get(key, {})
        return bool(entry.get("langs", {}).get(language, {}).get("reviewed"))

    def pending(
        self,
        filename: str,
        language: str,
        values: dict[str, str],
        dirty_terms: set[str] | None = None,
        prompt_generation: bool = False,
    ) -> list[str]:
        return [
            key
            for key, value in values.items()
            if not self.is_current(filename, key, value, language, dirty_terms, prompt_generation)
        ]

    def reasons(
        self,
        filename: str,
        language: str,
        values: dict[str, str],
        dirty_terms: set[str] | None = None,
        prompt_generation: bool = False,
    ) -> dict[str, list[str]]:
        grouped: dict[str, list[str]] = {}
        for key, value in values.items():
            reason = self.status_of(filename, key, value, language, dirty_terms, prompt_generation)
            if reason != CURRENT:
                grouped.setdefault(reason, []).append(key)
        return grouped

    def prune_absent(self, filename: str, language: str, present: set[str]) -> list[str]:
        """Forget records for keys that are not actually in the target file.

        The record and the file can only disagree if a write was interrupted or a
        file was edited by hand, and the disagreement is dangerous in one
        direction: a key marked current but missing from the file would be skipped
        by every future run and silently stay English. Observed once in
        ve_welcome_l_turkish.yml, so the invariant is now enforced on every run.
        """
        removed: list[str] = []
        for key, entry in list(self._file(filename).items()):
            langs = entry.get("langs", {})
            if language in langs and key not in present:
                del langs[language]
                removed.append(key)
                if not langs:
                    del self._file(filename)[key]
        return removed

    def drop_missing(self, filename: str, keys: set[str]) -> None:
        recorded = self._file(filename)
        for key in list(recorded):
            if key not in keys:
                del recorded[key]

    # -- glossary snapshots ---------------------------------------------------

    def dirty_terms(self, language: str, terms: dict[str, glossary.Term]) -> set[str]:
        """English forms of terms whose decision changed since the last snapshot.

        A term with no decision yet is not dirty: nothing was promised about it.
        """
        snapshot = self.data["glossary"].get(language, {})
        if not snapshot:
            return set()
        decisions = glossary.load_decisions(language)
        dirty: set[str] = set()
        for term_id, term in terms.items():
            decision = decisions.get(term_id)
            now = digest(f"{decision.translation}|{decision.status}") if decision and decision.translation else ""
            if not now:
                continue
            if snapshot.get(term_id) != now:
                dirty.add(term.english)
        return dirty

    def snapshot_glossary(self, language: str, terms: dict[str, glossary.Term]) -> None:
        decisions = glossary.load_decisions(language)
        snapshot = {}
        for term_id in terms:
            decision = decisions.get(term_id)
            if decision and decision.translation:
                snapshot[term_id] = digest(f"{decision.translation}|{decision.status}")
        self.data["glossary"][language] = snapshot


# -- reporting ----------------------------------------------------------------


def overview(state: State, terms: dict[str, glossary.Term], prompt_generation: bool = False) -> None:
    sources = yml.english_files(config.ENGLISH_DIR)
    languages = sorted(config.LANGUAGES)
    dirty = {language: state.dirty_terms(language, terms) for language in languages}

    header = f"{'file':<26}{'keys':>6}  " + "".join(f"{language[:4]:>6}" for language in languages)
    print(header)
    print("-" * len(header))
    totals = {language: 0 for language in languages}
    grand = 0
    for source in sources:
        values = yml.read(source).values()
        grand += len(values)
        row = f"{source.name.replace('_l_english.yml', ''):<26}{len(values):>6}  "
        for language in languages:
            done = len(values) - len(
                state.pending(source.name, language, values, dirty[language], prompt_generation)
            )
            totals[language] += done
            row += f"{done:>6}"
        print(row)
    print("-" * len(header))
    print(f"{'total':<26}{grand:>6}  " + "".join(f"{totals[l]:>6}" for l in languages))
    percent = "".join(f"{round(100 * totals[l] / grand) if grand else 0:>5}%" for l in languages)
    print(f"{'':<26}{'':>6}  {percent}")
    for language in languages:
        if dirty[language]:
            print(f"\n{language}: {len(dirty[language])} glossary term(s) changed since the last run")
            print("  " + ", ".join(sorted(dirty[language])[:8]))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--pending", choices=sorted(config.LANGUAGES))
    parser.add_argument("--why", nargs=2, metavar=("LANGUAGE", "FILE"))
    parser.add_argument("--refresh-prompts", action="store_true", help="Count a reworded prompt as stale.")
    args = parser.parse_args()

    state = State.load()
    terms = glossary.load_terms()

    if args.why:
        language, filename = args.why
        source = config.ENGLISH_DIR / filename
        if not source.exists():
            raise SystemExit(f"No such English file: {filename}")
        values = yml.read(source).values()
        grouped = state.reasons(
            filename, language, values, state.dirty_terms(language, terms), args.refresh_prompts
        )
        if not grouped:
            print(f"{language}/{filename}: everything is current ({len(values)} keys)")
            return 0
        for reason, keys in sorted(grouped.items()):
            print(f"{reason}: {len(keys)}")
            for key in keys[:12]:
                print(f"  {key}")
            if len(keys) > 12:
                print(f"  ... and {len(keys) - 12} more")
        return 0

    if args.pending:
        dirty = state.dirty_terms(args.pending, terms)
        total = 0
        for source in yml.english_files(config.ENGLISH_DIR):
            values = yml.read(source).values()
            missing = state.pending(source.name, args.pending, values, dirty, args.refresh_prompts)
            if missing:
                print(f"{source.name}: {len(missing)}/{len(values)} pending")
                total += len(missing)
        print(f"{args.pending}: {total} key(s) pending")
        return 0

    overview(state, terms, args.refresh_prompts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
