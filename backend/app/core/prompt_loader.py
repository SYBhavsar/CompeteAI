"""
Prompt Loader

Purpose: Load and parse markdown prompt files with YAML frontmatter.
Prompt files live in app/prompts/{name}.md
"""
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


@dataclass
class PromptConfig:
    service: str
    default_model: str
    default_provider: str
    temperature: float
    max_tokens: int
    system_prompt: str
    user_prompt: str


class PromptLoader:
    _cache: dict[str, PromptConfig] = {}

    @staticmethod
    def load(prompt_name: str) -> PromptConfig:
        """
        Load and parse a prompt markdown file.

        Args:
            prompt_name: Name without extension (e.g. 'summarization')

        Returns:
            PromptConfig with parsed frontmatter and prompt sections

        Raises:
            FileNotFoundError: If the prompt file does not exist
        """
        if prompt_name in PromptLoader._cache:
            return PromptLoader._cache[prompt_name]

        path = PROMPTS_DIR / f"{prompt_name}.md"
        if not path.exists():
            raise FileNotFoundError(f"Prompt file not found: {path}")

        raw = path.read_text(encoding="utf-8")
        frontmatter, body = PromptLoader._parse_frontmatter(raw)
        system_prompt, user_prompt = PromptLoader._parse_sections(body)

        config = PromptConfig(
            service=frontmatter.get("service", prompt_name),
            default_model=frontmatter.get("default_model", "gpt-3.5-turbo"),
            default_provider=frontmatter.get("default_provider", "openai"),
            temperature=float(frontmatter.get("temperature", 0.3)),
            max_tokens=int(frontmatter.get("max_tokens", 500)),
            system_prompt=system_prompt.strip(),
            user_prompt=user_prompt.strip(),
        )

        PromptLoader._cache[prompt_name] = config
        logger.debug("Loaded prompt '%s' from %s", prompt_name, path)
        return config

    @staticmethod
    def get_default_config(prompt_name: str) -> dict[str, Any]:
        """Return only the frontmatter config dict for the named prompt."""
        config = PromptLoader.load(prompt_name)
        return {
            "service": config.service,
            "default_model": config.default_model,
            "default_provider": config.default_provider,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
        }

    @staticmethod
    def _parse_frontmatter(raw: str) -> tuple[dict[str, Any], str]:
        if not raw.startswith("---"):
            return {}, raw

        end = raw.find("---", 3)
        if end == -1:
            return {}, raw

        yaml_text = raw[3:end].strip()
        body = raw[end + 3:].strip()
        frontmatter: dict[str, Any] = yaml.safe_load(yaml_text) or {}
        return frontmatter, body

    @staticmethod
    def _parse_sections(body: str) -> tuple[str, str]:
        """Parse # System and # User sections from markdown body."""
        system_lines: list[str] = []
        user_lines: list[str] = []
        current_section: str | None = None

        for line in body.splitlines():
            stripped = line.strip()
            if stripped == "# System":
                current_section = "system"
                continue
            if stripped == "# User":
                current_section = "user"
                continue

            if current_section == "system":
                system_lines.append(line)
            elif current_section == "user":
                user_lines.append(line)

        return "\n".join(system_lines).strip(), "\n".join(user_lines).strip()
