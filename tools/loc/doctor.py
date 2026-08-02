#!/usr/bin/env python3
"""`loc doctor` - check the setup and say what to do next.

Everything a first run needs, in one command: Python version, the mod's own
localization, the game installation the vocabulary is read from, the glossary,
the API keys, and how far the translation has got. Nothing here calls the API.

Exit code 1 means something blocks a run.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.loc import config, glossary, keys, state as state_module, yml

OK = "[ ok ]"
WARN = "[ !! ]"
FAIL = "[fail]"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.parse_args()

    problems = 0
    warnings = 0
    next_steps: list[str] = []

    print("Victoria Universalis IV - localization setup\n")

    # 1. Python -----------------------------------------------------------------
    version = sys.version_info
    if version >= (3, 10):
        print(f"{OK} Python {version.major}.{version.minor}.{version.micro} (3.10+ required)")
    else:
        problems += 1
        print(f"{FAIL} Python {version.major}.{version.minor} is too old; 3.10 or newer is required")
    print(f"{OK} no third-party packages needed")

    # 2. The mod's own localization --------------------------------------------
    sources = yml.english_files(config.ENGLISH_DIR)
    if not sources:
        problems += 1
        print(f"{FAIL} no English localization found in {config.ENGLISH_DIR}")
        print("       run this from the mod's root directory")
    else:
        keys_total = sum(len(yml.read(source).entries) for source in sources)
        print(f"{OK} source text: {len(sources)} file(s), {keys_total} key(s) in {config.ENGLISH_DIR.name}/")
        missing_dirs = [
            language
            for language in config.LANGUAGES
            if not (config.LOC_DIR / language).is_dir()
        ]
        if missing_dirs:
            warnings += 1
            print(f"{WARN} no folder yet for: {', '.join(missing_dirs)} (they will be created)")

    # 3. The game, for its vocabulary ------------------------------------------
    game = config.VANILLA_GAME_DIR
    if (game / "localization" / "english").is_dir():
        print(f"{OK} Victoria 3 found: {game}")
    else:
        warnings += 1
        print(f"{WARN} Victoria 3 not found (looked at {game})")
        print("       set VICTORIA3_GAME_DIR to the game's `game` folder")
        print("       without it, `loc vanilla` cannot refresh the game's own vocabulary")

    vanilla_files = sorted(config.VANILLA_GLOSSARY_DIR.glob("*.json"))
    if len(vanilla_files) >= len(config.LANGUAGES):
        counts = {path.stem: len(glossary.load_vanilla(path.stem)) for path in vanilla_files}
        smallest = min(counts.values())
        print(f"{OK} game vocabulary extracted for {len(vanilla_files)} language(s), {smallest}+ terms each")
    else:
        warnings += 1
        print(f"{WARN} game vocabulary missing for some languages ({len(vanilla_files)} of {len(config.LANGUAGES)})")
        next_steps.append("loc vanilla            # read the game's own words")

    # 4. Glossary ---------------------------------------------------------------
    terms = glossary.load_terms()
    if not terms:
        problems += 1
        print(f"{FAIL} no terms in {config.TERMS_FILE}")
    else:
        print(f"{OK} termbase: {len(terms)} canonical term(s)")
        decided: list[str] = []
        undecided: list[str] = []
        for language in sorted(config.LANGUAGES):
            decisions = glossary.load_decisions(language)
            done = sum(1 for term in terms if decisions.get(term) and decisions[term].translation)
            (decided if done == len(terms) else undecided).append(f"{language}({done})")
        if decided:
            print(f"       decided: {', '.join(decided)}")
        if undecided:
            warnings += 1
            print(f"{WARN} undecided termbase: {', '.join(undecided)}")
            next_steps.append("loc terms <language>   # propose glossary candidates")

    # 5. Keys -------------------------------------------------------------------
    registry = keys.Registry()
    environment = {keys.fingerprint(key) for key in keys.keys_from_environment()}
    usable = [
        entry
        for entry in registry.entries
        if not entry.paused and (entry.key or entry.fingerprint in environment)
    ]
    if usable:
        print(f"{OK} API keys: {len(usable)} in rotation ({', '.join(entry.name for entry in usable)})")
        paused = [entry.name for entry in registry.entries if entry.paused]
        if paused:
            print(f"       paused: {', '.join(paused)}")
        cooling = [
            entry.name
            for entry in usable
            if any(deadline > 0 for deadline in entry.cooldowns.values())
        ]
        if cooling:
            print(f"       resting: {', '.join(cooling)} (see `loc keys`)")
        spent = sum(entry.calls for entry in registry.entries)
        if spent:
            tokens = sum(entry.prompt_tokens + entry.output_tokens for entry in registry.entries)
            print(f"       used so far: {spent} call(s), {tokens / 1000:.0f}k token(s)")
    else:
        problems += 1
        print(f"{FAIL} no usable API key")
        print(f"       registry: {registry.path}")
        next_steps.insert(0, "loc keys add <name>    # add a Gemini API key (hidden prompt)")

    # 6. Progress ---------------------------------------------------------------
    if sources and terms:
        state = state_module.State.load()
        totals: list[str] = []
        for language in sorted(config.LANGUAGES):
            dirty = state.dirty_terms(language, terms)
            done = 0
            total = 0
            for source in sources:
                values = yml.read(source).values()
                total += len(values)
                done += len(values) - len(state.pending(source.name, language, values, dirty))
            share = round(100 * done / total) if total else 0
            totals.append(f"{language} {share}%")
        print(f"{OK} translated: {', '.join(totals)}")
        if any(not part.endswith(" 100%") for part in totals):
            next_steps.append("loc sync <language>    # translate what is pending")
        next_steps.append("loc verify             # quality gate before packaging")

    # -- verdict ---------------------------------------------------------------
    print()
    if problems:
        print(f"{problems} thing(s) block a run, {warnings} warning(s).")
    elif warnings:
        print(f"Ready, with {warnings} warning(s).")
    else:
        print("Everything checks out.")

    if next_steps:
        print("\nNext:")
        seen = set()
        for step in next_steps:
            if step not in seen:
                seen.add(step)
                print(f"  {step}")

    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
