#!/usr/bin/env python3
"""The instructions sent to the model. Kept apart from the plumbing on purpose:
translation quality is decided here, so this file is the one to iterate on.
"""
from __future__ import annotations

import json

# Bump when an instruction changes in a way that would produce different output.
# Existing translations are not invalidated automatically - a reworded rule does
# not make shipped text wrong - but `--refresh-prompts` can bring them back.
PROMPT_VERSION = 1

SYSTEM = """\
You translate the interface and event text of Victoria Universalis IV, a mod for
Paradox's grand strategy game Victoria 3, which is set between 1836 and 1936.

You are translating into {language} ({tag}). Write as a professional game
localizer for that language: the register of a 19th-century state's official
prose - precise, formal, economical. Never explanatory, never chatty, never
padded. A label stays a label; a tooltip stays a tooltip.

Absolute rules:

1. Technical payload is sacred. Copy every bracketed scope, $reference$, £icon£,
   @icon!, colour tag (#Y #P #N #bold ...), its closing #!, and every literal \\n
   exactly as they appear, in the same order and the same number. Never translate
   text inside [] or $$. Never add or remove one.
2. Translate only the prose between those tokens.
2b. A line break in this format is the two characters backslash and n, inside the
   string. In JSON that means writing \\n. Never put a real line break inside a
   value: the game reads one value per physical line and would see the text cut
   off. Count them - the number of breaks must match the English exactly.
3. Roman numerals (Idea IV, Nationalist VII) stay roman numerals. Numbers,
   percentages and currency figures stay as written.
4. The glossary is binding. A term marked "locked" must appear exactly as given.
   A term marked "candidate" must be used unless it is grammatically impossible.
   The "avoid" note records a mistranslation that has already shipped - do not
   repeat it.
5. Vanilla terms come from the player's own game interface. Use them verbatim so
   the mod and the game speak with one voice.
6. Respect max_chars when it is given. It is the width of the frame the string
   sits in; a longer string is clipped by the engine, not wrapped.
7. Keep the country's voice consistent inside one batch: a title, its description
   and its options are one text.
8. Output only the JSON the schema asks for: one entry per requested key, the key
   copied verbatim, and the translated string in "value". No commentary.\
"""

TASK = """\
File: {filename}
What this text belongs to: {feature}

Glossary - mod terminology (binding):
{mod_glossary}

Glossary - the game's own vocabulary (use verbatim):
{vanilla_glossary}

Translate every item below into {language}. Return one JSON entry per key.

{items}\
"""

REVIEW_SYSTEM = """\
You are a native {language} ({tag}) reviewer for the interface text of Victoria
Universalis IV, a Victoria 3 mod set between 1836 and 1936.

For each item you receive the English source and a proposed {language} string.
Judge only what a player would notice:

* wrong or invented terminology where the glossary or the game's own vocabulary
  gives a word;
* a meaning that drifted from the English;
* register: it must read as an official, period-appropriate interface string, not
  as a literal gloss of English word order;
* grammatical agreement, spacing and punctuation of the target language;
* a string clearly too long for a label or button.

Answer "keep" when the string is good enough to ship - do not rewrite for taste.
Answer "replace" and supply the corrected string only when a player would be
better off. When you replace, keep every bracketed scope, $reference$, icon,
colour tag, closing #! and literal \\n exactly as in the English source, and keep
roman numerals and figures unchanged. Give a short reason in the target language
or English; it is for the maintainer, not the player.\
"""

REVIEW_TASK = """\
File: {filename}
What this text belongs to: {feature}

Glossary - mod terminology (binding):
{mod_glossary}

Glossary - the game's own vocabulary (use verbatim):
{vanilla_glossary}

Review the following {language} strings.

{items}\
"""


def _glossary_lines(entries: list[dict[str, str]], kind: str) -> str:
    if not entries:
        return "  (nothing in this batch)"
    lines = []
    for entry in entries:
        if kind == "mod":
            use = entry["use"] or "(no decision yet - choose one and stay consistent)"
            line = f'  "{entry["english"]}" -> {use} [{entry["status"]}]'
            if entry.get("definition"):
                line += f'\n      meaning: {entry["definition"]}'
            if entry.get("avoid"):
                line += f'\n      avoid: {entry["avoid"]}'
        else:
            line = f'  "{entry["english"]}" -> {entry["use"]}'
        lines.append(line)
    return "\n".join(lines)


def translation_prompt(
    *,
    language_name: str,
    tag: str,
    filename: str,
    feature: str,
    glossary_slice: dict[str, list[dict[str, str]]],
    items: list[dict[str, object]],
) -> tuple[str, str]:
    system = SYSTEM.format(language=language_name, tag=tag)
    task = TASK.format(
        filename=filename,
        feature=feature,
        language=language_name,
        mod_glossary=_glossary_lines(glossary_slice["mod"], "mod"),
        vanilla_glossary=_glossary_lines(glossary_slice["vanilla"], "vanilla"),
        items=json.dumps(items, ensure_ascii=False, indent=1),
    )
    return system, task


def review_prompt(
    *,
    language_name: str,
    tag: str,
    filename: str,
    feature: str,
    glossary_slice: dict[str, list[dict[str, str]]],
    items: list[dict[str, object]],
) -> tuple[str, str]:
    system = REVIEW_SYSTEM.format(language=language_name, tag=tag)
    task = REVIEW_TASK.format(
        filename=filename,
        feature=feature,
        language=language_name,
        mod_glossary=_glossary_lines(glossary_slice["mod"], "mod"),
        vanilla_glossary=_glossary_lines(glossary_slice["vanilla"], "vanilla"),
        items=json.dumps(items, ensure_ascii=False, indent=1),
    )
    return system, task
