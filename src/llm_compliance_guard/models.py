from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Category = Literal["leak", "promise", "script", "overreach"]
Disposition = Literal["allow", "block", "rewrite_hint", "downgrade", "human_queue"]


class Span(BaseModel):
    start: int
    end: int
    excerpt: str


class Hit(BaseModel):
    rule_id: str
    category: Category
    disposition: Disposition
    message: str
    span: Span | None = None


class Audit(BaseModel):
    input_sha256: str
    rule_set: str
    rule_set_version: str
    latency_ms: float
    trace_id: str | None = None


class EvaluateRequest(BaseModel):
    text: str = Field(..., min_length=0, max_length=100_000)
    trace_id: str | None = None
    rule_set: str = "examples"


class EvaluateResponse(BaseModel):
    allowed: bool
    disposition: Disposition
    hits: list[Hit]
    audit: Audit


class RuleInfo(BaseModel):
    rule_id: str
    category: Category
    disposition: Disposition
    priority: int
    enabled: bool


class RulesResponse(BaseModel):
    rule_set: str
    version: str
    rules: list[RuleInfo]
