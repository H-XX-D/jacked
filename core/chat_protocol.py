"""Request and response shapes shared by FRIDAY and the MATRIX harness."""

import json


def chat_request(provider, model, messages, tools=None, *, max_tokens=150, managed=False):
    payload = {"model": model, "messages": messages, "stream": False}
    if tools:
        payload["tools"] = tools

    if provider == "openai":
        payload["max_tokens"] = max_tokens
        if tools:
            payload["tool_choice"] = "auto"
        return "/v1/chat/completions", payload

    payload["keep_alive"] = "2m" if managed else -1
    payload["options"] = {"num_predict": max_tokens}
    if managed:
        payload["options"]["num_ctx"] = 8192
    else:
        payload["options"]["num_gpu"] = 99
    return "/api/chat", payload


def chat_message(provider, response):
    if provider == "openai":
        return response.get("choices", [{}])[0].get("message", {})
    return response.get("message", {})


def tool_arguments(function):
    arguments = function.get("arguments", {})
    return json.loads(arguments) if isinstance(arguments, str) else arguments
