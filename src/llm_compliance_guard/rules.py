from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml

Category = Literal["leak", "promise", "script", "overreach"]
Disposition = Literal["allow", "block", "rewrite_hint", "downgrade", "human_queue"]
Probe = Literal["keyword", "regex"]


@dataclass(frozen=True)
class Rule:
    rule_id: str
    category: Category
    disposition: Disposition
    priority: int
    enabled: bool
    probe: Probe
    patterns: tuple[str, ...]
    message: str
    case_insensitive: bool = True

    def compiled(self) -> list[re.Pattern[str]]:
        flags = re.IGNORECASE if self.case_insensitive else 0
        if self.probe == "keyword":
            return [
                re.compile(re.escape(p), flags)
                for p in self.patterns
                if p
            ]
        return [re.compile(p, flags) for p in self.patterns if p]


@dataclass(frozen=True)
class RuleSet:
    name: str
    version: str
    rules: tuple[Rule, ...]


def _as_rule(raw: dict[str, Any]) -> Rule:
    return Rule(
        rule_id=str(raw["id"]),
        category=raw["category"],
        disposition=raw.get("disposition", "block"),
        priority=int(raw.get("priority", 100)),
        enabled=bool(raw.get("enabled", True)),
        probe=raw.get("probe", "keyword"),
        patterns=tuple(raw.get("patterns") or []),
        message=str(raw.get("message") or raw["id"]),
        case_insensitive=bool(raw.get("case_insensitive", True)),
    )


def load_rule_set(path: Path) -> RuleSet:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    rules = tuple(_as_rule(item) for item in (data.get("rules") or []))
    return RuleSet(
        name=str(data.get("name") or path.stem),
        version=str(data.get("version") or "0.0.0"),
        rules=rules,
    )


def default_examples_path() -> Path:
    # package-adjacent: <repo>/rules/examples/demo.yaml
    here = Path(__file__).resolve()
    repo_root = here.parents[2]
    return repo_root / "rules" / "examples" / "demo.yaml"


def load_named_rule_set(name: str = "examples") -> RuleSet:
    if name != "examples":
        raise FileNotFoundError(f"unknown rule_set: {name}")
    return load_rule_set(default_examples_path())
