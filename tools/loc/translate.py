#!/usr/bin/env python3
"""Translate localization/english into a target language with Gemini.

English is the only source. A target file is rebuilt from the English layout, so
a key the pipeline has not produced yet is simply absent and the game falls back
to English - which is always better than a stale machine translation.

Legacy values are not reused. The first run for a file discards whatever was
there; later runs keep only what this pipeline produced and recorded in
localization/.translation_state.json.

Every returned value is validated before it is written: identical markup payload,
no stray whitespace, no bare quotes, locked glossary terms present. A failing
value is retried once on its own with the problem quoted back to the model, and
if it still fails it is left out and reported.

Usage:
    export GEMINI_API_KEY=...
    python -m tools.loc.translate --language turkish --tier A
    python -m tools.loc.translate --language german --file ve_gui_l_english.yml
    python -m tools.loc.translate --language turkish --tier A --dry-run
    python -m tools.loc.translate --all                       # every language, every tier
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.loc import batching, config, gemini, glossary, keys, prompts, state as state_module, tokens, yml


def keys_summary(client: gemini.Client) -> str:
    return f"{len(client.pool.slots)} API key(s) in the pool, {client.model}"


def _items_for(source: yml.LocFile, keys: list[str]) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    for key in keys:
        english = source.entries[key].value
        kind = config.key_kind(key, english)
        item: dict[str, object] = {"key": key, "kind": kind, "english": english}
        budget = config.max_chars(key, kind, len(tokens.visible(english)))
        if budget is not None:
            item["max_chars"] = budget
        items.append(item)
    return items


def _check(key: str, english: str, value: str, language: str, terms) -> list[str]:
    kind = config.key_kind(key, english)
    budget = config.max_chars(key, kind, len(tokens.visible(english)))
    problems = [
        message
        for severity, message in tokens.validate(key, english, value, budget)
        if severity == "error"
    ]
    problems += glossary.violations(english, value, language, terms)
    return problems


def translate_file(
    source: Path,
    language: str,
    client: gemini.Client | None,
    state: state_module.State,
    terms,
    force: bool,
    dry_run: bool,
    limit: int | None,
    dirty_terms: set[str] | None = None,
    refresh_prompts: bool = False,
) -> tuple[int, int]:
    """Returns (written, failed)."""
    name = config.LANGUAGES[language][0]
    tag = config.LANGUAGES[language][1]
    profile = config.profile(source.name)
    english = yml.read(source)
    target_file = yml.target_path(config.LOC_DIR, source.name, language)

    if profile["tier"] == "X":
        # Identifier carriers: copy verbatim, no model involved.
        if not dry_run:
            yml.write(target_file, language, yml.build_target(english, language, english.values()))
        print(f"  {source.name}: copied verbatim ({len(english.entries)} keys)")
        return len(english.entries), 0

    # Values this pipeline already produced are reused; legacy machine output is
    # not. `previous` is a separate safety net: if a key fails translation we fall
    # back to whatever the file already said rather than deleting the line, which
    # would silently replace a usable string with English.
    kept: dict[str, str] = {}
    previous: dict[str, str] = {}
    if target_file.exists():
        previous = yml.read(target_file).values()
        stale_records = state.prune_absent(source.name, language, set(previous))
        if stale_records:
            print(
                f"    (dropped {len(stale_records)} record(s) for keys missing from the file: "
                f"{', '.join(stale_records[:4])})"
            )
        if not force:
            for key, value in previous.items():
                if key in english.entries and state.is_current(
                    source.name,
                    key,
                    english.entries[key].value,
                    language,
                    dirty_terms,
                    refresh_prompts,
                ):
                    kept[key] = value

    pending = [key for key in english.entries if key not in kept]
    if limit:
        pending = pending[:limit]
    if not pending:
        print(f"  {source.name}: up to date ({len(kept)} keys)")
        return 0, 0

    batches = batching.chunks(_items_for(english, pending))
    reasons = state.reasons(source.name, language, english.values(), dirty_terms, refresh_prompts)
    why = ", ".join(f"{reason}: {len(keys)}" for reason, keys in sorted(reasons.items()))
    print(
        f"  {source.name}: tier {profile['tier']}, {len(pending)} pending, "
        f"{len(batches)} request(s), {len(kept)} reused"
    )
    if why:
        print(f"    ({why})")

    if dry_run:
        first = batches[0]
        slice_ = glossary.subset_for([str(item["english"]) for item in first], language, terms)
        system, task = prompts.translation_prompt(
            language_name=name,
            tag=tag,
            filename=source.name,
            feature=profile["feature"],
            glossary_slice=slice_,
            items=first,
        )
        print("\n--- system instruction ---\n" + system)
        print("\n--- first request ---\n" + task[:4000])
        print(f"\n[dry run] {len(first)} keys in this request, "
              f"{len(slice_['mod'])} mod terms, {len(slice_['vanilla'])} vanilla terms")
        return 0, 0

    assert client is not None
    values = dict(kept)
    failures: list[tuple[str, str]] = []
    for index, batch in enumerate(batches, start=1):
        englishes = [str(item["english"]) for item in batch]
        slice_ = glossary.subset_for(englishes, language, terms)
        system, task = prompts.translation_prompt(
            language_name=name,
            tag=tag,
            filename=source.name,
            feature=profile["feature"],
            glossary_slice=slice_,
            items=batch,
        )
        try:
            answer = client.structured(system, task, gemini.TRANSLATION_SCHEMA)
        except gemini.QuotaExhausted:
            # Keep whatever this file already produced, then let the run stop.
            yml.write(target_file, language, yml.build_target(english, language, values))
            raise
        except gemini.Truncated as error:
            if len(batch) > 1:
                halves = [batch[: len(batch) // 2], batch[len(batch) // 2 :]]
                batches.extend(halves)
                print(f"    request {index}: {error}; split into two")
                continue
            failures.append((str(batch[0]["key"]), f"truncated: {error}"))
            continue
        except gemini.GeminiError as error:
            for item in batch:
                failures.append((str(item["key"]), f"request failed: {error}"))
            continue

        returned = {
            entry["key"]: tokens.normalize(entry["value"])
            for entry in answer.get("translations", [])
        }
        for item in batch:
            key = str(item["key"])
            source_value = str(item["english"])
            value = returned.get(key)
            if value is None:
                failures.append((key, "missing from the response"))
                _keep_previous(values, previous, key)
                continue
            problems = _check(key, source_value, value, language, terms)
            if problems:
                value = _retry_single(client, language, source.name, profile, item, problems, terms)
                if value is None:
                    failures.append((key, "; ".join(problems)))
                    _keep_previous(values, previous, key)
                    continue
            values[key] = value
            state.record(source.name, key, source_value, language, client.model)
        print(f"    request {index}/{len(batches)}: {len(returned)} values")

    yml.write(target_file, language, yml.build_target(english, language, values))
    state.drop_missing(source.name, set(english.entries))
    for key, reason in failures:
        print(f"    ! {key}: {reason}")
    return len(values) - len(kept), len(failures)


def _keep_previous(values: dict[str, str], previous: dict[str, str], key: str) -> None:
    """A failed key keeps the file's earlier string instead of vanishing.

    The value is deliberately not recorded in the state file, so the next run
    treats the key as pending and tries again.
    """
    if key in previous:
        values[key] = previous[key]


def _retry_single(
    client: gemini.Client,
    language: str,
    filename: str,
    profile: dict[str, str],
    item: dict[str, object],
    problems: list[str],
    terms,
) -> str | None:
    """Second and final attempt for one value, with the defect quoted back."""
    name, tag = config.LANGUAGES[language]
    slice_ = glossary.subset_for([str(item["english"])], language, terms)
    repaired = dict(item)
    repaired["fix_these_problems"] = problems
    system, task = prompts.translation_prompt(
        language_name=name,
        tag=tag,
        filename=filename,
        feature=profile["feature"],
        glossary_slice=slice_,
        items=[repaired],
    )
    try:
        answer = client.structured(system, task, gemini.TRANSLATION_SCHEMA)
    except gemini.GeminiError:
        return None
    for entry in answer.get("translations", []):
        if entry["key"] == item["key"]:
            value = tokens.normalize(entry["value"])
            if not _check(str(item["key"]), str(item["english"]), value, language, terms):
                return value
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--language", choices=sorted(config.LANGUAGES), action="append")
    parser.add_argument("--file", action="append", help="English filename, e.g. ve_gui_l_english.yml")
    parser.add_argument("--tier", action="append", choices=["A", "B", "C", "X"])
    parser.add_argument("--all", action="store_true", help="Every language and every tier.")
    parser.add_argument("--model", help="Override the model for this run.")
    parser.add_argument("--limit", type=int, help="Translate at most N keys per file (for a trial run).")
    parser.add_argument("--force", action="store_true", help="Retranslate keys already recorded as current.")
    parser.add_argument(
        "--refresh-prompts",
        action="store_true",
        help="Also retranslate keys produced by an older prompt generation.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print the plan and the first request; no network.")
    parser.add_argument(
        "--min-interval", type=float, default=0.0, help="Seconds between calls, per key."
    )
    parser.add_argument(
        "--day-cooldown",
        type=float,
        default=360.0,
        help="Minutes to rest a key whose daily allowance is spent (default 360).",
    )
    args = parser.parse_args()

    languages = sorted(config.LANGUAGES) if args.all else (args.language or [])
    if not languages:
        parser.error("choose --language (repeatable) or --all")

    sources = yml.english_files(config.ENGLISH_DIR)
    if args.file:
        wanted = set(args.file)
        unknown = wanted - {source.name for source in sources}
        if unknown:
            raise SystemExit(f"Unknown English file(s): {', '.join(sorted(unknown))}")
        sources = [source for source in sources if source.name in wanted]
    tiers = set(args.tier) if args.tier else {"A", "B", "C", "X"}
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
        print(keys_summary(client))

    written = failed = 0
    for language in languages:
        print(f"\n{language}:")
        dirty_terms = state.dirty_terms(language, terms)
        if dirty_terms:
            print(f"  glossary changed: {', '.join(sorted(dirty_terms)[:6])}")
        for source in sources:
            if client and not args.model:
                # Tier C is formulaic; the cheaper model is enough for it.
                tier = config.profile(source.name)["tier"]
                wanted_model = config.MODELS["bulk"] if tier == "C" else config.MODELS["quality"]
                if client.model != wanted_model:
                    # Same pool, same counters, same key cooldowns - only the model
                    # changes, and quota is tracked per key *and* model.
                    client = gemini.Client(wanted_model, pool=client.pool)
            try:
                file_written, file_failed = translate_file(
                    source,
                    language,
                    client,
                    state,
                    terms,
                    args.force,
                    args.dry_run,
                    args.limit,
                    dirty_terms,
                    args.refresh_prompts,
                )
            except gemini.QuotaExhausted as error:
                state.save()
                print(f"\nStopped: {error}")
                print(
                    "Nothing already translated was lost. Options: wait for the quota window to "
                    "reset, point GEMINI_MODEL_QUALITY at a model with quota left "
                    "(or pass --model), or enable billing on the key. Re-running continues "
                    "from where it stopped."
                )
                return 2
            written += file_written
            failed += file_failed
            if not args.dry_run:
                state.save()
        if not args.dry_run:
            # The termbase this language was translated against is now recorded,
            # so the next run can tell which keys a term change invalidated.
            state.snapshot_glossary(language, terms)
            state.save()

    if client:
        print(
            f"\n{written} value(s) written, {failed} failure(s). "
            f"{client.calls} request(s), {client.prompt_tokens} prompt tokens, "
            f"{client.output_tokens} output tokens."
        )
        print(client.pool.report())
        print("Run `loc verify` before packaging.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
