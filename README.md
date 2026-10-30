# llm-compliance-guard

Rule-engine guard for **LLM outputs**: keyword / regex / (optional) semantic checks, four example violation classes, dispositions, and an audit trail.

Not a general moderation platform. No model training. Demo rules are synthetic and desensitized — not real customer or employer policy packs.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn llm_compliance_guard.http_app:app --reload --port 8080
```

Check health:

```bash
curl -s http://127.0.0.1:8080/health
```

Evaluate sample text:

```bash
curl -s -X POST http://127.0.0.1:8080/v1/evaluate \
  -H 'content-type: application/json' \
  -d '{"text":"恭喜您！保证到账年化收益 20%。","trace_id":"demo-1"}'
```

## HTTP API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Liveness |
| `GET` | `/v1/rules` | Loaded rule ids + versions |
| `POST` | `/v1/evaluate` | Run the guard on one output string |

### `POST /v1/evaluate`

Request:

```json
{
  "text": "model output to check",
  "trace_id": "optional-biz-trace",
  "rule_set": "examples"
}
```

Response (shape):

```json
{
  "allowed": false,
  "disposition": "block",
  "hits": [
    {
      "rule_id": "ex-promise-guaranteed-yield",
      "category": "promise",
      "severity": "block",
      "message": "Guaranteed yield / arrival claims are not allowed in demo rules.",
      "span": { "start": 4, "end": 16, "excerpt": "保证到账年化收益" }
    }
  ],
  "audit": {
    "input_sha256": "...",
    "rule_set": "examples",
    "rule_set_version": "0.1.0",
    "latency_ms": 1.2,
    "trace_id": "demo-1"
  }
}
```

## Violation taxonomy (demo)

| Category | Meaning | Typical disposition |
| --- | --- | --- |
| `leak` | Unauthorized entities / credential-like patterns | `block` |
| `promise` | Improper yield / arrival guarantees | `block` or `rewrite_hint` |
| `script` | Aggressive or coercive marketing copy | `block` or `downgrade` |
| `overreach` | Instructions beyond tool permissions | `block` + queue |

## Layout

```
src/llm_compliance_guard/   # engine + FastAPI app
rules/examples/             # desensitized demo YAML rules
tests/                      # pytest
```

## Design notes

Companion write-up on the personal site: [LLM 输出合规校验器设计](https://batyuk.cn/notes/llm-compliance-guard-design) (also `/open-source`).

Semantic similarity probes are stubbed off by default in this MVP (HTTP + keyword/regex first).

## License

MIT
