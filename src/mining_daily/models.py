"""Minimal JSON chat adapter; credentials and HTTP response bodies are never logged."""

import json
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import httpx


class ProviderError(RuntimeError):
    """Transport/configuration failures are not business abstentions."""


class ResponseError(ValueError):
    """A model response did not satisfy the JSON protocol."""


@dataclass(frozen=True)
class ModelConfig:
    name: str
    base_url: str
    api_key: str
    timeout: float = 60
    max_attempts: int = 3

    @classmethod
    def from_env(cls, role: str) -> "ModelConfig":
        values = [
            os.getenv(f"{role}_{key}", "").strip() for key in ("MODEL", "BASE_URL", "API_KEY")
        ]
        if not all(values):
            raise ProviderError(f"Set {role}_MODEL, {role}_BASE_URL and {role}_API_KEY")
        try:
            timeout = float(os.getenv("MODEL_TIMEOUT_SECONDS", "60"))
            attempts = int(os.getenv("MODEL_MAX_ATTEMPTS", "3"))
        except ValueError as exc:
            raise ProviderError("Invalid timeout/retry configuration") from exc
        if not 1 <= timeout <= 300 or not 1 <= attempts <= 5:
            raise ProviderError("Timeout must be 1–300 seconds; attempts must be 1–5")
        parsed = urlparse(values[1])
        if parsed.scheme != "https" and not (
            parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1", "::1"}
        ):
            raise ProviderError("Use HTTPS for remote model endpoints")
        if (
            parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or not parsed.hostname
        ):
            raise ProviderError("Model endpoint must not contain credentials, query or fragment")
        return cls(values[0], values[1], values[2], timeout=timeout, max_attempts=attempts)


class ChatModel:
    def __init__(self, config: ModelConfig, client: httpx.Client | None = None) -> None:
        self.config = config
        self.name = config.name
        self.usage = {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0}
        self._client = client

    def complete(self, system: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = {
            "model": self.config.name,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            "response_format": {"type": "json_object"},
        }
        for attempt in range(self.config.max_attempts):
            try:
                self.usage["calls"] += 1
                if self._client is None:
                    with httpx.Client(
                        timeout=self.config.timeout, follow_redirects=False
                    ) as client:
                        response = self._post(client, body)
                else:
                    response = self._post(self._client, body)
                if response.status_code in {408, 429, 500, 502, 503, 504}:
                    if attempt + 1 < self.config.max_attempts:
                        time.sleep(min(2**attempt, 4))
                        continue
                if response.is_error:
                    raise ProviderError(f"Model endpoint returned HTTP {response.status_code}")
                try:
                    data = response.json()
                    for key in ("prompt_tokens", "completion_tokens"):
                        self.usage[key] += int(data.get("usage", {}).get(key, 0))
                    content = data["choices"][0]["message"]["content"]
                    result = json.loads(content)
                    if not isinstance(result, dict):
                        raise ValueError("Expected JSON object")
                    return result
                except (ValueError, KeyError, IndexError, TypeError) as exc:
                    raise ResponseError("Model must return a valid JSON object") from exc
            except httpx.TransportError as exc:
                if attempt + 1 == self.config.max_attempts:
                    raise ProviderError("Model transport failed after bounded retries") from exc
                time.sleep(min(2**attempt, 4))
        raise ProviderError("Retry budget exhausted")

    def _post(self, client: httpx.Client, body: dict[str, Any]) -> httpx.Response:
        return client.post(
            self.config.base_url.rstrip("/") + "/chat/completions",
            headers={"Authorization": f"Bearer {self.config.api_key}"},
            json=body,
            timeout=self.config.timeout,
        )
