"""Deterministic editorial checks for scripts before production."""

import dataclasses
import typing
import urllib.parse


REQUIRED_SECTIONS = (
    "relatable_financial_problem",
    "escalating_real_world_stakes",
    "clear_explanation_of_why_it_matters",
    "hopeful_and_realistic_possibility",
    "practical_action_viewers_can_take",
    "empowering_close",
)

# These are explicit claims of guaranteed outcomes, not ordinary urgency words.
PROHIBITED_PHRASES = (
    "guaranteed wealth",
    "guarantees wealth",
    "guarantee wealth",
    "guaranteeing wealth",
    "get rich overnight",
    "become rich overnight",
    "risk-free investment returns",
    "guaranteed investment returns",
    "double your money guaranteed",
    "you will definitely become rich",
)

SHAMING_PHRASES = (
    "poor because you are lazy",
    "poverty is your fault",
    "only fools stay poor",
    "you deserve to be poor",
)


@dataclasses.dataclass
class ScriptQualityReport:
    """Result of the deterministic script editorial checks."""

    passed: bool
    errors: list[str] = dataclasses.field(default_factory=list)


def _has_text(value: typing.Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_http_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urllib.parse.urlparse(value.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def validate_script(script: Any) -> ScriptQualityReport:
    """Validate a structured script package against the editorial policy.

    Expected shape:
      {
        "title": "...",
        "sections": {"<required section key>": "..."},
        "claims": [{"text": "...", "sources": ["https://..."]}],
        "hypothetical_examples": [{"label": "Hypothetical example", "text": "..."}]
      }

    This is a deterministic structural and phrase check, not a substitute for
    human-level fact checking or semantic review of financial claims.
    """
    errors: list[str] = []
    if not isinstance(script, dict):
        return ScriptQualityReport(False, ["Script package must be a JSON object"])

    if not _has_text(script.get("title")):
        errors.append("A non-empty script title is required")

    sections = script.get("sections")
    if not isinstance(sections, dict):
        errors.append("Script sections must be an object")
        sections = {}

    combined_parts: list[str] = []
    for section in REQUIRED_SECTIONS:
        value = sections.get(section)
        if not _has_text(value):
            errors.append(f"Required story section is missing or empty: {section}")
        else:
            combined_parts.append(value.strip())

    full_text = " ".join(combined_parts).casefold()
    for phrase in PROHIBITED_PHRASES:
        if phrase in full_text:
            errors.append(f"Prohibited guaranteed-outcome claim detected: '{phrase}'")
    for phrase in SHAMING_PHRASES:
        if phrase in full_text:
            errors.append(f"Shaming language detected: '{phrase}'")

    claims = script.get("claims", [])
    if not isinstance(claims, list):
        errors.append("Claims must be a list")
    else:
        for index, claim in enumerate(claims, start=1):
            if not isinstance(claim, dict) or not _has_text(claim.get("text")):
                errors.append(f"Claim {index} must contain non-empty text")
                continue
            sources = claim.get("sources")
            if not isinstance(sources, list) or not sources:
                errors.append(f"Claim {index} has no supporting source")
                continue
            if not all(_is_http_url(source) for source in sources):
                errors.append(f"Claim {index} contains an invalid source URL")

    examples = script.get("hypothetical_examples", [])
    if not isinstance(examples, list):
        errors.append("hypothetical_examples must be a list")
    else:
        for index, example in enumerate(examples, start=1):
            if not isinstance(example, dict) or not _has_text(example.get("text")):
                errors.append(f"Hypothetical example {index} must contain text")
                continue
            label = example.get("label", "")
            if not _has_text(label) or "hypothetical" not in label.casefold():
                errors.append(
                    f"Hypothetical example {index} must be explicitly labelled hypothetical"
                )

    if "claims" not in script:
        errors.append("A claims list is required, even when it is empty")

    return ScriptQualityReport(passed=not errors, errors=errors)
