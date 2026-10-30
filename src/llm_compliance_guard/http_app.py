from __future__ import annotations

from functools import lru_cache

from fastapi import FastAPI, HTTPException

from llm_compliance_guard import __version__
from llm_compliance_guard.engine import Engine
from llm_compliance_guard.models import (
    EvaluateRequest,
    EvaluateResponse,
    RuleInfo,
    RulesResponse,
)
from llm_compliance_guard.rules import load_named_rule_set

app = FastAPI(
    title="llm-compliance-guard",
    version=__version__,
    description="Rule-engine guard for LLM outputs (keyword/regex MVP).",
)


@lru_cache(maxsize=8)
def get_engine(rule_set: str) -> Engine:
    try:
        rs = load_named_rule_set(rule_set)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Engine(rule_set=rs)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@app.get("/v1/rules", response_model=RulesResponse)
def list_rules(rule_set: str = "examples") -> RulesResponse:
    engine = get_engine(rule_set)
    rs = engine.rule_set
    return RulesResponse(
        rule_set=rs.name,
        version=rs.version,
        rules=[
            RuleInfo(
                rule_id=r.rule_id,
                category=r.category,
                disposition=r.disposition,
                priority=r.priority,
                enabled=r.enabled,
            )
            for r in rs.rules
        ],
    )


@app.post("/v1/evaluate", response_model=EvaluateResponse)
def evaluate(body: EvaluateRequest) -> EvaluateResponse:
    engine = get_engine(body.rule_set)
    return engine.evaluate(body.text, trace_id=body.trace_id)


def main() -> None:
    import uvicorn

    uvicorn.run(
        "llm_compliance_guard.http_app:app",
        host="0.0.0.0",
        port=8080,
        reload=False,
    )


if __name__ == "__main__":
    main()
