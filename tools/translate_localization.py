#!/usr/bin/env python3
"""Translate VE localization values while preserving Victoria 3 formatting tokens.

Uses Google Translate's public endpoint.  This is deliberately source-driven:
the English file supplies every key and target files retain their language header.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

LANGUAGES = {
    "braz_por": "pt",
    "french": "fr",
    "german": "de",
    "japanese": "ja",
    "korean": "ko",
    "polish": "pl",
    "russian": "ru",
    "simp_chinese": "zh-CN",
    "spanish": "es",
    "turkish": "tr",
}
LINE = re.compile(r'^(\s*)([^\s:#]+):(\d+)\s+"(.*)"\s*$')
TOKEN = re.compile(r"(\[[^\]]+\]|#[A-Za-z_]+|#!|\$[^$]+\$|£[^£]*£|@[^@!]+!)")
# These values are GUI texticon identifiers, not player-visible prose.
IDENTIFIER_VALUE_FILES = {"ve_religion_aspect_icons_l_english.yml"}


def protect(value: str, serial: int) -> tuple[str, list[tuple[str, str]]]:
    tokens: list[tuple[str, str]] = []
    def repl(match: re.Match[str]) -> str:
        placeholder = f"[[[VE_TOKEN_{serial}_{len(tokens)}]]]"
        tokens.append((placeholder, match.group(0)))
        return placeholder
    return TOKEN.sub(repl, value), tokens


def restore(value: str, tokens: list[tuple[str, str]]) -> str:
    # The endpoint occasionally duplicates a closing bracket on opaque markers.
    value = re.sub(r"\[\[\[VE_TOKEN_(\d+)_(\d+)\]\]+", r"[[[VE_TOKEN_\1_\2]]]", value)
    for placeholder, token in tokens:
        if placeholder not in value:
            raise ValueError(f"translation lost protected token {token!r} in {value!r}")
        value = value.replace(placeholder, token)
    return value


def translate_batch(values: list[str], target: str) -> list[str]:
    separator = "\ue000"
    query = urlencode({"client": "gtx", "sl": "en", "tl": target, "dt": "t", "q": separator.join(values)})
    request = Request("https://translate.googleapis.com/translate_a/single?" + query, headers={"User-Agent": "Victoria-Universalis-IV-localization"})
    for attempt in range(4):
        try:
            with urlopen(request, timeout=45) as response:
                payload = json.loads(response.read().decode("utf-8"))
            break
        except (HTTPError, URLError):
            if attempt == 3:
                raise
            time.sleep(1.5 * (attempt + 1))
    translated = "".join(segment[0] for segment in payload[0])
    result = translated.split(separator)
    if len(result) != len(values):
        # Some adjacent word pairs are normalized together by the service.  Split
        # only the affected batch; one-value batches never need a separator.
        if len(values) == 1:
            return [translated]
        midpoint = len(values) // 2
        return translate_batch(values[:midpoint], target) + translate_batch(values[midpoint:], target)
    return result


def batches(items: list[tuple[int, str, list[tuple[str, str]]]], max_chars: int = 4500):
    current = []
    chars = 0
    for item in items:
        size = len(item[1]) + 16
        if current and chars + size > max_chars:
            yield current
            current, chars = [], 0
        current.append(item)
        chars += size
    if current:
        yield current


def translate_file(source: Path, target: Path, target_code: str, dry_run: bool) -> int:
    lines = source.read_text(encoding="utf-8-sig").splitlines(keepends=True)
    # Translate only prose segments. Script scopes, markup, icons, and variables
    # are never sent to the translation service and are reassembled verbatim.
    parsed: dict[int, tuple[re.Match[str], list[str]]] = {}
    work: list[tuple[int, str, list[tuple[str, str]]]] = []
    if source.name not in IDENTIFIER_VALUE_FILES:
        for index, line in enumerate(lines):
            match = LINE.match(line.rstrip("\r\n"))
            if not match:
                continue
            parts = TOKEN.split(match.group(4))
            parsed[index] = (match, parts)
            for part_index in range(0, len(parts), 2):
                if parts[part_index]:
                    raw = parts[part_index]
                    leading = raw[:len(raw) - len(raw.lstrip())]
                    trailing = raw[len(raw.rstrip()):]
                    core = raw.strip()
                    if core:
                        work.append((index, core, [(str(part_index), leading, trailing)]))
    translated = 0
    all_batches = list(batches(work))
    if dry_run:
        batch_results = [[item[1] for item in batch] for batch in all_batches]
    else:
        with ThreadPoolExecutor(max_workers=6) as executor:
            batch_results = list(executor.map(lambda batch: translate_batch([item[1] for item in batch], target_code), all_batches))
    for batch, results in zip(all_batches, batch_results):
        if len(results) != len(batch):
            raise RuntimeError(f"expected {len(batch)} translations, got {len(results)}")
        for (line_index, _, metadata), result in zip(batch, results):
            part_index, leading, trailing = metadata[0]
            parsed[line_index][1][int(part_index)] = leading + result + trailing
    for line_index, (match, parts) in parsed.items():
        restored = "".join(parts).replace('"', '\\"')
        ending = "\r\n" if lines[line_index].endswith("\r\n") else "\n"
        lines[line_index] = f'{match.group(1)}{match.group(2)}:{match.group(3)} "{restored}"{ending}'
        translated += 1
    lines[0] = f"l_{target.stem.split('_l_')[-1]}:\n"
    if not dry_run:
        target.write_text("\ufeff" + "".join(lines), encoding="utf-8")
    return translated


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--language", choices=LANGUAGES, action="append", help="Target localization directory; repeat to select several.")
    parser.add_argument("--file", action="append", help="English localization filename to translate; repeat to select several.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1] / "localization"
    selected = args.language or list(LANGUAGES)
    total = 0
    for language in selected:
        sources = sorted((root / "english").glob("*.yml"))
        if args.file:
            wanted = set(args.file)
            sources = [source for source in sources if source.name in wanted]
            unknown = wanted - {source.name for source in sources}
            if unknown:
                raise SystemExit(f"Unknown English localization file(s): {', '.join(sorted(unknown))}")
        for source in sources:
            target_name = source.name.replace("_l_english", f"_l_{language}")
            count = translate_file(source, root / language / target_name, LANGUAGES[language], args.dry_run)
            total += count
            print(f"{language}: {target_name}: {count} values", flush=True)
    print(f"Completed {total} values.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
