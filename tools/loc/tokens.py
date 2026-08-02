#!/usr/bin/env python3
"""Markup handling and output validation for translated localization values.

A translated value is only accepted when it carries exactly the same technical
payload as its English source: the same script scopes, variable references,
icons, colour tags, and line breaks, in the same quantity. Everything else in
this module exists to catch the failure modes the old Google-endpoint pipeline
shipped into the repository - lost tokens, stray whitespace, bare quotes, and
labels too long for their frame.
"""
from __future__ import annotations

import re

# Order matters: `#!` must be tried before `#word`, and `\n` before a bare `\`.
TOKEN = re.compile(
    r"("
    r"\[[^\]]*\]"  # [GetPlayer.GetName], [concept_authority], [Nbsp]
    r"|\$[^$]*\$"  # $ve_piety_tt$
    r"|£[^£]*£"  # £money£ style icons
    r"|@[^@!\s]+!"  # @bur! texticons
    r"|#!"  # end-of-format marker
    r"|#[A-Za-z_]+"  # #Y #P #bold #tooltippable_concept
    r"|\\n"  # literal line break
    r"|\\t"
    r")"
)

# Concept references must survive verbatim; they are the game's own vocabulary.
CONCEPT = re.compile(r"\[(concept_[a-z0-9_]+)\]|\$(concept_[a-z0-9_]+)\$")


def normalize(value: str) -> str:
    """Repair a model's line breaks into the form the game's parser needs.

    A localization value is one physical line and writes its breaks as the two
    characters backslash-n. A model answering in JSON may express the same break
    as "\\n", which json.loads decodes into a real newline character - the game
    would then see a truncated line instead of a break. Since a real newline can
    never be legal in a value, any that arrives was meant as a game line break.

    Observed live: the same prompt produced literal breaks for German and real
    newlines for Turkish, which silently dropped the whole entry.
    """
    return (
        value.replace("\r\n", "\\n")
        .replace("\r", "\\n")
        .replace("\n", "\\n")
        .replace("\t", "\\t")
    )


def tokens(value: str) -> list[str]:
    return TOKEN.findall(value)


def token_counts(value: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for token in tokens(value):
        counts[token] = counts.get(token, 0) + 1
    return counts


def visible(value: str) -> str:
    """The part a player actually reads, with markup and icons removed."""
    stripped = TOKEN.sub("", value)
    return re.sub(r"\s+", " ", stripped).strip()


def concepts(value: str) -> set[str]:
    return {a or b for a, b in CONCEPT.findall(value)}


def _edge_whitespace(value: str) -> tuple[str, str]:
    return value[: len(value) - len(value.lstrip())], value[len(value.rstrip()) :]


def validate(
    key: str,
    english: str,
    translated: str,
    max_chars: int | None = None,
) -> list[tuple[str, str]]:
    """Return (severity, message) pairs; an empty list means the value is publishable.

    Severity "error" blocks a release. Severity "warn" is a judgement call: the
    length budget is derived from the English string, so it flags suspicion, not
    certainty.
    """
    problems: list[tuple[str, str]] = []

    if not translated.strip():
        problems.append(("error", "empty value"))
        return problems

    # Edge whitespace is sometimes deliberate ("Bonus: " is concatenated with a
    # value), so only a difference from English is a defect.
    if _edge_whitespace(translated) != _edge_whitespace(english):
        problems.append(("error", "leading or trailing whitespace differs from English"))

    if re.search(r'(?<!\\)"', translated):
        problems.append(("error", "unescaped double quote"))

    source_counts = token_counts(english)
    target_counts = token_counts(translated)
    if source_counts != target_counts:
        lost = {t: n - target_counts.get(t, 0) for t, n in source_counts.items() if n > target_counts.get(t, 0)}
        gained = {t: n - source_counts.get(t, 0) for t, n in target_counts.items() if n > source_counts.get(t, 0)}
        detail = []
        if lost:
            detail.append("lost " + ", ".join(f"{t!r}x{n}" for t, n in sorted(lost.items())))
        if gained:
            detail.append("added " + ", ".join(f"{t!r}x{n}" for t, n in sorted(gained.items())))
        problems.append(("error", "token mismatch: " + "; ".join(detail)))

    if visible(english) and not visible(translated):
        problems.append(("error", "prose dropped, only markup left"))

    if max_chars is not None:
        length = len(visible(translated))
        if length > max_chars:
            problems.append(
                ("warn", f"may not fit its frame: {length} visible characters, budget {max_chars}")
            )

    return problems


def looks_untranslated(english: str, translated: str) -> bool:
    """True when a target value is still the English string.

    Short cognates ('Ambition', 'Bonus') are legitimately identical in several
    languages, so only values with a real word of Latin prose are reported.
    """
    if visible(english) != visible(translated):
        return False
    return bool(re.search(r"[A-Za-z]{4}", visible(english)))
