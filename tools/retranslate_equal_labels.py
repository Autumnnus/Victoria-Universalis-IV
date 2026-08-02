#!/usr/bin/env python3
"""Retry visible target values that remained byte-identical to English source text."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import re

from translate_localization import IDENTIFIER_VALUE_FILES, LANGUAGES, LINE, TOKEN, batches, translate_batch


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("language", choices=LANGUAGES)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1] / "localization"
    changed = 0
    for source in sorted((root / "english").glob("*.yml")):
        if source.name in IDENTIFIER_VALUE_FILES:
            continue
        target = root / args.language / source.name.replace("_l_english", f"_l_{args.language}")
        source_lines = source.read_text(encoding="utf-8-sig").splitlines(keepends=True)
        target_lines = target.read_text(encoding="utf-8-sig").splitlines(keepends=True)
        source_values = {m.group(2): m.group(4) for line in source_lines if (m := LINE.match(line.rstrip("\r\n")))}
        work = []
        parts_by_line = {}
        for index, line in enumerate(target_lines):
            match = LINE.match(line.rstrip("\r\n"))
            if not match or source_values.get(match.group(2)) != match.group(4):
                continue
            if not re.search(r"[A-Za-z]{4}", match.group(4)):
                continue
            parts = TOKEN.split(match.group(4))
            parts_by_line[index] = (match, parts)
            for part_index in range(0, len(parts), 2):
                raw = parts[part_index]
                core = raw.strip()
                if core:
                    work.append((index, core, [(str(part_index), raw[:len(raw)-len(raw.lstrip())], raw[len(raw.rstrip()):])]))
        # A single UI label can be treated as a name when batched beside other
        # labels. Send each retry independently while retaining modest parallelism.
        all_batches = [[item] for item in work]
        with ThreadPoolExecutor(max_workers=6) as executor:
            results_by_batch = list(executor.map(lambda batch: translate_batch([item[1] for item in batch], LANGUAGES[args.language]), all_batches))
        for batch, results in zip(all_batches, results_by_batch):
            for (index, _, metadata), result in zip(batch, results):
                part, leading, trailing = metadata[0]
                parts_by_line[index][1][int(part)] = leading + result + trailing
        for index, (match, parts) in parts_by_line.items():
            value = "".join(parts).replace('"', '\\"')
            if value == match.group(4):
                continue
            ending = "\r\n" if target_lines[index].endswith("\r\n") else "\n"
            target_lines[index] = f'{match.group(1)}{match.group(2)}:{match.group(3)} "{value}"{ending}'
            changed += 1
        target.write_text("\ufeff" + "".join(target_lines), encoding="utf-8")
    print(f"Retried {changed} visible values for {args.language}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
