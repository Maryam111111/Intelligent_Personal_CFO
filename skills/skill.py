"""Skill dataclass — every agent capability is a Skill instance."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Skill:
    name: str                          # snake_case identifier
    description: str                   # human-readable summary
    prompt_template: str               # Jinja-style {variable} template
    output_schema: Optional[dict] = None  # expected JSON schema (optional)

    def render_prompt(self, **kwargs) -> str:
        """Fill prompt_template with provided variables."""
        try:
            return self.prompt_template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing variable {e} for skill '{self.name}'") from e
