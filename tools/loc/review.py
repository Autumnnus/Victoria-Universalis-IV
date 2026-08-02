#!/usr/bin/env python3
"""Second pass over already translated text: a native reviewer, not a retranslator.

Only tier A files go through this by default - the chrome a player reads on every
screen. The reviewer sees the English source, the current translation and the same
glossary, and answers keep or replace per key. A replacement is written only when
it passes the same validation as a first-pass translation, so the review can never
make a file less publishable than it already was.

Usage:
    export GEMINI_API_KEY=...
    python -m tools.loc.review --language turkish
    python -m tools.loc.review --language german --file ve_gui_l_english.yml --dry-run
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.loc import batching, config, gemini, glossary, keys, prompts, state as state_module, tokens, yml


def review_file(
    source: Path,
    language: str,
    client: gemini.Client | None,
    state: state_module.State,
    terms,
    dry_run: bool,
    show_kept: bool,
) -> tuple[int, int]:
    """Returns (replaced, reviewed)."""
    name, tag = config.LANGUAGES[language]
    profile = config.profile(source.name)
    english = yml.read(source)
    target_path = yml.target_path(config.LOC_DIR, source.name, language)
    if not target_path.exists():
        print(f"  {source.name}: no translation yet")
        return 0, 0

    translated = yml.read(target_path)
    items: list[dict[str, object]] = []
    for key, entry in english.entries.items():
        if key not in translated.entries:
            continue
        if state.is_reviewed(source.name, key, language):
            continue
        items.append(
            {
                "key": key,
                "kind": config.key_kind(key, entry.value),
                "english": entry.value,
                "current": translated.entries[key].value,
            }
        )
    if not items:
        print(f"  {source.name}: nothing left to review")
        return 0, 0

    batches = batching.chunks(items)
    print(f"  {source.name}: {len(items)} to review, {len(batches)} request(s)")

    if dry_run:
        first = batches[0]
        slice_ = glossary.subset_for([str(item["english"]) for item in first], language, terms)
        system, task = prompts.review_prompt(
            language_name=name,
            tag=tag,
            filename=source.name,
            feature=profile["feature"],
            glossary_slice=slice_,
            items=first,
        )
        print("\n--- system instruction ---\n" + system)
        print("\n--- first request ---\n" + task[:4000])
        return 0, 0

    assert client is not None
    values = translated.values()
    replaced = reviewed = 0
    for index, batch in enumerate(batches, start=1):
        slice_ = glossary.subset_for([str(item["english"]) for item in batch], language, terms)
        system, task = prompts.review_prompt(
            language_name=name,
            tag=tag,
            filename=source.name,
            feature=profile["feature"],
            glossary_slice=slice_,
            items=batch,
        )
        try:
            answer = client.structured(system, task, gemini.REVIEW_SCHEMA)
        except gemini.QuotaExhausted:
            yml.write(target_path, language, yml.build_target(english, language, values))
            raise
        except gemini.Truncated as error:
            if len(batch) > 1:
                batches.extend([batch[: len(batch) // 2], batch[len(batch) // 2 :]])
                print(f"    request {index}: {error}; split into two")
            continue
        except gemini.GeminiError as error:
            print(f"    ! request {index} failed: {error}")
            continue

        verdicts = {entry["key"]: entry for entry in answer.get("reviews", [])}
        for item in batch:
            key = str(item["key"])
            verdict = verdicts.get(key)
            if not verdict:
                continue
            reviewed += 1
            if verdict.get("verdict") != "replace":
                if show_kept and verdict.get("reason"):
                    print(f"    = {key}: {verdict['reason']}")
                state.record(source.name, key, str(item["english"]), language, client.model, reviewed=True)
                continue
            candidate = tokens.normalize(verdict.get("value", ""))
            kind = config.key_kind(key, str(item["english"]))
            budget = config.max_chars(key, kind, len(tokens.visible(str(item["english"]))))
            problems = [
                message
                for severity, message in tokens.validate(key, str(item["english"]), candidate, budget)
                if severity == "error"
            ]
            problems += glossary.violations(str(item["english"]), candidate, language, terms)
            if problems:
                print(f"    ! {key}: replacement rejected ({'; '.join(problems)})")
                state.record(source.name, key, str(item["english"]), language, client.model, reviewed=True)
                continue
            print(f"    ~ {key}: {item['current']!r} -> {candidate!r}")
            if verdict.get("reason"):
                print(f"        {verdict['reason']}")
            values[key] = candidate
            replaced += 1
            state.record(source.name, key, str(item["english"]), language, client.model, reviewed=True)

    yml.write(target_path, language, yml.build_target(english, language, values))
    return replaced, reviewed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--language", choices=sorted(config.LANGUAGES), action="append", required=True)
    parser.add_argument("--file", action="append")
    parser.add_argument("--tier", action="append", choices=["A", "B", "C"], default=None)
    parser.add_argument("--model")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--show-kept", action="store_true", help="Print the reviewer's note for kept strings too.")
    parser.add_argument("--min-interval", type=float, default=0.0, help="Seconds between calls, per key.")
    parser.add_argument("--day-cooldown", type=float, default=360.0,
                        help="Minutes to rest a key whose daily allowance is spent.")
    args = parser.parse_args()

    sources = yml.english_files(config.ENGLISH_DIR)
    if args.file:
        wanted = set(args.file)
        unknown = wanted - {source.name for source in sources}
        if unknown:
            raise SystemExit(f"Unknown English file(s): {', '.join(sorted(unknown))}")
        sources = [source for source in sources if source.name in wanted]
    tiers = set(args.tier) if args.tier else {"A"}
    sources = [source for source in sources if config.profile(source.name)["tier"] in tiers]
    if not sources:
        raise SystemExit("No files selected.")

    terms = glossary.load_terms()
    state = state_module.State.load()
    client = None
    if not args.dry_run:
        try:
            client = gemini.Client(
                args.model or config.MODELS["quality"],
                pool=keys.pool(min_interval=args.min_interval, day_cooldown=args.day_cooldown * 60),
            )
        except (gemini.GeminiError, keys.NoKeys) as error:
            raise SystemExit(str(error)) from error

    replaced = reviewed = 0
    for language in args.language:
        print(f"\n{language}:")
        for source in sources:
            try:
                file_replaced, file_reviewed = review_file(
                    source, language, client, state, terms, args.dry_run, args.show_kept
                )
            except gemini.QuotaExhausted as error:
                state.save()
                print(f"\nStopped: {error}")
                return 2
            replaced += file_replaced
            reviewed += file_reviewed
            if not args.dry_run:
                state.save()

    if client:
        print(
            f"\n{replaced} of {reviewed} reviewed string(s) replaced. "
            f"{client.calls} request(s), {client.prompt_tokens} prompt tokens, "
            f"{client.output_tokens} output tokens."
        )
        print(client.pool.report())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
