#!/usr/bin/env python3
"""Fill a language's termbase with candidate translations for the mod's terms.

This runs before any text is translated. Deciding the 88 canonical terms once and
locking them is what keeps a 2,259-key sweep internally consistent; leaving them
to be re-invented inside every request is how the shipped files ended up with two
names for National Cohesion in the same language.

Each term is proposed with the game's own related vocabulary in view, so a mod
term does not collide with a vanilla one. Existing `locked` decisions are never
touched. Existing `candidate` decisions are kept unless --force is given.

Usage:
    export GEMINI_API_KEY=...
    python -m tools.loc.propose_terms --language german
    python -m tools.loc.propose_terms --all --dry-run
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.loc import config, gemini, glossary, keys

BATCH = 22

SYSTEM = """\
You are establishing the official {language} ({tag}) terminology for Victoria
Universalis IV, a mod for Victoria 3, set between 1836 and 1936.

These terms will be locked and reused in thousands of interface strings, so each
one must be a name, not a description: short, unambiguous, and in the register of
a 19th-century state's official vocabulary. A player will meet it in a panel
label, a tooltip and an event title alike.

For every term you receive its English form, what it means in this mod, and the
mistranslation to avoid. You also receive the vocabulary the player's own game
already uses in {language}. Rules:

1. Never collide with a vanilla term that means something else. If the game
   already uses a word for another concept, choose a different one.
2. Where the mod term wraps a vanilla concept, stay close to the vanilla wording
   so the player recognises it.
3. Prefer a term of the period over a modern technical one, unless the vanilla
   interface uses the modern one.
4. Keep the same word family across related terms (Religious Model, Religious
   Program, Religious Project) so the systems read as one system.
5. Give the single best choice in "translation", up to two defensible
   alternatives, and a one-line reason in English for the maintainer.\
"""

TASK = """\
Establish {language} terms for the following.

The player's game already uses these {language} words:
{vanilla}

Terms to decide:
{terms}\
"""

SCHEMA = {
    "type": "object",
    "properties": {
        "terms": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "translation": {"type": "string"},
                    "alternatives": {"type": "array", "items": {"type": "string"}},
                    "reason": {"type": "string"},
                },
                "required": ["id", "translation"],
            },
        }
    },
    "required": ["terms"],
}

# Vanilla words worth putting in front of the model for every batch: these are the
# concepts the mod's vocabulary sits next to and must not collide with.
ANCHORS = (
    "concept_authority",
    "concept_bureaucracy",
    "concept_legitimacy",
    "concept_literacy",
    "concept_innovation",
    "concept_prestige",
    "concept_turmoil",
    "concept_conversion",
    "concept_assimilation",
    "concept_acceptance",
    "concept_state",
    "concept_law",
    "concept_institution",
    "concept_journal_entry",
    "concept_technology_spread",
    "ig_devout",
    "ig_intelligentsia",
    "institution_schools",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--language", choices=sorted(config.LANGUAGES), action="append")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--force", action="store_true", help="Replace existing candidates too.")
    parser.add_argument("--model")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--min-interval", type=float, default=0.0, help="Seconds between calls, per key.")
    parser.add_argument("--day-cooldown", type=float, default=360.0,
                        help="Minutes to rest a key whose daily allowance is spent.")
    args = parser.parse_args()

    languages = sorted(config.LANGUAGES) if args.all else (args.language or [])
    if not languages:
        parser.error("choose --language (repeatable) or --all")

    terms = glossary.load_terms()
    client = None
    if not args.dry_run:
        try:
            client = gemini.Client(
                args.model or config.MODELS["quality"],
                pool=keys.pool(min_interval=args.min_interval, day_cooldown=args.day_cooldown * 60),
            )
        except (gemini.GeminiError, keys.NoKeys) as error:
            raise SystemExit(str(error)) from error

    for language in languages:
        name, tag = config.LANGUAGES[language]
        decisions = glossary.load_decisions(language)
        vanilla = glossary.load_vanilla(language)
        anchor_lines = "\n".join(
            f'  "{vanilla[key]["en"]}" -> {vanilla[key]["target"]}' for key in ANCHORS if key in vanilla
        ) or "  (no vanilla reference extracted yet)"

        todo = [
            term
            for term in terms.values()
            if not (
                decisions.get(term.id)
                and decisions[term.id].translation
                and (decisions[term.id].status == "locked" or not args.force)
            )
        ]
        print(f"\n{language}: {len(todo)} term(s) to propose")
        if not todo:
            continue

        for start in range(0, len(todo), BATCH):
            batch = todo[start : start + BATCH]
            payload = [
                {
                    "id": term.id,
                    "english": term.english,
                    "category": term.category,
                    "meaning": term.definition,
                    "avoid": term.avoid,
                }
                for term in batch
            ]
            prompt = TASK.format(
                language=name,
                vanilla=anchor_lines,
                terms=json.dumps(payload, ensure_ascii=False, indent=1),
            )
            if args.dry_run:
                print("\n--- system instruction ---\n" + SYSTEM.format(language=name, tag=tag))
                print("\n--- first request ---\n" + prompt[:3000])
                break

            assert client is not None
            try:
                answer = client.structured(SYSTEM.format(language=name, tag=tag), prompt, SCHEMA)
            except gemini.QuotaExhausted as error:
                glossary.save_decisions(language, terms, decisions)
                print(f"\nStopped: {error}")
                print("Terms decided so far are saved; re-running continues from there.")
                return 2
            except gemini.GeminiError as error:
                print(f"  ! batch {start // BATCH + 1} failed: {error}")
                continue
            for entry in answer.get("terms", []):
                term_id = entry.get("id", "")
                if term_id not in terms or not entry.get("translation"):
                    continue
                existing = decisions.get(term_id)
                if existing and existing.status == "locked" and existing.translation:
                    continue
                note = entry.get("reason", "")
                alternatives = entry.get("alternatives") or []
                if alternatives:
                    note = (note + " | alternatives: " + ", ".join(alternatives[:2])).strip(" |")
                decisions[term_id] = glossary.Decision(
                    id=term_id, translation=entry["translation"], status="candidate", note=note.replace("\t", " ")
                )
                print(f"  {terms[term_id].english:<32} -> {entry['translation']}")

        if not args.dry_run:
            path = glossary.save_decisions(language, terms, decisions)
            print(f"  written: {path.relative_to(config.MOD_ROOT)}")

    if client:
        print(
            f"\n{client.calls} request(s), {client.prompt_tokens} prompt tokens, "
            f"{client.output_tokens} output tokens."
        )
        print(client.pool.report())
        print("Review the candidates, then change the ones you accept to `locked`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
