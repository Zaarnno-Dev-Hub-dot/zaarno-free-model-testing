# Agent notes — Free Model Testing

## Relationship to other LLM projects

| Layer | Project | Port |
|-------|---------|------|
| Cloud API gateway | [zaarno-freellmapi](https://github.com/Zaarnno-Dev-Hub-dot/zaarno-freellmapi) | :3003 |
| Cloud model benchmarks | This repo | — |
| Local model benchmarks | [zaarno-local-llm-benchmark](https://github.com/Zaarnno-Dev-Hub-dot/zaarno-local-llm-benchmark) | Ollama :11434 |

This harness tests providers **directly** (not through freellmapi) for cleaner per-model results. Use `dispatch.py` when you want freellmapi's fallback routing in production.

## Before running

1. Copy `.env.example` → `.env`, fill provider keys
2. Do not commit `.env` or paste keys into scripts
3. Check `~/PORTS.md` if using freellmapi via `dispatch.py`

## Outputs

- `results/discipline_results.json` — raw per-model scores
- `results/final_report.html` — visual summary with bucket breakdown
- `results/decision_matrix.html` — pick chart for wiring into Hermes configs

## Next integration step

Wire top picks from `decision_matrix.html` into Hermes `config.yaml` and freellmapi provider keys per skill `~/.hermes/skills/devops/freellmapi-provider-integration/SKILL.md`.