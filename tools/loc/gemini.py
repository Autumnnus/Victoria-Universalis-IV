#!/usr/bin/env python3
"""Minimal Gemini client for the localization pipeline.

Standard library only, like the rest of tools/. Keys come from the environment
through tools/loc/keys.py and are sent as a header, never placed in a URL or
written to a file. The client itself holds no key: it borrows one from the pool
per request, so a rate-limited key is set aside and the next one takes over.

Every call asks for structured JSON output with an explicit response schema, so
the caller never parses prose: a translated batch comes back as a list of
{key, value} objects and a mismatch is the model's problem to retry, not ours.
"""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request

from tools.loc import keys

ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
RETRY_STATUS = {408, 429, 500, 502, 503, 504}
RETRY_DELAY = re.compile(r'"retryDelay"\s*:\s*"(\d+(?:\.\d+)?)s"')
QUOTA_ID = re.compile(r'"quotaId"\s*:\s*"([^"]+)"')
QUOTA_LIMIT = re.compile(r"limit:\s*(\d+)")

# A per-minute rate limit is something to wait out. A per-day allowance is not:
# no amount of waiting inside one run brings it back.
MAX_WAIT = 300.0
DEFAULT_QUOTA_WAIT = 60.0
QUOTA_WAITS = 12  # how many rate-limit pauses one call may sit through


def quota_scope(body: str) -> str:
    """"minute", "day" or "unknown", read from the API's own quotaId."""
    match = QUOTA_ID.search(body)
    if not match:
        return "unknown"
    quota_id = match.group(1)
    if "PerMinute" in quota_id:
        return "minute"
    if "PerDay" in quota_id:
        return "day"
    return "unknown"


class GeminiError(RuntimeError):
    pass


class Truncated(GeminiError):
    """The model stopped before completing its JSON; the caller should split."""


class QuotaExhausted(GeminiError):
    """The account's quota for this model is spent; retrying cannot help."""


class Client:
    def __init__(
        self,
        model: str,
        api_key: str | None = None,
        pool: keys.Pool | None = None,
        temperature: float = 0.25,
        min_interval: float = 0.0,
        timeout: int = 180,
        attempts: int = 4,
    ) -> None:
        self.model = model
        try:
            if pool is not None:
                self.pool = pool
            elif api_key:
                self.pool = keys.Pool([api_key], min_interval=min_interval)
            else:
                self.pool = keys.pool(min_interval=min_interval)
        except keys.NoKeys as error:
            raise GeminiError(str(error)) from error
        self.temperature = temperature
        self.timeout = timeout
        self.attempts = attempts

    # Counters live on the pool, so switching models keeps one set of totals.
    @property
    def calls(self) -> int:
        return self.pool.calls

    @property
    def prompt_tokens(self) -> int:
        return self.pool.prompt_tokens

    @property
    def output_tokens(self) -> int:
        return self.pool.output_tokens

    @property
    def quota_waits(self) -> int:
        return self.pool.quota_waits

    @property
    def quota_seconds(self) -> float:
        return self.pool.quota_seconds

    # -- plumbing -------------------------------------------------------------

    def _post(self, body: dict) -> dict:
        payload = json.dumps(body).encode("utf-8")
        transient = 0
        while True:
            try:
                slot = self.pool.acquire(self.model, max_sleep=MAX_WAIT)
            except keys.AllCooling as error:
                raise QuotaExhausted(str(error)) from error

            request = urllib.request.Request(
                ENDPOINT.format(model=self.model),
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": slot.key,
                    "User-Agent": "Victoria-Universalis-IV-localization",
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    answer = json.loads(response.read().decode("utf-8"))
                    usage = answer.get("usageMetadata", {})
                    self.pool.used(
                        slot,
                        usage.get("promptTokenCount", 0),
                        usage.get("candidatesTokenCount", 0),
                    )
                    return answer
            except urllib.error.HTTPError as error:
                self.pool.used(slot)
                body_text = error.read().decode("utf-8", "replace")
                detail = " ".join(body_text.split())[:900]

                retry_after = error.headers.get("Retry-After")
                suggested = RETRY_DELAY.search(body_text)
                delay = None
                if retry_after and retry_after.replace(".", "", 1).isdigit():
                    delay = float(retry_after)
                elif suggested:
                    delay = float(suggested.group(1))

                if error.code == 429:
                    # Rest this key for this model and move on. With more than one
                    # key that costs nothing; with one key the pool does the wait.
                    scope = quota_scope(body_text)
                    limit = QUOTA_LIMIT.search(body_text)
                    if limit:
                        self.pool.adapt(int(limit.group(1)))
                    self.pool.penalize(
                        slot, self.model, delay if delay is not None else DEFAULT_QUOTA_WAIT, scope
                    )
                    continue

                if error.code not in RETRY_STATUS:
                    raise GeminiError(f"HTTP {error.code}: {detail}") from error
                transient += 1
                if transient >= self.attempts:
                    raise GeminiError(f"HTTP {error.code} after {transient} attempts: {detail}") from error
                time.sleep(delay if delay is not None else 2.0 * transient**2)
            except (urllib.error.URLError, TimeoutError) as error:
                self.pool.used(slot)
                transient += 1
                if transient >= self.attempts:
                    raise GeminiError(f"{error} after {transient} attempts") from error
                time.sleep(2.0 * transient)

    # -- public API -----------------------------------------------------------

    def structured(self, system: str, prompt: str, schema: dict) -> dict:
        """One structured-output call. Returns the parsed JSON object."""
        response = self._post(
            {
                "systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": self.temperature,
                    "responseMimeType": "application/json",
                    "responseSchema": schema,
                },
            }
        )

        # Token totals are attributed to the key that answered, inside _post.

        candidates = response.get("candidates") or []
        if not candidates:
            feedback = response.get("promptFeedback", {})
            raise GeminiError(f"no candidate returned; promptFeedback={feedback}")
        candidate = candidates[0]
        reason = candidate.get("finishReason", "STOP")
        text = "".join(part.get("text", "") for part in candidate.get("content", {}).get("parts", []))
        if reason not in ("STOP", None):
            raise Truncated(f"finishReason={reason} after {len(text)} characters")
        try:
            return json.loads(text)
        except json.JSONDecodeError as error:
            raise Truncated(f"unparsable JSON ({error}); first 200 chars: {text[:200]!r}") from error


# The one schema the pipeline needs: a keyed list of translated values.
TRANSLATION_SCHEMA = {
    "type": "object",
    "properties": {
        "translations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                    "value": {"type": "string"},
                },
                "required": ["key", "value"],
            },
        }
    },
    "required": ["translations"],
}

# Review returns a verdict per key so unchanged entries cost nothing downstream.
REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "reviews": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                    "verdict": {"type": "string", "enum": ["keep", "replace"]},
                    "value": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["key", "verdict"],
            },
        }
    },
    "required": ["reviews"],
}
