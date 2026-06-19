#!/usr/bin/env python3
"""
Free Model Dispatcher — Routes task types to the best free model.
Uses freellmapi as the unified proxy (localhost:3003).

Usage:
  python3 dispatch.py coder "Write a Python function..."
  python3 dispatch.py writer "Write a tweet thread..."
  python3 dispatch.py researcher "Compare these tools..."
  python3 dispatch.py auto "Any task..."  # auto-picks best all-rounder
"""

import json, subprocess, sys, time

import os

FREELMAPI_URL = os.environ.get("FREELMAPI_URL", "http://127.0.0.1:3003/v1/chat/completions")
FREELMAPI_KEY = os.environ.get("FREELMAPI_KEY", "")

# Discipline → ordered model list (best first, fallback chain)
ROUTES = {
    "coder": [
        {"model": "codestral-latest", "provider": "codestral", "note": "Fastest coder (2.5s)"},
        {"model": "poolside/laguna-xs.2:free", "provider": "openrouter", "note": "Best speed-quality (4.5s)"},
        {"model": "nvidia/nemotron-3-nano-30b-a3b", "provider": "nvidia", "note": "Fast NVIDIA (2.5s)"},
        {"model": "openai/gpt-oss-120b:free", "provider": "openrouter", "note": "Strong generalist (14s)"},
        {"model": "minimax/minimax-m2.5:free", "provider": "openrouter", "note": "Newly unblocked"},
        # Ollama Cloud route (separate pathway)
        {"model": "qwen3-coder:480b-cloud", "provider": "ollama-cloud", "note": "480B coder (3.6s)"},
        {"model": "gpt-oss:20b-cloud", "provider": "ollama-cloud", "note": "Fast 20B (3.8s)"},
    ],
    "writer": [
        {"model": "mistral-large-latest", "provider": "mistral", "note": "Best writer (4.7s)"},
        {"model": "poolside/laguna-xs.2:free", "provider": "openrouter", "note": "Strong writer (4.9s)"},
        {"model": "@cf/meta/llama-4-scout-17b-16e-instruct", "provider": "cloudflare", "note": "Fast Cloudflare (2.3s)"},
        {"model": "meta/llama-4-maverick-17b-128e-instruct", "provider": "nvidia", "note": "Solid writer (14.8s)"},
        {"model": "gpt-oss:20b-cloud", "provider": "ollama-cloud", "note": "Fast writer (4.4s)"},
    ],
    "researcher": [
        {"model": "openai/gpt-oss-120b:free", "provider": "openrouter", "note": "Best researcher (16.6s)"},
        {"model": "mistral-large-latest", "provider": "mistral", "note": "Fast researcher (6.6s)"},
        {"model": "@cf/meta/llama-3.3-70b-instruct-fp8-fast", "provider": "cloudflare", "note": "Good researcher (7.1s)"},
        {"model": "meta/llama-3.3-70b-instruct", "provider": "nvidia", "note": "Deep researcher (5.1s)"},
        {"model": "gpt-oss:120b-cloud", "provider": "ollama-cloud", "note": "Strong researcher (12.3s)"},
    ],
    "auto": [
        {"model": "poolside/laguna-xs.2:free", "provider": "openrouter", "note": "Best all-rounder (4.5s)"},
        {"model": "gpt-oss:20b-cloud", "provider": "ollama-cloud", "note": "Fast generalist (4.7s avg)"},
        {"model": "mistral-large-latest", "provider": "mistral", "note": "Strong all-rounder (4.9s)"},
        {"model": "codestral-latest", "provider": "codestral", "note": "Fast generalist (2.5s)"},
        {"model": "@cf/meta/llama-4-scout-17b-16e-instruct", "provider": "cloudflare", "note": "Good all-rounder (3.5s)"},
    ],
}


def call_freellmapi(model_id, prompt, timeout=60):
    """Call a model through freellmapi."""
    data = json.dumps({
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
    })

    cmd = [
        "curl", "-s", "-w", "\n%{http_code}",
        FREELMAPI_URL,
        "-H", f"Authorization: Bearer {FREELMAPI_KEY}",
        "-H", "Content-Type: application/json",
        "-d", data,
        "--max-time", str(timeout),
    ]

    start = time.time()
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=timeout + 5).decode()
        latency = round(time.time() - start, 2)
        parts = output.rsplit("\n", 1)
        http_code = parts[-1].strip()
        body = parts[0]

        if http_code != "200":
            return {"success": False, "error": f"HTTP {http_code}", "latency": latency, "body": body[:200]}

        resp = json.loads(body)
        msg = resp.get("choices", [{}])[0].get("message", {})
        content = msg.get("content") or msg.get("reasoning") or ""
        usage = resp.get("usage", {})
        routed = resp.get("_routed_via", {})

        return {
            "success": True,
            "content": content.strip(),
            "latency": latency,
            "tokens": (usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)),
            "routed_via": routed,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "timeout", "latency": round(time.time() - start, 2)}
    except Exception as e:
        return {"success": False, "error": str(e)[:80], "latency": round(time.time() - start, 2)}


def dispatch(discipline, prompt):
    """Try each model in the route chain until one succeeds."""
    if discipline not in ROUTES:
        print(f"Unknown discipline: {discipline}")
        print(f"Available: {', '.join(ROUTES.keys())}")
        return None

    chain = ROUTES[discipline]
    print(f"📋 Dispatching: {discipline}")
    print(f"📝 Prompt: {prompt[:60]}...")
    print()

    for i, route in enumerate(chain):
        print(f"  [{i + 1}/{len(chain)}] {route['model']} ({route['note']})... ", end="", flush=True)
        result = call_freellmapi(route["model"], prompt)

        if result["success"]:
            print(f"✅ {result['latency']}s | {result['tokens'][0] + result['tokens'][1]} tokens")
            print(f"     Routed via: {result['routed_via']}")
            print()
            print("─" * 50)
            print(result["content"])
            print("─" * 50)
            return result
        else:
            print(f"❌ {result['error']} ({result['latency']}s)")
            if i < len(chain) - 1:
                print(f"     ↳ Falling back...")

    print("  All models in chain failed.")
    return None


if __name__ == "__main__":
    if not FREELMAPI_KEY:
        print("Set FREELMAPI_KEY (see .env.example)", file=sys.stderr)
        sys.exit(1)
    if len(sys.argv) < 3:
        print("Usage: python3 dispatch.py <discipline> <prompt>")
        print(f"  Disciplines: {', '.join(ROUTES.keys())}")
        print(f"  Example: python3 dispatch.py coder 'Write a Python function...'")
        sys.exit(1)

    discipline = sys.argv[1]
    prompt = " ".join(sys.argv[2:])
    dispatch(discipline, prompt)