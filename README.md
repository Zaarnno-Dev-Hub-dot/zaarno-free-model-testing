# Zaarno Free Model Testing

Free-tier cloud LLM benchmark harness — run dozens of models across coder / writer / researcher disciplines and compare results in HTML reports.

## What it is

Python scripts that call free or free-tier APIs (OpenRouter, NVIDIA NIM, Mistral/Codestral, Cloudflare Workers AI, and similar), score responses on three disciplines, and write JSON + HTML under `results/`.

**Optional gateway:** You can route single tasks through a local [FreeLLMAPI](https://github.com/Zaarnno-Dev-Hub-dot/zaarno-freellmapi)-compatible proxy via `dispatch.py` (`FREELMAPI_URL` / `FREELMAPI_KEY`). FreeLLMAPI is used here as optional gateway plumbing — **not claimed as original Zaarno IP**. The discipline harness talks to providers directly for cleaner per-model numbers.

## Features

- Multi-provider free-model matrix (`run_discipline_tests.py`)
- Three disciplines: coder, writer, researcher
- HTML reports under `results/` (e.g. `final_report.html`, `decision_matrix.html`) plus JSON dumps
- `dispatch.py` — ordered fallback chain through a FreeLLMAPI-compatible endpoint

## Quick start

```bash
git clone https://github.com/Zaarnno-Dev-Hub-dot/zaarno-free-model-testing.git
cd zaarno-free-model-testing
cp .env.example .env
# Fill keys in .env (never commit .env)

# Full discipline suite (can take a while)
python3 run_discipline_tests.py

# Optional: one-shot via local FreeLLMAPI gateway
# export FREELMAPI_URL=http://127.0.0.1:3003/v1/chat/completions
# export FREELMAPI_KEY=your-local-bearer
python3 dispatch.py coder "Write a Python flatten_json function"
```

Open results in a browser:

- [`results/final_report.html`](results/final_report.html)
- [`results/decision_matrix.html`](results/decision_matrix.html)

## Environment

See `.env.example` for provider key names. Copy to `.env` and set only the providers you use. Keys never belong in git.

## Security

API keys live in `.env` (gitignored) or your secret store — never in tracked files. Rotate anything that ever landed in git history.

## License

MIT — see [LICENSE](LICENSE). Copyright (c) 2026 Zachary Arnold.

Anyone may use, modify, and redistribute this harness under the MIT terms.
