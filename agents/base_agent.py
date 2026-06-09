"""Abstract BaseAgent — interface every agent implements."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from core.claude_client import call_claude
from skills.skill import Skill

if TYPE_CHECKING:
    from core.context import AgentContext


class BaseAgent(ABC):
    """
    Every agent must declare:
      - name:   human-readable label
      - skills: list of Skill instances this agent exposes
    And implement:
      - run(context) -> AgentContext  (mutates context, returns it)
    """

    name: str = "BaseAgent"
    skills: list[Skill] = []

    def run(self, context: "AgentContext") -> "AgentContext":
        """Execute the agent, populate context, and return it."""
        raise NotImplementedError

    def call_claude(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int = 1024,
    ) -> str:
        system = system or (
            f"You are the {self.name} in a multi-agent Personal Finance AI system. "
            "Produce structured, specific, data-driven analysis. "
            "Use ## for headings, - for bullets, **text** for bold."
        )
        print(f"  [{self.name}] calling Claude...")
        return call_claude(prompt=prompt, system=system, max_tokens=max_tokens)

    def skill_names(self) -> list[str]:
        return [s.name for s in self.skills]
