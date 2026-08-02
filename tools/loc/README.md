# loc — a localization pipeline for Paradox mods

`loc` translates a Paradox mod's localization with an LLM and refuses to ship the
result unless it is technically sound. It was built for **Victoria Universalis
IV**, whose eleven languages had been machine-translated key by key with no
context: "Religious Settlement" became *religious colonisation* in every
language, "Steam and the State" kept the word *Steam*, and "Doctrine Ledger"
turned into *Doutrina Ledger*.

The fix is not a better model. It is what you put in front of one:

- a **termbase** the model may not contradict, with the mistranslation to avoid
  recorded next to every term;
- the **game's own vocabulary**, extracted from the installed game, so the mod
  says *Bürokrasi* / *行政力* exactly like the interface around it;
- **whole entries with context** — an event's title, description and options
  travel in one request, never split;
- a **validation gate** on every returned string: identical markup payload, no
  stray whitespace, no bare quotes, locked terms present, length budget honoured.

No third-party packages. Python 3.10 or newer, standard library only.

---

## Quick start

```
1  ./loc doctor              says what is missing and what to do next
2  ./loc keys add main       adds a Gemini API key (hidden prompt)
3  ./loc status              what is translated, per file and language
4  ./loc sync turkish        glossary → translate → review → verify
5  ./loc verify              the quality gate, before you package
```

On Windows use `loc.cmd` (`loc doctor`, `loc sync turkish`, …); elsewhere `./loc`.
Both are thin wrappers around `python -m tools.loc`.

Run `loc` with no arguments for a menu — nothing has to be memorised.

### What you need

| | |
|---|---|
| Python | 3.10+, no packages to install |
| API key | one Gemini key is enough; several make it faster (see *Keys*) |
| The game | optional but recommended: its localization is read (never written) to extract vocabulary. Set `VICTORIA3_GAME_DIR` if it is not found automatically |

---

## How it works

English is the only source of truth. Target files are rebuilt from the English
layout, so a key the pipeline has not produced is simply absent and the game
falls back to English — always better than a stale machine translation.

```
localization/english/*.yml
   │
   ├─ 1  vanilla     read the game's own vocabulary        → glossary/vanilla/<lang>.json
   ├─ 2  terms       propose a translation per mod term    → glossary/<lang>.tsv
   │     ↳ you review and lock what you accept
   ├─ 3  translate   only keys that are new or stale
   ├─ 4  review      a native reviewer over the interface text
   └─ 5  verify      markup, whitespace, locked terms, duplicates
```

### The glossary is the point

`localization/glossary/terms.tsv` holds the mod's canonical terms — 88 for
Victoria Universalis IV — each with a definition and an `avoid` note:

```
religious_settlement  Religious Settlement  meter  0-100 equilibrium meter …
    avoid: settlement means accord, arrangement, modus vivendi. It is NOT a place
    of habitation, a colony, a village, or "solving a problem".
```

Per language, `localization/glossary/<language>.tsv` records the decision and its
status:

| status | meaning |
|---|---|
| `locked` | a human accepted it; no run may contradict it, and it is checked on every value |
| `candidate` | a model proposed it and it is in use, still open to review |
| `todo` | nothing decided yet |

Changing a decision invalidates **only the keys whose English text mentions that
term**. Locking `Ledger → Doktrin Defteri` retranslates the handful of strings
that say "Ledger", not the file.

### Versioning is per key, not per file

`localization/.translation_state.json` records the hash of the English value each
translation was made from. A key comes back into scope when:

| signal | when |
|---|---|
| `english changed` | the English value was edited |
| `glossary term changed` | a term its text mentions got a new decision |
| `prompt generation changed` | only with `--refresh-prompts`; a reworded instruction does not make shipped text wrong |

So `loc sync` twice in a row costs one status check and zero API calls, and a
typo fix in one tooltip brings back exactly that tooltip in every language.

### Content tiers

Not every string deserves the same effort. `config.FILE_PROFILES` assigns each
file a tier:

| tier | what | treatment |
|---|---|---|
| A | panel labels, buttons, event titles and options, tooltips | quality model + review pass |
| B | long event and Journal Entry prose | quality model |
| C | formulaic modifier names | cheaper model; the glossary does the work |
| X | identifier carriers, not prose | copied verbatim, no model |

### Keys

Keys are named, stored **outside the repository**
(`%APPDATA%\victoria-universalis-loc\keys.json`, or `~/.config/…`), and never
passed as command-line arguments.

```
loc keys                     list keys with usage and state
loc keys add main            add one (hidden prompt)
loc keys pause spare         keep it registered, out of rotation
loc keys remove spare
loc keys rename main primary
loc keys clear-cooldowns
loc keys reset-usage
loc keys where
```

Environment keys work too and need no registration: `GEMINI_API_KEY`,
`GEMINI_API_KEYS` (comma-separated), `GEMINI_API_KEY_1..9`, `GEMINI_API_KEY_FILE`.
An environment key is tracked by a short fingerprint for its usage and cooldowns;
its value is never written to disk.

Why more than one key: the free tier limits requests per minute per project. One
key means a 48-second pause every 15 requests. Several keys mean the run moves to
the next key immediately and the tired one returns on its own. A per-day
allowance parks that key for `--day-cooldown` minutes (default 360) instead.

Per-key usage — calls, tokens, how often it hit a limit, when it was last used —
is kept across runs and shown by `loc keys`.

---

## Commands

| | |
|---|---|
| `loc` | interactive menu |
| `loc doctor` | check the setup, print the next step |
| `loc status` | translated vs pending, per file and language |
| `loc keys …` | manage the key pool |
| `loc vanilla` | re-extract the game's vocabulary |
| `loc terms <lang>` | propose glossary candidates |
| `loc translate <lang>` | translate pending keys |
| `loc review <lang>` | native review pass over tier A |
| `loc verify` | quality gate |
| `loc sync <lang>` \| `loc sync all` | all of the above, in order, skipping finished steps |

Useful flags, forwarded to the underlying step:

| | |
|---|---|
| `--dry-run` | print the plan and the exact request; no API call |
| `--limit 20` | translate at most 20 keys per file (trial runs) |
| `--min-interval 4.5` | seconds between calls, **per key** |
| `--force` | retranslate keys already recorded as current |
| `--refresh-prompts` | also retranslate keys made by an older prompt generation |
| `--model <name>` | override the model for one run |
| `--strict` | `verify` fails on warnings too |

Models live in one place, `config.MODELS`, and can be overridden per shell with
`GEMINI_MODEL_QUALITY` and `GEMINI_MODEL_BULK`.

### Cost

Victoria Universalis IV is 2,146 keys. One full sweep of all ten languages is
roughly 700 requests, ~1.6M input and ~0.5M output tokens — single-digit dollars
on the small models, and free-tier keys can do it over a few days.

---

## For translators

You do not need to run anything to improve a language. The highest-value fix is a
**term**:

1. open `localization/glossary/<language>.tsv`;
2. correct the `translation` column;
3. set its `status` to `locked` and put your reasoning in `note`;
4. send the file back (pull request, or just paste the changed lines).

A locked term is honoured by every future run and checked on every string that
mentions it, so one correction fixes the whole mod rather than one tooltip.

If you do want to run it: `loc sync <language>` retranslates only what your change
invalidated.

---

## Using it for another mod

The machinery is mod-agnostic; the mod-specific parts are small and isolated:

| what | where |
|---|---|
| the languages you ship | `config.LANGUAGES` |
| one entry per localization file: tier + a sentence on what the text is | `config.FILE_PROFILES` |
| tight frames that need a hard character budget | `config.MAX_CHARS_BY_KEY` |
| your mod's terms, definitions and mistranslations to avoid | `localization/glossary/terms.tsv` |
| strings that may legitimately equal English | `verify.ALLOWED_EQUAL_KEYS` |

`vanilla_terms.py` is Victoria 3-shaped: it looks for `concept_*`, `ig_*`,
`law_*`, `building_*`, `bg_*` keys and the modifier types your mod writes. Other
Clausewitz games use the same file format, so adapting it is a matter of changing
those patterns and the install path.

Everything else — the yml reader/writer, markup validation, batching, the key
pool, the state file, the prompts — carries over unchanged.

---

## Files

| | |
|---|---|
| `config.py` | paths, languages, models, per-file tiers, length budgets |
| `yml.py` | the only place that reads or writes localization files (UTF-8 BOM, CRLF, key order) |
| `tokens.py` | markup handling, line-break repair, validation |
| `batching.py` | how a file is cut into requests; events are never split |
| `prompts.py` | the instructions — the file to iterate on for quality |
| `gemini.py` | the API client: structured JSON output, retries, quota classification |
| `keys.py` | named keys, the pool, per-key usage and cooldowns |
| `glossary.py` | termbase, per-language decisions, relevant slice per request |
| `vanilla_terms.py` | extracts the game's own vocabulary (read-only) |
| `propose_terms.py` | proposes a term set for a language |
| `translate.py` | the main pass |
| `review.py` | the second pass: keep or replace, never a blind retranslation |
| `verify.py` | quality gate |
| `state.py` | per-key versioning and progress reporting |
| `doctor.py` | setup check |
| `__main__.py` | one entry point and the menu |

Licence: MIT, see `LICENSE` — the pipeline only, not the mod's content.
