#!/usr/bin/env python3
"""Shared configuration for the Victoria Universalis IV localization pipeline.

The pipeline is source-driven: `localization/english` is the only authority for
keys and meaning. Target languages are rebuilt from it, never edited in place.

Nothing here reaches out to the network; the Gemini client keeps its own module.
"""
from __future__ import annotations

import os
from pathlib import Path

# --- paths -------------------------------------------------------------------

MOD_ROOT = Path(__file__).resolve().parents[2]
LOC_DIR = MOD_ROOT / "localization"
ENGLISH_DIR = LOC_DIR / "english"
GLOSSARY_DIR = LOC_DIR / "glossary"
VANILLA_GLOSSARY_DIR = GLOSSARY_DIR / "vanilla"
TERMS_FILE = GLOSSARY_DIR / "terms.tsv"
STATE_FILE = LOC_DIR / ".translation_state.json"
# API keys, their names, usage and cooldowns live OUTSIDE the repository - see
# tools/loc/keys.py registry_path(). Nothing key-related is stored here.

# Read-only reference. Override with VICTORIA3_GAME_DIR when the install moves.
VANILLA_GAME_DIR = Path(
    os.environ.get(
        "VICTORIA3_GAME_DIR",
        r"C:\Program Files (x86)\Steam\steamapps\common\Victoria 3\game",
    )
)

# --- languages ---------------------------------------------------------------

# Directory name -> (name used when instructing the model, BCP-47 tag).
LANGUAGES: dict[str, tuple[str, str]] = {
    "braz_por": ("Brazilian Portuguese", "pt-BR"),
    "french": ("French", "fr-FR"),
    "german": ("German", "de-DE"),
    "japanese": ("Japanese", "ja-JP"),
    "korean": ("Korean", "ko-KR"),
    "polish": ("Polish", "pl-PL"),
    "russian": ("Russian", "ru-RU"),
    "simp_chinese": ("Simplified Chinese", "zh-CN"),
    "spanish": ("Spanish", "es-ES"),
    "turkish": ("Turkish", "tr-TR"),
}

# --- models ------------------------------------------------------------------

# Single place where model names live, so a version bump is a one-line change.
# Both can be overridden per shell, which is how you move the whole pipeline onto
# one model when an account's quota only stretches to the cheaper tier.
MODELS = {
    # tier A/B prose, glossary candidates, review pass
    "quality": os.environ.get("GEMINI_MODEL_QUALITY", "gemini-3.5-flash-lite"),
    # tier C sweeps
    "bulk": os.environ.get("GEMINI_MODEL_BULK", "gemini-3.1-flash-lite"),
}

# --- per-file profiles -------------------------------------------------------

# tier A: player-facing chrome (labels, buttons, event titles/options, tooltips
#         a player reads constantly) - translated by the quality model and then
#         sent through the review pass.
# tier B: long event and Journal Entry prose - quality model, no review pass.
# tier C: formulaic modifier names - bulk model, glossary does the work.
# tier X: not prose; never sent to a model.
FILE_PROFILES: dict[str, dict[str, str]] = {
    "sulius_ui_l_english.yml": {
        "tier": "A",
        "feature": "Overrides of vanilla topbar tooltips (legitimacy, money, research). "
        "Wording must match the vanilla game's own tooltips.",
    },
    "ve_age_l_english.yml": {
        "tier": "A",
        "feature": "Ages and Era Momentum: three Ages with seven objectives each, "
        "Era Rewards bought with Era Momentum, and once-per-campaign Golden Ages.",
    },
    "ve_country_ideas_l_english.yml": {
        "tier": "B",
        "feature": "National Ideas: per-country profiles of two Traditions, seven "
        "National Ideas and one National Bonus, unlocked by purchased idea levels.",
    },
    "ve_country_panel_l_english.yml": {
        "tier": "A",
        "feature": "Read-only National Doctrine section on the country panel, shown "
        "for any country: resources, idea groups, models, meters, Era standing.",
    },
    "ve_culture_l_english.yml": {
        "tier": "A",
        "feature": "National Identity page: Identity Models, Cultural Mandate, "
        "National Cohesion meter and Cultural Projects.",
    },
    "ve_doctrine_journeys_l_english.yml": {
        "tier": "B",
        "feature": "Doctrine Journeys: multi-year Journal Entries tied to an idea "
        "group, measuring building levels and country conditions for a reward.",
    },
    "ve_era_crossroads_l_english.yml": {
        "tier": "B",
        "feature": "Era Crossroads: one strategic Journey per Age with three routes "
        "anchored to objectives the country already secured.",
    },
    "ve_flavor_events_l_english.yml": {
        "tier": "B",
        "feature": "Legacy idea-group flavor events (not currently dispatched).",
    },
    "ve_gui_l_english.yml": {
        "tier": "A",
        "feature": "Panel chrome: tab names, buttons, state-panel project cards, "
        "topbar chips, alerts. Space is tight; keep labels short.",
    },
    "ve_idea_ambient_events_l_english.yml": {
        "tier": "B",
        "feature": "Idea Group ambient events: dilemmas, opportunities and setbacks "
        "raised by an embraced idea group.",
    },
    "ve_idea_l_english.yml": {
        "tier": "A",
        "feature": "Ideas page: 21 idea groups in Production/Society/Military, "
        "National Insight costs, group capacity and Doctrine Implementation Strain.",
    },
    "ve_ledger_l_english.yml": {
        "tier": "A",
        "feature": "Doctrine Ledger: a sortable, filterable, paged table comparing "
        "every country's doctrine standing. Column headers must stay very short.",
    },
    "ve_modifiers_l_english.yml": {
        "tier": "C",
        "feature": "Modifier display names. Mostly formulaic: '<Group> Idea <roman "
        "numeral>', '<Group> Ambition', National Idea and Era Reward names.",
    },
    "ve_project_events_l_english.yml": {
        "tier": "B",
        "feature": "Religious and Cultural Project incidents: administrative "
        "disputes, crises that can cancel a project, and rare breakthroughs.",
    },
    "ve_religion_aspect_icons_l_english.yml": {
        "tier": "X",
        "feature": "GUI texticon identifiers, not prose. Copied verbatim.",
    },
    "ve_religion_l_english.yml": {
        "tier": "A",
        "feature": "Religion page: Religious Models, the Religious Settlement meter, "
        "Piety Reform, eight Religious Programs per model, Religious Projects.",
    },
    "ve_tag_flavor_l_english.yml": {
        "tier": "B",
        "feature": "Country flavor chains for the Ottomans, Japan and the United "
        "States, each with three routes and a delayed closure.",
    },
    "ve_transition_journeys_l_english.yml": {
        "tier": "B",
        "feature": "Religious Settlement and National Compact transition Journeys "
        "that run while a model change is being absorbed.",
    },
    "ve_welcome_l_english.yml": {
        "tier": "A",
        "feature": "Game-start popup summarising the mod's systems.",
    },
}

DEFAULT_PROFILE = {"tier": "B", "feature": "Victoria Universalis IV mod text."}


def profile(filename: str) -> dict[str, str]:
    return FILE_PROFILES.get(filename, DEFAULT_PROFILE)


# --- key kinds ---------------------------------------------------------------

# Ordered longest-match-first; the first rule whose test passes wins.
def key_kind(key: str, value: str) -> str:
    lowered = key.lower()
    if lowered.endswith((".t", "_title")) or "_title_" in lowered:
        return "event_title"
    if lowered.endswith(".f"):
        return "event_flavor"
    if lowered.endswith((".d", "_desc", "_description", "_reason")):
        return "event_description"
    if any(lowered.endswith("." + letter) for letter in "abcdefghij"):
        return "event_option"
    if lowered.endswith((".tt", "_tt", "_tooltip", "_hint")):
        return "tooltip"
    if lowered.endswith(("_button", "_button_short", "_short")):
        return "button"
    if lowered.endswith("_mdf") or "_idea_" in lowered or lowered.endswith("_ambition"):
        return "modifier"
    if lowered.endswith(("_label", "_name", "_status")) or key.isupper():
        return "label"
    if len(value) > 200:
        return "paragraph"
    return "label"


# --- length budgets ----------------------------------------------------------

# The panels are pixel-budgeted (see MECHANICS_REFERENCE.md 9.0 and 9.2), so a
# long translation does not wrap - it clips or pushes a card out of its frame.
# Visible length is measured after markup tokens are removed.
#
# The budget is relative to English, because the English string is what the frame
# was authored around. A translation may run somewhat longer - German and Russian
# always do - but not half again as long.
LENGTH_FACTOR_BY_KIND = {
    "button": 1.30,
    "label": 1.40,
}
LENGTH_SLACK = 6

# Keys that sit in the tightest frames. Exact keys win over kind defaults.
MAX_CHARS_BY_KEY = {
    # Doctrine Ledger column headers
    "VE_LG_COL_RANK": 12,
    "VE_LG_COL_INSIGHT": 14,
    "VE_LG_COL_GROUPS": 14,
    "VE_LG_COL_IDEAS": 14,
    "VE_LG_COL_NATIONAL_IDEAS": 20,
    "VE_LG_COL_RELIGION": 20,
    "VE_LG_COL_IDENTITY": 20,
    "VE_LG_COL_ERA": 14,
    # Panel tab row
    "VE_IDEAS": 16,
    "VE_RELIGION": 16,
    "VE_CULTURE": 16,
    "VE_AGE": 16,
    "VE_LEDGER": 16,
}


def max_chars(key: str, kind: str, english_length: int) -> int | None:
    """Visible-character budget for a translated value, or None when unbounded."""
    factor = LENGTH_FACTOR_BY_KIND.get(kind)
    relative = int(english_length * factor) + LENGTH_SLACK if factor else None
    hard = MAX_CHARS_BY_KEY.get(key)
    if hard is None:
        return relative
    # A hard cap only applies when the English string itself respects it;
    # otherwise the cap is stale and the relative budget is the honest check.
    if english_length > hard:
        return relative
    return hard if relative is None else max(hard, relative)
