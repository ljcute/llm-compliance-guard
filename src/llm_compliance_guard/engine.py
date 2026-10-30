from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass

from llm_compliance_guard.models import Audit, EvaluateResponse, Hit, Span
from llm_compliance_guard.rules import Rule, RuleSet


_DISPOSITION_RANK = {
    "allow": 0,
    "rewrite_hint": 1,
    "downgrade": 2,
    "human_queue": 3,
    "block": 4,
}


@dataclass
class Engine:
    rule_set: RuleSet

    def evaluate(self, text: str, *, trace_id: str | None = None) -> EvaluateResponse:
        started = time.perf_counter()
        hits: list[Hit] = []
        enabled = sorted(
            (r for r in self.rule_set.rules if r.enabled),
            key=lambda r: r.priority,
        )
        for rule in enabled:
            hit = self._match(rule, text)
            if hit is None:
                continue
            hits.append(hit)
            if rule.disposition == "block" and rule.priority <= 10:
                # short-circuit high-priority blocks
                break

        disposition = "allow"
        for h in hits:
            if _DISPOSITION_RANK[h.disposition] > _DISPOSITION_RANK[disposition]:
                disposition = h.disposition

        latency_ms = (time.perf_counter() - started) * 1000.0
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return EvaluateResponse(
            allowed=disposition == "allow" and not hits,
            disposition=disposition if hits else "allow",
            hits=hits,
            audit=Audit(
                input_sha256=digest,
                rule_set=self.rule_set.name,
                rule_set_version=self.rule_set.version,
                latency_ms=round(latency_ms, 3),
                trace_id=trace_id,
            ),
        )

    def _match(self, rule: Rule, text: str) -> Hit | None:
        for pattern in rule.compiled():
            m = pattern.search(text)
            if not m:
                continue
            start, end = m.span()
            return Hit(
                rule_id=rule.rule_id,
                category=rule.category,
                disposition=rule.disposition,
                message=rule.message,
                span=Span(start=start, end=end, excerpt=text[start:end]),
            )
        return None
