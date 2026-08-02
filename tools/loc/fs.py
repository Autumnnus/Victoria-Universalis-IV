#!/usr/bin/env python3
"""Writing files on a machine where something else is also touching them.

This mod lives in a OneDrive folder. OneDrive, editors, antivirus and the Paradox
launcher all open these files at unpredictable moments, and Windows answers a
write into an open file with `OSError: [Errno 22] Invalid argument` or
`[Errno 13] Permission denied`. Once, that killed a ten-language run at the very
last save.

So every write here is:

* atomic - written to a temporary file beside the target, then renamed over it,
  which is a single operation on Windows and NTFS. A crash or a lock can never
  leave a half-written state file;
* retried - a handful of times with a short backoff, because these locks are held
  for milliseconds;
* survivable - if it still fails, the caller is told rather than crashed, and the
  content is left in the temporary file so nothing is lost.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

RETRIES = 6
BACKOFF = 0.25


class WriteFailed(OSError):
    """The target could not be replaced; the payload is in `kept`."""

    def __init__(self, path: Path, kept: Path, reason: OSError) -> None:
        super().__init__(f"could not write {path.name}: {reason}")
        self.path = path
        self.kept = kept
        self.reason = reason


def write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp{os.getpid()}")
    last: OSError | None = None
    for attempt in range(RETRIES):
        try:
            temporary.write_bytes(payload)
            os.replace(temporary, path)
            return
        except OSError as error:
            last = error
            time.sleep(BACKOFF * (attempt + 1))
    # Keep the payload next to the target so a failed run loses nothing.
    try:
        temporary.write_bytes(payload)
    except OSError:
        temporary = path.with_name(path.name + ".new")
        try:
            temporary.write_bytes(payload)
        except OSError:
            raise WriteFailed(path, path, last) from last
    raise WriteFailed(path, temporary, last)


def write_text(path: Path, text: str, encoding: str = "utf-8", newline: str = "") -> None:
    if newline:
        text = text.replace("\n", newline)
    write_bytes(path, text.encode(encoding))
