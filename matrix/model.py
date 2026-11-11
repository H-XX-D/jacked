"""Loopback-only model transport using the FRIDAY chat protocol."""

import http.client
import ipaddress
import json
import os
from dataclasses import dataclass
from urllib.parse import urlsplit

from core.chat_protocol import chat_message, chat_request


def local_endpoint(url):
    endpoint = urlsplit(url)
    try:
        local = ipaddress.ip_address(endpoint.hostname or "").is_loopback
    except ValueError:
        local = endpoint.hostname == "localhost"
    if (
        endpoint.scheme != "http"
        or not local
        or endpoint.username is not None
        or endpoint.password is not None
        or endpoint.path not in {"", "/", "/v1", "/v1/"}
        or endpoint.query
        or endpoint.fragment
        or endpoint.port == 0
    ):
        raise ValueError("Use an HTTP server on loopback.")
    return endpoint


def request_json(url, method, route, payload=None, *, timeout=30, headers=None):
    endpoint = local_endpoint(url)
    if headers and any(not all(32 <= ord(char) < 127 for char in value) for value in headers.values()):
        raise ValueError("The local service credential contains invalid header characters.")
    host = "127.0.0.1" if endpoint.hostname == "localhost" else endpoint.hostname
    conn = http.client.HTTPConnection(host, endpoint.port, timeout=timeout)
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    try:
        conn.request(method, route, body, {"Content-Type": "application/json", **(headers or {})})
        response = conn.getresponse()
        if not 200 <= response.status < 300:
            raise RuntimeError(f"Local server returned HTTP {response.status} for {route}.")
        content = response.read(2_000_001)
        if len(content) > 2_000_000:
            raise RuntimeError("Local server response exceeds 2 MB.")
        return json.loads(content)
    except (OSError, http.client.HTTPException, ValueError) as error:
        raise RuntimeError(f"Could not use local server at {url}: {error}") from error
    finally:
        conn.close()


@dataclass(frozen=True)
class LocalModel:
    provider: str
    url: str
    model: str
    timeout: int = 120
    max_tokens: int = 700

    def __post_init__(self):
        local_endpoint(self.url)
        if self.provider not in {"ollama", "openai", "zeta", "zeta09"}:
            raise ValueError("Choose a supported model provider.")
        if not self.model.strip() or not 1 <= self.timeout <= 600:
            raise ValueError("Set a model name and a timeout between 1 and 600 seconds.")
        if not 128 <= self.max_tokens <= 32_768:
            raise ValueError("Set a model output limit between 128 and 32768 tokens.")

    @property
    def wire(self):
        return "ollama" if self.provider == "ollama" else "openai"

    def _request(self, method, route, payload=None):
        token = os.environ.get("ZETA_API_KEY") if self.provider in {"zeta", "zeta09"} else None
        headers = {"Authorization": f"Bearer {token}"} if token else None
        return request_json(self.url, method, route, payload, timeout=self.timeout, headers=headers)

    def models(self):
        if self.provider == "ollama":
            return [item["name"] for item in self._request("GET", "/api/tags").get("models", [])]
        return [item["id"] for item in self._request("GET", "/v1/models").get("data", [])]

    def chat(self, messages, tools):
        route, payload = chat_request(
            self.wire, self.model, messages, tools, max_tokens=self.max_tokens, managed=True
        )
        if self.provider == "zeta09":
            payload["system"] = messages[0]["content"]
        response = self._request("POST", route, payload)
        try:
            message = chat_message(self.wire, response)
            if not isinstance(message, dict) or not message:
                raise ValueError("missing assistant message")
            calls = message.get("tool_calls") or []
            content = message.get("content") or ""
            if not isinstance(content, str) or not isinstance(calls, list):
                raise ValueError("malformed assistant message")
            result = {"role": "assistant", "content": content}
            if calls and self.provider != "zeta09":
                result["tool_calls"] = calls
            if self.provider == "ollama" and isinstance(message.get("thinking"), str):
                result["thinking"] = message["thinking"]
            return result
        except (AttributeError, IndexError, TypeError, ValueError) as error:
            raise RuntimeError(f"Invalid response from local model: {error}") from error
