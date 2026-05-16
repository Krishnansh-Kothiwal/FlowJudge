import json
import os

from pydantic import ValidationError

from llm import call_role_model
from schemas import FlowState, QualityReview, StartupSummary


def _max_retries() -> int:
    try:
        return int(os.getenv("MAX_RETRIES", "2"))
    except ValueError:
        return 2


def _append_log(state: FlowState, message: str) -> list[str]:
    return [*state.get("logs", []), message]


def _schema_text() -> str:
    return """
{
  "title": "string",
  "summary": "string",
  "target_users": ["string", "string"],
  "core_features": ["string", "string", "string"],
  "risks": ["string", "string"]
}
Extra keys are not allowed.
"""


def _parse_json_object(text: str) -> dict:
    cleaned = (text or "").strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```json").removeprefix("```").strip()
        cleaned = cleaned.removesuffix("```").strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(cleaned[start : end + 1])


def planner_node(state: FlowState) -> dict:
    plan = (
        "Generate a concise StartupSummary JSON object tailored to the task. "
        "Include a specific title and summary, at least two meaningful target users, "
        "at least three concrete core features, and at least two realistic risks."
    )
    return {
        "plan": plan,
        "logs": _append_log(state, "Planner created the JSON generation plan."),
    }


def generator_node(state: FlowState) -> dict:
    prompt = f"""
You are the Generator Agent for FlowJudge.

User task:
{state["task"]}

Planner decision:
{state["plan"]}

Return raw JSON only. Do not use markdown. Do not use code fences.
Use exactly these keys and no others:
title, summary, target_users, core_features, risks

Required schema:
{_schema_text()}
"""
    response, provider_label = call_role_model("generator", prompt)
    history = [*state.get("provider_history", []), provider_label]
    return {
        "raw_output": response,
        "current_output": response,
        "provider_used": provider_label,
        "provider_history": history,
        "logs": _append_log(state, f"Generator completed using {provider_label}."),
    }


def schema_verifier_node(state: FlowState) -> dict:
    try:
        data = _parse_json_object(state.get("current_output", ""))
        validated = StartupSummary.model_validate(data)
        return {
            "validated": True,
            "final": validated.model_dump(),
            "schema_error": None,
            "logs": _append_log(state, "Schema verifier passed."),
        }
    except json.JSONDecodeError as exc:
        message = f"Invalid JSON: {exc.msg}"
    except ValidationError as exc:
        first_error = exc.errors()[0] if exc.errors() else {}
        location = ".".join(str(part) for part in first_error.get("loc", []))
        detail = first_error.get("msg", "Validation failed")
        message = f"{location}: {detail}" if location else detail

    return {
        "validated": False,
        "final": None,
        "schema_error": message,
        "logs": _append_log(state, f"Schema verifier failed: {message}"),
    }


def quality_critic_node(state: FlowState) -> dict:
    prompt = f"""
You are the Quality Critic Agent for FlowJudge.

User task:
{state["task"]}

Validated JSON:
{json.dumps(state.get("final"), indent=2)}

Judge whether the JSON is high quality.
Criteria:
- output must be specific to the user task
- not generic
- target_users must be meaningful
- core_features must be concrete
- risks must be realistic
- professional but not bloated

Return only this JSON shape:
{{
  "passed": true,
  "feedback": "..."
}}
"""
    response, provider_label = call_role_model("critic", prompt)
    history = [*state.get("provider_history", []), provider_label]

    try:
        review_data = _parse_json_object(response)
        review = QualityReview.model_validate(review_data)
        return {
            "quality_passed": review.passed,
            "quality_feedback": review.feedback,
            "provider_used": provider_label,
            "provider_history": history,
            "logs": _append_log(state, f"Quality critic completed using {provider_label}."),
        }
    except (json.JSONDecodeError, ValidationError):
        return {
            "quality_passed": False,
            "quality_feedback": "Critic response could not be parsed.",
            "provider_used": provider_label,
            "provider_history": history,
            "logs": _append_log(state, "Critic parsing failed."),
        }


def repair_node(state: FlowState) -> dict:
    prompt = f"""
You are the Repair Agent for FlowJudge.

Original task:
{state["task"]}

Planner output:
{state["plan"]}

Previous output:
{state.get("current_output", "")}

Schema error, if any:
{state.get("schema_error") or "None"}

Quality feedback, if any:
{state.get("quality_feedback") or "None"}

Repair the output so it satisfies the exact required schema and quality criteria.
Return raw JSON only. Do not use markdown. Do not use code fences.

Exact required schema:
{_schema_text()}
"""
    response, provider_label = call_role_model("repair", prompt)
    history = [*state.get("provider_history", []), provider_label]
    repair_history = [*state.get("repair_history", []), provider_label]
    retries = state.get("retries", 0) + 1

    return {
        "repaired_output": response,
        "current_output": response,
        "provider_used": provider_label,
        "provider_history": history,
        "repair_history": repair_history,
        "retries": retries,
        "logs": _append_log(state, f"Repair attempt {retries} completed using {provider_label}."),
    }


def route_after_schema_verifier(state: FlowState) -> str:
    if not state.get("validated", False):
        if state.get("retries", 0) < _max_retries():
            return "repair"
        return "end"
    return "quality_critic"


def route_after_quality_critic(state: FlowState) -> str:
    if state.get("quality_passed", False):
        return "end"
    if state.get("retries", 0) < _max_retries():
        return "repair"
    return "end"
