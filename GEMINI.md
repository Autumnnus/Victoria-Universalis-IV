# Victoria Universalis IV - Gemini & Antigravity Guide

## Project purpose

Victoria Universalis IV is a Victoria 3 mod which adapts selected Europa Universalis IV-style mechanics to Victoria 3: national ideas, idea groups, religions and religious aspects, cultures, ages, and their supporting UI/events. Implement features in Victoria 3's native scripting and UI patterns; do not assume EU4 syntax or systems are directly compatible.

## Non-negotiable: Victoria 3 installation is read-only

The vanilla game directory is:

```text
C:\Program Files (x86)\Steam\steamapps\common\Victoria 3\game
```

It is a **reference-only** source of truth. It may be searched, listed, and read to learn current game syntax, definitions, GUI templates, icons, localization keys, scripted GUI bindings, and comparable vanilla implementations.

Never modify, create, rename, move, delete, format, copy files into, or otherwise write to that directory or any of its descendants. Do not run tools that might write there (including editor formatters, generators, game launch commands with an output path there, or broad recursive operations). All implementation changes belong in this mod workspace only.

Before introducing a mechanic or overriding a vanilla GUI, inspect the relevant vanilla implementation in that directory and mirror its current Victoria 3 conventions. Treat a vanilla file as a dependency to reference, never an editable template.

## Workspace and safety

- The mod root is this repository/workspace. Make all edits here only.
- Preserve unrelated user changes. Start relevant work with `git status --short` and inspect the target files before editing.
- Prefer narrowly scoped, additive files over broad vanilla overrides. When an override is necessary, override only named blocks/nodes and document the vanilla file and blocks being extended in a nearby comment.
- Use the existing `ve_` prefix for new custom identifiers, filenames, variables, modifiers, scripted GUI names, GUI types, localization keys, and feature-specific assets. Keep event namespaces unique and stable.
- Do not use destructive git commands (`reset --hard`, `checkout --`, broad cleanup) or overwrite user work without explicit confirmation.
- Keep game content deterministic and performant: put recurring logic in appropriate `on_actions`, avoid expensive unbounded scopes in frequently fired pulses, and use scripted triggers/values/effects for reusable logic.

## Current mod layout

```text
common/
  alert_groups/, alert_types/             # custom alerts
  customizable_localization/              # context-dependent localization
  history/global/, history/states/        # initial global/state setup
  on_actions/                             # pulse and hook event dispatch
  scripted_effects/                       # reusable mutations and feature logic
  scripted_guis/                          # UI data/actions exposed to GUI
  scripted_triggers/                      # reusable conditions/tooltips
  script_values/                          # reusable calculations
  static_modifiers/                       # national idea, religion, age, culture modifiers
events/                                   # event namespaces and definitions
gfx/                                      # mod-owned textures and other assets
gui/                                      # custom panels and narrowly overridden vanilla nodes
localization/<language>/                  # per-language .yml files
topbar.gui                                # root-level GUI override used by the mod
```

The vanilla game also contains many applicable `common/` categories, including `religions`, `decisions`, `journal_entries`, `institutions`, `laws`, `modifier_type_definitions`, `scripted_buttons`, `scripted_modifiers`, `defines`, and `game_concepts`. Add to one only after confirming the native format and load behavior in vanilla.

## Where to implement things

| Need | Primary location(s) |
| --- | --- |
| A recurring or externally triggered outcome | `events/`, dispatched from `common/on_actions/` or a scripted effect |
| Reusable condition | `common/scripted_triggers/` |
| Reusable mutation/workflow | `common/scripted_effects/` |
| Reusable number/calculation | `common/script_values/` |
| Player-facing mechanical bonus | `common/static_modifiers/` (or another vanilla-supported modifier mechanism) |
| Data/actions displayed in a custom panel | `common/scripted_guis/` plus `gui/` |
| Custom alert | `common/alert_types/` and, where needed, `common/alert_groups/` |
| New texture/icon | `gfx/` with a mod-local path, then reference it from GUI/script |
| Text visible to players | `localization/<language>/` |
| Initial save/start setup | the appropriate `common/history/` location |

## Events and scripting conventions

- Put event definitions in a feature-named file under `events/`; begin with `namespace = ve_<feature>` and use IDs such as `ve_ideas.1`. Never reuse a vanilla namespace or event ID.
- Specify the proper event type (`country_event`, `state_event`, etc.) and explicit title, description, options, image/icon, trigger, cooldown, and duration when appropriate. Copy these details from comparable vanilla events.
- Fire events from a deliberate hook: custom entries under `common/on_actions/`, a decision/button, or a scripted effect. Do not depend on an event file's presence to execute it.
- Keep event text keys alongside the feature's localization. Event IDs, modifier IDs, variable names, flags, scopes, and localization keys must agree exactly.
- Use `scope = country`/the appropriate scope in reusable blocks. Make scope transitions explicit (`capital =`, `owner =`, `root =`, etc.) rather than relying on a caller's incidental scope.
- Reuse the established patterns in `common/scripted_effects/ve_*.txt`, `common/scripted_triggers/ve_*.txt`, and `common/script_values/ve_*.txt`; consolidate repeated logic there instead of duplicating it in every GUI click or event option.

## GUI and assets

- Inspect the matching vanilla `.gui` file before changing UI. In mod GUI files, preserve the native node hierarchy and use `blockoverride` only for the smallest necessary named node.
- The mod's principal panel patterns are in `gui/ve_gui_panel.gui`, `gui/ve_panel_ideas.gui`, `gui/ve_panel_religion.gui`, and the `common/scripted_guis/ve_*.txt` files. Extend these patterns for related systems.
- GUI data/commands belong in scripted GUIs or supported game bindings; GUI should not duplicate large amounts of game logic.
- Use unique GUI type/node names with the `ve_` prefix, localize all visible labels/tooltips, and make visibility conditions safe when variables/scopes are absent.
- Put new assets under mod-owned `gfx/` paths. Verify the path, filename, format, and reference syntax against a working vanilla or existing mod asset before wiring it in.
- Do not replace whole vanilla GUI files merely to alter a small element. Check UI interactions in game after changes, especially topbar and fullscreen panel overrides.

## Localization

- Every player-visible key must have an English entry in `localization/english/`; add translations only when requested or when maintaining an existing translated key set.
- Follow Victoria 3's exact format: language header (for example `l_english:`), quoted strings, and the localization filename convention `*_l_<language>.yml`.
- Preserve the encoding and line-ending conventions already used by the target localization folder/file. Do not mechanically reformat or re-encode unrelated localization.
- Use stable, feature-prefixed keys such as `ve_religion_*`, `ve_idea_*`, and `ve_age_*`; avoid generic names that could collide with vanilla or another mod.
- Add names, descriptions, tooltips, event title/description/options, and concept text together with the mechanics that use them. Validate that all referenced keys exist.
- Keep formatting markup (`#P`, `#Y`, `#tooltippable_concept`, icons, `\n`, etc.) consistent with nearby working entries and vanilla examples.

## Testing and logs

- Do not repeatedly ask the user to launch the game or manually test routine changes. When syntax, identifiers, braces, localization references, modifier definitions, and comparable vanilla patterns can be checked statically, perform those checks yourself and treat them as sufficient for normal implementation work.
- Request or recommend user-run game testing only for important, critical, or genuinely runtime-dependent behavior that static inspection cannot establish. Examples include risky GUI overrides, save compatibility or migration, event/on-action dispatch, scope-dependent behavior, timing and pulse logic, multiplayer behavior, crashes, or a suspected engine-specific issue.
- Do not end every task with a generic “test this in game” requirement. If no critical runtime uncertainty remains, report the static verification performed and finish the task.
- When the user mentions errors, debugging, crashes, warnings, or logs—or when diagnosis requires game output—inspect the Victoria 3 logs at:

```text
C:\Users\prost\OneDrive\Documents\Paradox Interactive\Victoria 3\logs
```

- Treat the logs directory as a diagnostic, read-only source. Inspect relevant files such as `error.log`, `debug.log`, `game.log`, and `system.log` when present; do not modify, delete, truncate, or clear them.

## Verification checklist

After an implementation:

1. Review every edited file and confirm nothing outside the workspace was touched.
2. Search for all new identifiers and localization keys to catch spelling or scope mismatches.
3. Check script braces and GUI block nesting; compare changed syntax with a known working vanilla or mod example.
4. Require Victoria 3 runtime validation only when the change is critical or cannot be verified reliably through static checks. When logs are relevant, inspect the configured Victoria 3 logs directory directly.
5. Report files changed, validation performed, and any game-runtime checks that remain for the user.

## Working style for future requests

Translate requested EU4 concepts into a Victoria 3-compatible design before coding. State any necessary adaptation (for example, a mechanic that needs country variables, modifiers, scripted GUI, and pulse events rather than a native EU4 subsystem). Use the installed game's source files whenever syntax, available triggers/effects, GUI hierarchy, assets, or localization conventions are uncertain—always read-only.

## Mechanics reference

- Before answering, designing, debugging, or implementing anything related to religion, culture/National Identity, Cultural or Religious Projects, idea groups, National Ideas, ages/Era Momentum, or the culture/religion actions in the state panel, read `MECHANICS_REFERENCE.md`.
- Treat that document as the durable system map and vocabulary reference. The implementation files linked from it remain the final source of truth when exact syntax or a recently changed value matters.
- When one of those mechanics changes, update `MECHANICS_REFERENCE.md` in the same task so the documented rules, variables, thresholds, state actions, and source map do not drift from the code.
