#!/usr/bin/env python3
"""One entry point for the whole localization pipeline.

    python -m tools.loc                 interactive menu (nothing to memorise)
    python -m tools.loc doctor          check the setup and say what to do next
    python -m tools.loc status
    python -m tools.loc sync turkish
    python -m tools.loc sync all

`sync` is the useful one: it runs the steps in the order they depend on each
other - glossary candidates, then translation of whatever is pending, then the
review pass over the chrome, then the quality gate - and skips every step that
has nothing to do. Running it twice in a row costs one status check and no API
calls.

Every subcommand forwards unknown flags to the underlying module, so
`python -m tools.loc translate turkish --limit 20 --dry-run` works.
"""
from __future__ import annotations

import contextlib
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.loc import config, doctor, glossary, keys, propose_terms, review, state as state_module, translate, verify
from tools.loc import vanilla_terms, yml

STEPS = """\
The pipeline, in order:

  1  vanilla     read the game's own vocabulary  (no API key needed)
  2  terms       propose glossary candidates for the mod's 88 terms
     -           you review localization/glossary/<language>.tsv and lock what you accept
  3  translate   translate every key that is new or stale
  4  review      native reviewer over the interface text (tier A)
  5  verify      quality gate: markup, whitespace, locked terms  (no API key needed)

  doctor         is everything set up? what should I do next?
  status         what is done and what is pending, per file and language
  keys           the API key pool: how many keys, which are resting
  sync           1-5 in order, skipping whatever has nothing to do\
"""


@contextlib.contextmanager
def argv(args: list[str]):
    original = sys.argv
    sys.argv = [original[0]] + args
    try:
        yield
    finally:
        sys.argv = original


def call(module, args: list[str]) -> int:
    with argv(args):
        try:
            return module.main() or 0
        except SystemExit as stop:
            # A SystemExit carries either an exit code or a message meant for the
            # user; printing the message and returning 1 is what a bare script
            # would do, and it keeps the menu alive instead of dumping a traceback.
            code = stop.code
            if code is None:
                return 0
            if isinstance(code, int):
                return code
            print(code)
            return 1


def languages_from(token: str) -> list[str]:
    if token in ("all", "*"):
        return sorted(config.LANGUAGES)
    if token in config.LANGUAGES:
        return [token]
    matches = [language for language in config.LANGUAGES if language.startswith(token)]
    if len(matches) == 1:
        return matches
    raise SystemExit(
        f"Unknown language {token!r}. Choose one of: {', '.join(sorted(config.LANGUAGES))}, or 'all'."
    )


def sync(languages: list[str], extra: list[str], dry_run: bool = False) -> int:
    """Run the whole pipeline for the given languages, skipping finished steps."""
    terms = glossary.load_terms()
    worst = 0

    # Step 0: the encoding of the *source*. Everything this pipeline writes is
    # UTF-8 with a BOM by construction, but the English files are edited by hand,
    # and an editor that drops the BOM turns every accent into mojibake in game.
    # The repair is byte-safe and idempotent, so it runs before every sync.
    if not dry_run:
        repaired = [
            (path, changes)
            for path, changes in (
                (path, yml.fix_encoding(path)) for path in sorted(config.LOC_DIR.glob("*/*.yml"))
            )
            if changes
        ]
        if repaired:
            print(f"\n-- encoding: repaired {len(repaired)} file(s)")
            for path, changes in repaired[:10]:
                print(f"   {path.relative_to(config.MOD_ROOT)}: {', '.join(changes)}")

    for language in languages:
        print(f"\n{'=' * 72}\n{language}\n{'=' * 72}")

        decisions = glossary.load_decisions(language)
        undecided = [term for term in terms if not (decisions.get(term) and decisions[term].translation)]
        if undecided:
            print(f"\n-- glossary: {len(undecided)} term(s) undecided")
            code = call(propose_terms, ["--language", language] + extra + (["--dry-run"] if dry_run else []))
            worst = max(worst, code)
            if code == 2:  # quota
                return 2
            print(
                f"\n   Review localization/glossary/{language}.tsv and change the ones you accept "
                "from `candidate` to `locked`."
            )
        else:
            print("\n-- glossary: all terms decided")

        print("\n-- translate")
        code = call(translate, ["--language", language] + extra + (["--dry-run"] if dry_run else []))
        worst = max(worst, code)
        if code == 2:
            return 2

        print("\n-- review (interface text)")
        code = call(review, ["--language", language] + extra + (["--dry-run"] if dry_run else []))
        worst = max(worst, code)
        if code == 2:
            return 2

    print(f"\n{'=' * 72}\nverify\n{'=' * 72}")
    worst = max(worst, call(verify, [arg for arg in extra if arg.startswith("--strict")]))
    return worst


def menu() -> int:
    state = state_module.State.load()
    terms = glossary.load_terms()
    while True:
        print("\n" + "=" * 72)
        print("Victoria Universalis IV - localization")
        print("=" * 72)
        print(STEPS)
        print(
            "\n  d) doctor        s) status       t) terms            x) translate"
            "\n  r) review        v) verify       y) sync             g) game vocabulary"
            "\n  k) keys          q) quit"
        )
        try:
            choice = input("\n> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        if choice in ("q", "quit", "exit"):
            return 0
        if choice in ("s", "status"):
            state = state_module.State.load()
            state_module.overview(state, terms)
            continue
        if choice in ("g", "vanilla"):
            call(vanilla_terms, [])
            continue
        if choice in ("v", "verify"):
            call(verify, [])
            continue
        if choice in ("k", "keys"):
            call(keys, [])
            continue
        if choice in ("d", "doctor"):
            call(doctor, [])
            continue

        actions = {"t": propose_terms, "x": translate, "r": review, "y": None}
        if choice not in actions:
            print("Not a choice.")
            continue

        print(f"\nLanguages: {', '.join(sorted(config.LANGUAGES))}, or 'all'")
        try:
            token = input("language> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        try:
            chosen = languages_from(token)
        except SystemExit as error:
            print(error)
            continue

        trial = input("trial run first (no API calls)? [Y/n] ").strip().lower() not in ("n", "no")
        extra = ["--dry-run"] if trial else []
        if not trial:
            # Free-tier keys allow 15 requests a minute; 4.5s per key keeps a run
            # under that instead of hitting the limit and waiting it out.
            pace = input("seconds between calls, per key [4.5] ").strip() or "4.5"
            try:
                float(pace)
            except ValueError:
                print(f"{pace!r} is not a number; using 4.5")
                pace = "4.5"
            extra += ["--min-interval", pace]

        if choice == "y":
            sync(chosen, extra if not trial else [], dry_run=trial)
        else:
            module = actions[choice]
            for language in chosen:
                call(module, ["--language", language] + extra)
        state = state_module.State.load()


def main() -> int:
    args = sys.argv[1:]
    if not args:
        return menu()

    command, rest = args[0], args[1:]

    if command in ("help", "-h", "--help"):
        print(__doc__)
        print(STEPS)
        return 0

    if command == "status":
        return call(state_module, rest)

    if command in ("vanilla", "game"):
        return call(vanilla_terms, rest)

    if command == "verify":
        return call(verify, rest)

    if command == "keys":
        return call(keys, rest)

    if command in ("doctor", "check", "setup"):
        return call(doctor, rest)

    if command in ("terms", "translate", "review", "sync"):
        if not rest:
            raise SystemExit(f"Which language? e.g. `python -m tools.loc {command} turkish` or `... all`")
        chosen = languages_from(rest[0])
        extra = rest[1:]
        if command == "sync":
            return sync(chosen, extra)
        module = {"terms": propose_terms, "translate": translate, "review": review}[command]
        worst = 0
        for language in chosen:
            worst = max(worst, call(module, ["--language", language] + extra))
        return worst

    raise SystemExit(f"Unknown command {command!r}. Try `python -m tools.loc help`.")


if __name__ == "__main__":
    raise SystemExit(main())
