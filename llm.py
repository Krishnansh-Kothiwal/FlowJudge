import os
from typing import Callable

import google.generativeai as genai
import requests
from dotenv import load_dotenv


load_dotenv(override=True)

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _request_timeout() -> int:
    try:
        return int(_env("REQUEST_TIMEOUT", "45"))
    except ValueError:
        return 45


def _split_models(value: str, default: str) -> list[str]:
    configured = value or default
    models = [model.strip() for model in configured.split(",") if model.strip()]
    return models or [default]


def _dedupe_candidates(candidates: list[tuple[str, str, str]]) -> list[tuple[str, str, str]]:
    seen: set[tuple[str, str, str]] = set()
    unique: list[tuple[str, str, str]] = []
    for label, provider, model in candidates:
        key = (label, provider, model)
        if key not in seen:
            unique.append((label, provider, model))
            seen.add(key)
    return unique


def _clean_response(text: str) -> str:
    text = (text or "").strip()
    if not text:
        raise RuntimeError("Provider returned an empty response.")
    return text


def call_nvidia(prompt: str, model: str) -> str:
    api_key = _env("NVIDIA_API_KEY")
    if not api_key:
        raise RuntimeError("NVIDIA_API_KEY is missing.")

    try:
        response = requests.post(
            NVIDIA_BASE_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": 1200,
            },
            timeout=_request_timeout(),
        )
    except requests.Timeout as exc:
        raise RuntimeError("NVIDIA request timed out.") from exc
    except requests.RequestException as exc:
        raise RuntimeError(f"NVIDIA request failed: {exc}") from exc

    if response.status_code == 429:
        raise RuntimeError("NVIDIA rate limit reached.")
    if response.status_code >= 400:
        raise RuntimeError(f"NVIDIA provider error {response.status_code}: {response.text[:300]}")

    try:
        data = response.json()
        text = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise RuntimeError("NVIDIA returned a malformed response.") from exc

    return _clean_response(text)


def list_gemini_generate_content_models() -> list[str]:
    api_key = _env("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing.")

    try:
        genai.configure(api_key=api_key)
        models = genai.list_models()
    except Exception as exc:
        raise RuntimeError(f"Could not list Gemini models: {exc}") from exc

    names: list[str] = []
    for model in models:
        methods = getattr(model, "supported_generation_methods", []) or []
        if "generateContent" in methods:
            name = getattr(model, "name", "")
            names.append(name.removeprefix("models/"))
    return sorted(names)


def _gemini_model_help() -> str:
    try:
        models = list_gemini_generate_content_models()
    except RuntimeError as exc:
        return f"Could not list available Gemini models. {exc}"

    if not models:
        return "No Gemini models with generateContent support were returned for this API key."

    preview = ", ".join(models[:12])
    suffix = "" if len(models) <= 12 else f", and {len(models) - 12} more"
    return f"Available Gemini generateContent models for this key include: {preview}{suffix}."


def call_gemini(prompt: str, model: str) -> str:
    api_key = _env("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing.")

    try:
        genai.configure(api_key=api_key)
        gemini_model = genai.GenerativeModel(model)
        response = gemini_model.generate_content(
            prompt,
            generation_config={"temperature": 0.2, "max_output_tokens": 1200},
            request_options={"timeout": _request_timeout()},
        )
        text = getattr(response, "text", "")
    except Exception as exc:
        message = str(exc)
        if "404" in message or "not found" in message or "not supported" in message:
            raise RuntimeError(
                f"Gemini model '{model}' is unavailable or does not support generateContent. "
                f"Set CRITIC_MODEL in .env to an available model. {_gemini_model_help()}"
            ) from exc
        raise RuntimeError(f"Gemini request failed: {exc}") from exc

    return _clean_response(text)


def _provider_call(provider: str) -> Callable[[str, str], str]:
    if provider == "nvidia":
        return call_nvidia
    if provider == "gemini":
        return call_gemini
    raise RuntimeError(f"Unsupported provider: {provider}")


def _role_candidates(role: str) -> list[tuple[str, str, str]]:
    generator_provider = _env("GENERATOR_PROVIDER", "nvidia").lower()
    generator_models = _split_models(_env("GENERATOR_MODEL"), "google/gemma-4-31b-it")
    critic_provider = _env("CRITIC_PROVIDER", "gemini").lower()
    critic_models = _split_models(_env("CRITIC_MODEL"), "gemini-3.1-flash-lite")
    repair_provider = _env("REPAIR_PROVIDER", "auto").lower()
    
    gen_fallback_provider = _env("GENERATOR_FALLBACK_PROVIDER", critic_provider).lower()
    gen_fallback_models = _split_models(_env("GENERATOR_FALLBACK_MODEL"), _env("CRITIC_MODEL", "gemini-3.1-flash-lite"))

    if role == "generator":
        candidates = [("generator", generator_provider, model) for model in generator_models]
        candidates.extend(("generator fallback", gen_fallback_provider, model) for model in gen_fallback_models)
        return _dedupe_candidates(candidates)
    if role == "critic":
        return [("critic", critic_provider, model) for model in critic_models]
    if role == "repair":
        if repair_provider == "auto":
            candidates = [("repair", generator_provider, model) for model in generator_models]
            candidates.extend(("repair fallback", gen_fallback_provider, model) for model in gen_fallback_models)
            return _dedupe_candidates(candidates)
        repair_models = generator_models if repair_provider == "nvidia" else critic_models
        return [("repair", repair_provider, model) for model in repair_models]
    raise RuntimeError(f"Unsupported role: {role}")


def call_role_model(role: str, prompt: str) -> tuple[str, str]:
    failures: list[str] = []

    for label_role, provider, model in _role_candidates(role):
        provider_model_label = f"{label_role}: {provider}/{model}"
        try:
            text = _provider_call(provider)(prompt, model)
            return text, provider_model_label
        except RuntimeError as exc:
            failures.append(f"{provider_model_label} failed: {exc}")

    joined = " | ".join(failures) if failures else "No providers configured."
    raise RuntimeError(f"All allowed providers failed for {role}. {joined}")
