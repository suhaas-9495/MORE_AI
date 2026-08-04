import yaml
import os
from typing import Dict, Optional
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

# cache loaded prompts — don't re-read from disk on every call
_prompt_cache: Dict[str, dict] = {}


def load_prompt(agent_type: str) -> dict:
    """
    Loads prompt config from YAML file.
    Falls back to hardcoded prompt if file not found.
    Cached after first load — hot-reload on version bump.
    """
    if agent_type in _prompt_cache:
        return _prompt_cache[agent_type]

    prompt_file = PROMPTS_DIR / f"{agent_type}.yaml"
    if not prompt_file.exists():
        return {"system_prompt": _get_fallback_prompt(agent_type)}

    with open(prompt_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    _prompt_cache[agent_type] = config
    print(f"[PromptLoader] Loaded {agent_type} v{config.get('version', '?')}")
    return config


def get_system_prompt(agent_type: str) -> str:
    """Returns the system prompt string for an agent type."""
    config = load_prompt(agent_type)
    return config.get("system_prompt", _get_fallback_prompt(agent_type))


def get_prompt_version(agent_type: str) -> str:
    """Returns current version of a prompt."""
    config = load_prompt(agent_type)
    return config.get("version", "unknown")


def get_prompt_changelog(agent_type: str) -> list:
    """Returns full changelog for a prompt — visible in API."""
    config = load_prompt(agent_type)
    return config.get("changelog", [])


def reload_prompt(agent_type: str):
    """Force reload a prompt from disk — use after editing YAML."""
    if agent_type in _prompt_cache:
        del _prompt_cache[agent_type]
    return load_prompt(agent_type)


def _get_fallback_prompt(agent_type: str) -> str:
    """Hardcoded fallbacks — used if YAML file is missing."""
    fallbacks = {
        "planner": "You are a senior software architect. Break down tasks into clear numbered steps.",
        "coder": "You are an expert Python engineer. Write clean production-grade code.",
        "reviewer": "You are a senior code reviewer. Identify bugs, security issues, and improvements.",
        "tester": "You are a QA engineer. Write pytest unit tests for the given code.",
        "researcher": "You are a technical researcher. Research best practices and patterns.",
        "documenter": "You are a technical writer. Generate clear developer documentation.",
    }
    return fallbacks.get(agent_type, "You are a helpful AI assistant.")