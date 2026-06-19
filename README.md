# Zaarno Free Model Testing

Benchmark harness for **free-tier cloud LLM APIs** — tests 35+ models across OpenRouter, NVIDIA NIM, Mistral, Codestral, and Cloudflare Workers AI using three disciplines: Coder, Writer, Researcher.

**GitHub:** [Zaarnno-Dev-Hub-dot/zaarno-free-model-testing](https://github.com/Zaarnno-Dev-Hub-dot/zaarno-free-model-testing)  
**Gateway (production proxy):** [zaarno-freellmapi](https://github.com/Zaarnno-Dev-Hub-dot/zaarno-freellmapi) on `127.0.0.1:3003`  
**Local LLM benchmarks:** [zaarno-local-llm-benchmark](https://github.com/Zaarnno-Dev-Hub-dot/zaarno-local-llm-benchmark)

## Results (May 2026 run)

| Metric | Value |
|--------|-------|
| Models tested | 35 across 6 providers |
| Full generalists (3/3 disciplines) | 16 |
| Top picks | Poolside XS.2, Codestral, Nemotron Nano 30B, GPT-OSS 120B |

Open `results/final_report.html` or `results/decision_matrix.html` in a browser for the full visual report.

## Quick start

```bash
cd ~/Desktop/My\ Projects/Free\ Model\ Testing
cp .env.example .env
# Fill keys in .env (or export from ~/.secrets/)

# Run full discipline suite (~30–60 min)
python3 run_discipline_tests.py

# Route a single task through freellmapi fallback chain
export FREELMAPI_KEY=your-freellmapi-bearer-token
python3 dispatch.py coder "Write a Python flatten_json function"
```

## Scripts

| File | Purpose |
|------|---------|
| `run_discipline_tests.py` | Full 3-discipline benchmark across all configured models |
| `dispatch.py` | Task router — picks best free model per discipline via freellmapi |
| `results/` | JSON + HTML reports from benchmark runs |

## Providers tested

- **OpenRouter** — 19 free models (Llama, GPT-OSS, Nemotron, Poolside, etc.)
- **NVIDIA NIM** — Llama 3.3/4, Nemotron, Mistral Large
- **Mistral** — Large, Medium, Devstral, Magistral
- **Codestral** — codestral-latest (fast coder)
- **Cloudflare Workers AI** — Kimi, DeepSeek distill, Llama Scout, GLM, GPT-OSS

## Security

API keys must live in `.env` or `~/.secrets/` — never in git. If keys were previously in plaintext scripts, rotate them.

## Agent notes

See `AGENTS.md`. Wiki runbook: `~/wiki/projects/free-model-testing/run.md`.