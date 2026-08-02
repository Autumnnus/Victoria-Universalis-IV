#!/usr/bin/env python3
"""Named Gemini API keys: a registry, a pool, and per-key usage.

Why a pool: the free tier limits requests per minute *per project*. One key means
a 48-second pause every 15 requests. Several keys mean the run moves to the next
key and keeps working, and the tired key comes back on its own when its window
has passed.

The registry lives OUTSIDE the repository so a key can never be committed:

    %APPDATA%\\victoria-universalis-loc\\keys.json      (Windows)
    ~/.config/victoria-universalis-loc/keys.json        (elsewhere)

Override with VU4_LOC_KEYS_FILE. Keys are added through `loc keys add <name>`,
which reads the key from a hidden prompt - never from a command-line argument,
which would land in the shell history.

Keys in the environment still work and need no registration:

    GEMINI_API_KEYS       several keys, separated by comma, semicolon or newline
    GEMINI_API_KEY        one key
    GEMINI_API_KEY_1..9   numbered keys
    GEMINI_API_KEY_FILE   path to a file outside the repo, one key per line

An environment key gets a registry entry for its cooldowns and usage, identified
by a short fingerprint - the key itself is never written to disk.

Per key the registry keeps: name, paused flag, cumulative calls and tokens, how
often it hit a limit, when it was last used, and a cooldown deadline per model.

Usage:
    loc keys                      list every key with its usage and state
    loc keys add ana              add a key (hidden prompt)
    loc keys remove ana
    loc keys pause ana            keep it registered but out of the rotation
    loc keys resume ana
    loc keys rename ana yedek
    loc keys clear-cooldowns [name]
    loc keys reset-usage [name]
    loc keys where                show the registry path
"""
from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

MAX_SLEEP = 300.0  # never block a run longer than this waiting for a key
DEFAULT_DAY_COOLDOWN = 6 * 3600.0
FLUSH_EVERY = 10  # write usage back to disk after this many calls


class NoKeys(RuntimeError):
    pass


class AllCooling(RuntimeError):
    """Every key is out of quota for longer than the caller is willing to wait."""


def registry_path() -> Path:
    override = os.environ.get("VU4_LOC_KEYS_FILE", "").strip()
    if override:
        return Path(override)
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "victoria-universalis-loc" / "keys.json"


def fingerprint(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:10]


def mask(key: str) -> str:
    return f"{key[:4]}...{key[-4:]}" if len(key) > 10 else "?" * len(key)


def _split(raw: str) -> list[str]:
    for separator in (",", ";", "\n", " "):
        raw = raw.replace(separator, "\n")
    return [part.strip() for part in raw.split("\n") if part.strip()]


def keys_from_environment() -> list[str]:
    found: list[str] = []
    found += _split(os.environ.get("GEMINI_API_KEYS", ""))
    single = os.environ.get("GEMINI_API_KEY", "").strip()
    if single:
        found.append(single)
    for index in range(1, 10):
        numbered = os.environ.get(f"GEMINI_API_KEY_{index}", "").strip()
        if numbered:
            found.append(numbered)
    path = os.environ.get("GEMINI_API_KEY_FILE", "").strip()
    if path and Path(path).is_file():
        found += _split(Path(path).read_text(encoding="utf-8"))

    unique: list[str] = []
    for key in found:
        if key not in unique:
            unique.append(key)
    return unique


# -- registry -----------------------------------------------------------------


@dataclass
class Entry:
    name: str
    fingerprint: str
    key: str | None = None  # None for an environment key: never stored
    source: str = "store"  # "store" | "env"
    paused: bool = False
    added: str = ""
    calls: int = 0
    prompt_tokens: int = 0
    output_tokens: int = 0
    limits: int = 0
    last_used: float = 0.0
    cooldowns: dict[str, float] = field(default_factory=dict)  # model -> epoch
    scopes: dict[str, str] = field(default_factory=dict)  # model -> "minute" | "day"

    def to_json(self) -> dict:
        data = {
            "name": self.name,
            "fingerprint": self.fingerprint,
            "source": self.source,
            "paused": self.paused,
            "added": self.added,
            "usage": {
                "calls": self.calls,
                "prompt_tokens": self.prompt_tokens,
                "output_tokens": self.output_tokens,
                "limits": self.limits,
                "last_used": self.last_used,
            },
            "cooldowns": self.cooldowns,
            "scopes": self.scopes,
        }
        if self.source == "store" and self.key:
            data["key"] = self.key
        return data

    @classmethod
    def from_json(cls, data: dict) -> "Entry":
        usage = data.get("usage", {})
        return cls(
            name=data.get("name", "?"),
            fingerprint=data.get("fingerprint", ""),
            key=data.get("key"),
            source=data.get("source", "store"),
            paused=bool(data.get("paused")),
            added=data.get("added", ""),
            calls=int(usage.get("calls", 0)),
            prompt_tokens=int(usage.get("prompt_tokens", 0)),
            output_tokens=int(usage.get("output_tokens", 0)),
            limits=int(usage.get("limits", 0)),
            last_used=float(usage.get("last_used", 0.0)),
            cooldowns={m: float(d) for m, d in (data.get("cooldowns") or {}).items()},
            scopes=dict(data.get("scopes") or {}),
        )


class Registry:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or registry_path()
        self.entries: list[Entry] = []
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        self.entries = [Entry.from_json(item) for item in data.get("keys", [])]

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "note": "Victoria Universalis IV localization keys. Environment keys are "
            "tracked by fingerprint only; their value is never stored.",
            "keys": [entry.to_json() for entry in self.entries],
        }
        self.path.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")

    # -- lookup ---------------------------------------------------------------

    def by_name(self, name: str) -> Entry | None:
        lowered = name.lower()
        for entry in self.entries:
            if entry.name.lower() == lowered:
                return entry
        return None

    def by_fingerprint(self, value: str) -> Entry | None:
        for entry in self.entries:
            if entry.fingerprint == value:
                return entry
        return None

    def next_env_name(self) -> str:
        used = {entry.name for entry in self.entries}
        index = 1
        while f"env-{index}" in used:
            index += 1
        return f"env-{index}"

    # -- mutation -------------------------------------------------------------

    def add(self, name: str, key: str) -> Entry:
        if self.by_name(name):
            raise ValueError(f"a key named {name!r} already exists")
        existing = self.by_fingerprint(fingerprint(key))
        if existing:
            raise ValueError(f"that key is already registered as {existing.name!r}")
        entry = Entry(
            name=name,
            fingerprint=fingerprint(key),
            key=key,
            source="store",
            added=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        )
        self.entries.append(entry)
        self.save()
        return entry

    def register_env(self, key: str) -> Entry:
        """Track an environment key without ever writing its value down."""
        entry = self.by_fingerprint(fingerprint(key))
        if entry:
            entry.source = "env" if entry.key is None else entry.source
            return entry
        entry = Entry(
            name=self.next_env_name(),
            fingerprint=fingerprint(key),
            key=None,
            source="env",
            added=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        )
        self.entries.append(entry)
        return entry

    def remove(self, name: str) -> Entry:
        entry = self.by_name(name)
        if not entry:
            raise ValueError(f"no key named {name!r}")
        self.entries.remove(entry)
        self.save()
        return entry


# -- pool ---------------------------------------------------------------------


@dataclass
class Slot:
    key: str
    entry: Entry

    @property
    def label(self) -> str:
        return f"{self.entry.name} ({mask(self.key)})"

    def ready_at(self, model: str) -> float:
        return self.entry.cooldowns.get(model, 0.0)

    def cooling(self, model: str, now: float | None = None) -> bool:
        return self.ready_at(model) > (now if now is not None else time.time())


class Pool:
    def __init__(
        self,
        keys: list[str] | None = None,
        min_interval: float = 0.0,
        day_cooldown: float = DEFAULT_DAY_COOLDOWN,
        registry: Registry | None = None,
    ) -> None:
        self.registry = registry or Registry()
        self.slots: list[Slot] = []
        self._paced: dict[str, float] = {}  # fingerprint -> monotonic of last call

        if keys is not None:
            # Explicit list (tests, or a single --api-key client).
            for key in keys:
                self.slots.append(Slot(key=key, entry=self.registry.register_env(key)))
        else:
            for entry in self.registry.entries:
                if entry.source == "store" and entry.key and not entry.paused:
                    self.slots.append(Slot(key=entry.key, entry=entry))
            for key in keys_from_environment():
                entry = self.registry.register_env(key)
                if entry.paused or any(slot.entry is entry for slot in self.slots):
                    continue
                self.slots.append(Slot(key=key, entry=entry))

        if not self.slots:
            paused = [entry.name for entry in self.registry.entries if entry.paused]
            hint = f" ({len(paused)} paused: {', '.join(paused)})" if paused else ""
            raise NoKeys(
                f"No usable Gemini API key{hint}. Add one with `loc keys add <name>`, "
                "or set GEMINI_API_KEYS in the shell."
            )

        self.min_interval = min_interval
        self.day_cooldown = day_cooldown
        self.next_slot = 0
        self.calls = 0
        self.prompt_tokens = 0
        self.output_tokens = 0
        self.quota_waits = 0
        self.quota_seconds = 0.0
        self.switches = 0
        self._since_flush = 0
        self.registry.save()

    # -- scheduling -----------------------------------------------------------

    def _available(self, model: str, now: float) -> list[Slot]:
        return [slot for slot in self.slots if not slot.cooling(model, now)]

    def acquire(self, model: str, max_sleep: float = MAX_SLEEP) -> Slot:
        """The next key usable for this model, waiting only when none is ready."""
        while True:
            now = time.time()
            ready = self._available(model, now)
            if ready:
                index_of = {id(slot): position for position, slot in enumerate(self.slots)}
                ordered = sorted(
                    ready,
                    key=lambda slot: (
                        (index_of[id(slot)] - self.next_slot) % len(self.slots),
                        self._paced.get(slot.entry.fingerprint, 0.0),
                    ),
                )
                slot = ordered[0]
                position = index_of[id(slot)]
                if len(self.slots) > 1 and position != self.next_slot % len(self.slots):
                    self.switches += 1
                self.next_slot = (position + 1) % len(self.slots)
                self._pace(slot)
                return slot

            soonest = min(slot.ready_at(model) for slot in self.slots)
            wait = max(0.0, soonest - now)
            if wait > max_sleep:
                parked = ", ".join(
                    f"{slot.entry.name}: {slot.entry.scopes.get(model, 'unknown')} quota, "
                    f"{(slot.ready_at(model) - now) / 60:.0f} min left"
                    for slot in self.slots
                )
                raise AllCooling(f"every key is out of quota for {model} ({parked})")
            print(f"    all {len(self.slots)} key(s) cooling for {model}: waiting {wait:.0f}s")
            self.quota_waits += 1
            self.quota_seconds += wait
            time.sleep(wait + 1.0)

    def _pace(self, slot: Slot) -> None:
        if self.min_interval <= 0:
            return
        last = self._paced.get(slot.entry.fingerprint, 0.0)
        wait = last + self.min_interval - time.monotonic()
        if wait > 0:
            time.sleep(wait)

    def used(self, slot: Slot, prompt_tokens: int = 0, output_tokens: int = 0) -> None:
        self._paced[slot.entry.fingerprint] = time.monotonic()
        slot.entry.calls += 1
        slot.entry.prompt_tokens += prompt_tokens
        slot.entry.output_tokens += output_tokens
        slot.entry.last_used = time.time()
        self.calls += 1
        self.prompt_tokens += prompt_tokens
        self.output_tokens += output_tokens
        self._since_flush += 1
        if self._since_flush >= FLUSH_EVERY:
            self.flush()

    def penalize(self, slot: Slot, model: str, seconds: float, scope: str) -> None:
        """Put one key to sleep for one model after a 429."""
        if scope == "day":
            seconds = max(seconds, self.day_cooldown)
        slot.entry.cooldowns[model] = time.time() + seconds
        slot.entry.scopes[model] = scope
        slot.entry.limits += 1
        self._paced[slot.entry.fingerprint] = time.monotonic()
        remaining = len(self._available(model, time.time()))
        print(
            f"    {slot.label}: {scope} quota hit on {model}, resting {seconds / 60:.1f} min"
            f" ({remaining} of {len(self.slots)} key(s) still available)"
        )
        self.flush()

    def adapt(self, requests_per_minute: int) -> None:
        """Pace each key to the limit the API just reported."""
        if not 0 < requests_per_minute <= 1000:
            return
        pace = 60.0 / requests_per_minute + 0.5
        if pace > self.min_interval:
            self.min_interval = pace
            print(f"    pacing each key to {pace:.1f}s between calls ({requests_per_minute}/minute)")

    def flush(self) -> None:
        self._since_flush = 0
        self.registry.save()

    # -- reporting ------------------------------------------------------------

    def report(self) -> str:
        self.flush()
        lines = [f"{len(self.slots)} key(s) in rotation"]
        for slot in self.slots:
            lines.append("  " + describe(slot.entry, slot.key))
        if self.switches:
            lines.append(f"  switched key {self.switches} time(s)")
        if self.quota_waits:
            lines.append(
                f"  whole pool waited {self.quota_waits} time(s), "
                f"{self.quota_seconds / 60:.1f} minute(s) total"
            )
        return "\n".join(lines)


def describe(entry: Entry, key: str | None = None, labels: bool = True) -> str:
    """One line per key. `labels=False` when a table header names the columns."""
    now = time.time()
    cooling = {
        model: (deadline - now) / 60 for model, deadline in entry.cooldowns.items() if deadline > now
    }
    if entry.paused:
        state = "paused"
    elif cooling:
        state = "cooling " + ", ".join(
            f"{model.split('-')[-1]} {minutes:.0f}min/{entry.scopes.get(model, '?')}"
            for model, minutes in cooling.items()
        )
    else:
        state = "ready"
    shown = mask(key) if key else (mask(entry.key) if entry.key else f"env:{entry.fingerprint[:6]}")
    last = (
        datetime.fromtimestamp(entry.last_used).strftime("%Y-%m-%d %H:%M")
        if entry.last_used
        else "never"
    )
    tokens = f"{(entry.prompt_tokens + entry.output_tokens) / 1000:.1f}k"
    if labels:
        return (
            f"{entry.name:<14} {shown:<14} {entry.source:<6} "
            f"calls={entry.calls:<6} tokens={tokens:<9} limits={entry.limits:<4} "
            f"last={last:<17} {state}"
        )
    return (
        f"{entry.name:<14} {shown:<14} {entry.source:<6} "
        f"{entry.calls:<13}{tokens:<16}{entry.limits:<10}{last:<18}{state}"
    )


_POOL: Pool | None = None


def pool(min_interval: float | None = None, day_cooldown: float | None = None) -> Pool:
    """The process-wide pool, so every client and model share one set of keys."""
    global _POOL
    if _POOL is None:
        _POOL = Pool(
            min_interval=min_interval or 0.0,
            day_cooldown=day_cooldown if day_cooldown is not None else DEFAULT_DAY_COOLDOWN,
        )
    else:
        if min_interval is not None and min_interval > _POOL.min_interval:
            _POOL.min_interval = min_interval
        if day_cooldown is not None:
            _POOL.day_cooldown = day_cooldown
    return _POOL


def reset() -> None:
    """Forget the cached pool - used by tests."""
    global _POOL
    _POOL = None


# -- command line -------------------------------------------------------------


def _read_key(from_stdin: bool) -> str:
    if from_stdin:
        return sys.stdin.read().strip()
    first = getpass.getpass("Paste the API key (input hidden): ").strip()
    if not first:
        raise SystemExit("Nothing entered.")
    return first


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Manage the named Gemini API keys used by the localization pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "loc keys                      list keys, usage and state\n"
            "loc keys add ana              add a key (hidden prompt)\n"
            "loc keys remove ana           forget a key\n"
            "loc keys pause ana            keep it registered, out of rotation\n"
            "loc keys resume ana\n"
            "loc keys rename ana yedek\n"
            "loc keys clear-cooldowns [name]\n"
            "loc keys reset-usage [name]\n"
            "loc keys where                show the registry path"
        ),
    )
    parser.add_argument(
        "action",
        nargs="?",
        default="list",
        choices=["list", "add", "remove", "pause", "resume", "rename", "clear-cooldowns", "reset-usage", "where"],
    )
    parser.add_argument("name", nargs="?")
    parser.add_argument("new_name", nargs="?")
    parser.add_argument("--stdin", action="store_true", help="Read the key from stdin instead of a prompt.")
    args = parser.parse_args()

    registry = Registry()

    if args.action == "where":
        print(registry.path)
        print(f"exists: {registry.path.exists()}, {len(registry.entries)} entry(ies)")
        return 0

    if args.action == "add":
        if not args.name:
            raise SystemExit("Give the key a name: `loc keys add ana`")
        key = _read_key(args.stdin)
        if len(key) < 20 or " " in key:
            raise SystemExit("That does not look like an API key.")
        try:
            entry = registry.add(args.name, key)
        except ValueError as error:
            raise SystemExit(str(error)) from error
        print(f"Added {entry.name} ({mask(key)}) to {registry.path}")
        return 0

    if args.action == "remove":
        if not args.name:
            raise SystemExit("Which key? `loc keys remove ana`")
        try:
            entry = registry.remove(args.name)
        except ValueError as error:
            raise SystemExit(str(error)) from error
        print(f"Removed {entry.name}.")
        return 0

    if args.action in ("pause", "resume"):
        if not args.name:
            raise SystemExit(f"Which key? `loc keys {args.action} ana`")
        entry = registry.by_name(args.name)
        if not entry:
            raise SystemExit(f"no key named {args.name!r}")
        entry.paused = args.action == "pause"
        registry.save()
        print(f"{entry.name} is now {'paused' if entry.paused else 'in rotation'}.")
        return 0

    if args.action == "rename":
        if not (args.name and args.new_name):
            raise SystemExit("`loc keys rename ana yedek`")
        entry = registry.by_name(args.name)
        if not entry:
            raise SystemExit(f"no key named {args.name!r}")
        if registry.by_name(args.new_name):
            raise SystemExit(f"a key named {args.new_name!r} already exists")
        entry.name = args.new_name
        registry.save()
        print(f"Renamed to {entry.name}.")
        return 0

    if args.action == "clear-cooldowns":
        targets = [registry.by_name(args.name)] if args.name else registry.entries
        if args.name and not targets[0]:
            raise SystemExit(f"no key named {args.name!r}")
        for entry in targets:
            entry.cooldowns.clear()
            entry.scopes.clear()
        registry.save()
        print(f"Cleared cooldowns for {len(targets)} key(s); they count as ready again.")
        return 0

    if args.action == "reset-usage":
        targets = [registry.by_name(args.name)] if args.name else registry.entries
        if args.name and not targets[0]:
            raise SystemExit(f"no key named {args.name!r}")
        for entry in targets:
            entry.calls = entry.prompt_tokens = entry.output_tokens = entry.limits = 0
            entry.last_used = 0.0
        registry.save()
        print(f"Reset usage counters for {len(targets)} key(s).")
        return 0

    # list
    environment = {fingerprint(key) for key in keys_from_environment()}
    if not registry.entries and not environment:
        print("No keys yet.")
        print("  loc keys add ana          register one (hidden prompt)")
        print('  $env:GEMINI_API_KEYS = "key1,key2"   or use the environment')
        return 1
    for key in keys_from_environment():
        registry.register_env(key)
    registry.save()

    print(
        f"  {'name':<14} {'key':<14} {'source':<6} {'calls':<13}{'tokens':<16}"
        f"{'limits':<10}{'last used':<18}state"
    )
    for entry in registry.entries:
        missing = entry.source == "env" and entry.fingerprint not in environment
        line = describe(entry, labels=False)
        if missing:
            line += "  (not in this shell's environment)"
        print("  " + line)
    rotation = sum(
        1
        for entry in registry.entries
        if not entry.paused and (entry.key or entry.fingerprint in environment)
    )
    print(f"\n{rotation} key(s) would be used by a run. Registry: {registry.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
