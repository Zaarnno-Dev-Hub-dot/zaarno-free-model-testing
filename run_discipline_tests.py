#!/usr/bin/env python3
"""
Discipline Test Runner — Free Model Testing v1
Tests all working models across 3 disciplines: Coder, Writer, Researcher
"""
import json, subprocess, time, os, re, sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def _require_env(name: str) -> str:
    val = os.environ.get(name, "").strip()
    if not val:
        print(f"Missing env var: {name} (see .env.example)", file=sys.stderr)
        sys.exit(1)
    return val

_cf_account = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()

# === API KEYS (from environment — never commit secrets) ===
KEYS = {
    "openrouter": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "key": os.environ.get("OPENROUTER_API_KEY", ""),
        "headers": {"HTTP-Referer": "https://localhost", "X-Title": "Free Model Testing"},
    },
    "nvidia": {
        "url": "https://integrate.api.nvidia.com/v1/chat/completions",
        "key": os.environ.get("NVIDIA_API_KEY", ""),
        "headers": {},
    },
    "mistral": {
        "url": "https://api.mistral.ai/v1/chat/completions",
        "key": os.environ.get("MISTRAL_API_KEY", ""),
        "headers": {},
    },
    "codestral": {
        "url": "https://codestral.mistral.ai/v1/chat/completions",
        "key": os.environ.get("CODESTRAL_API_KEY", ""),
        "headers": {},
    },
    "cloudflare": {
        "url": f"https://api.cloudflare.com/client/v4/accounts/{_cf_account}/ai/v1/chat/completions" if _cf_account else "",
        "key": os.environ.get("CLOUDFLARE_API_TOKEN", ""),
        "headers": {},
    },
}

# === MODELS (all confirmed working in pulse check) ===
MODELS = [
    # OpenRouter standard
    ("openrouter", "liquid/lfm-2.5-1.2b-instruct:free"),
    ("openrouter", "openai/gpt-oss-120b:free"),
    ("openrouter", "openai/gpt-oss-20b:free"),
    ("openrouter", "nvidia/nemotron-3-super-120b-a12b:free"),
    # OpenRouter reasoning
    ("openrouter", "nvidia/nemotron-3-nano-30b-a3b:free"),
    ("openrouter", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"),
    ("openrouter", "nvidia/nemotron-nano-9b-v2:free"),
    ("openrouter", "liquid/lfm-2.5-1.2b-thinking:free"),
    ("openrouter", "poolside/laguna-m.1:free"),
    ("openrouter", "poolside/laguna-xs.2:free"),
    ("openrouter", "z-ai/glm-4.5-air:free"),
    # NVIDIA standard
    ("nvidia", "meta/llama-3.3-70b-instruct"),
    ("nvidia", "meta/llama-3.1-70b-instruct"),
    ("nvidia", "meta/llama-4-maverick-17b-128e-instruct"),
    ("nvidia", "mistralai/mistral-large-3-675b-instruct-2512"),
    ("nvidia", "nvidia/nemotron-3-super-120b-a12b"),
    # NVIDIA reasoning
    ("nvidia", "nvidia/nemotron-3-nano-30b-a3b"),
    # Mistral standard
    ("mistral", "ministral-8b-2512"),
    ("mistral", "mistral-medium-latest"),
    ("mistral", "mistral-large-latest"),
    ("mistral", "devstral-latest"),
    # Mistral reasoning
    ("mistral", "magistral-medium-latest"),
    # Codestral
    ("codestral", "codestral-latest"),
    # Cloudflare
    ("cloudflare", "@cf/deepseek-ai/deepseek-r1-distill-qwen-32b"),
    ("cloudflare", "@cf/ibm-granite/granite-4.0-h-micro"),
    ("cloudflare", "@cf/meta/llama-3.3-70b-instruct-fp8-fast"),
    ("cloudflare", "@cf/meta/llama-4-scout-17b-16e-instruct"),
    ("cloudflare", "@cf/moonshotai/kimi-k2.5"),
    ("cloudflare", "@cf/moonshotai/kimi-k2.6"),
    ("cloudflare", "@cf/openai/gpt-oss-120b"),
    ("cloudflare", "@cf/qwen/qwen3-30b-a3b-fp8"),
    ("cloudflare", "@cf/zai-org/glm-4.7-flash"),
]

# === DISCIPLINE QUESTIONS ===
DISCIPLINES = {
    "coder": {
        "prompt": "Write a Python function `flatten_json(nested_dict)` that takes any nested dict/list structure and returns a flat dict with dot-notation keys (e.g., 'users.0.email'). Handle all edge cases: empty objects, lists of lists, None values. Show just the code.",
        "max_tokens": 500,
    },
    "writer": {
        "prompt": "Write a 3-tweet thread announcing a new AI tool that auto-generates test cases from PR descriptions. Target: senior engineers who are skeptical of AI tools. First tweet hooks the pain point, second explains how it works, third gives a call to action. Keep each tweet under 280 characters.",
        "max_tokens": 500,
    },
    "researcher": {
        "prompt": "I need a quick competitive analysis on AI code review tools. Find and compare: CodeRabbit, Graphite, and Qodo (formerly CodiumAI). For each: pricing model, key differentiator, and one limitation. Output as a markdown table.",
        "max_tokens": 600,
    }
}


def call_model(api_name, model_id, prompt, max_tokens=300, timeout=45):
    """Make an API call and return the response text."""
    api = KEYS[api_name]
    headers = api["headers"]
    
    data = json.dumps({
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
    })
    
    cmd = ["curl", "-s", "-w", "\n%{http_code}", api["url"],
           "-H", f"Authorization: Bearer {api['key']}",
           "-H", "Content-Type: application/json",
           "-d", data, "--max-time", str(timeout)]
    
    for k, v in headers.items():
        cmd.extend(["-H", f"{k}: {v}"])
    
    start = time.time()
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=timeout+5).decode()
        latency = round(time.time() - start, 2)
        
        parts = output.rsplit('\n', 1)
        http_code = parts[-1].strip()
        body = parts[0] if len(parts) > 1 else ""
        
        if http_code != "200":
            return {"success": False, "error": f"HTTP {http_code}", "latency": latency}
        
        resp = json.loads(body)
        msg = resp.get("choices", [{}])[0].get("message", {})
        
        # Try content field first, then reasoning field (reasoning models)
        content = msg.get("content") or msg.get("reasoning") or ""
        
        return {"success": True, "content": content.strip(), "latency": latency,
                "usage": resp.get("usage", {})}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "timeout", "latency": round(time.time() - start, 2)}
    except Exception as e:
        return {"success": False, "error": str(e)[:80], "latency": round(time.time() - start, 2)}


def evaluate_coder(content):
    """Check if the output contains valid Python with flatten_json function."""
    if not content:
        return {"pass": False, "reason": "empty"}
    
    has_function = "def flatten_json" in content
    has_return = "return" in content
    has_dict = "dict" in content or "isinstance" in content
    
    # Try to extract and compile the function
    # Find the function definition
    code_blocks = re.findall(r'```python\n(.*?)\n```', content, re.DOTALL)
    if not code_blocks:
        code_blocks = re.findall(r'```\n(.*?)\n```', content, re.DOTALL)
    if not code_blocks:
        # No code blocks - try to find function definition directly
        func_match = re.search(r'(def flatten_json.*?)(?:\n\S|$)', content, re.DOTALL)
        if func_match:
            code_blocks = [func_match.group(1)]
    
    compiled = False
    if code_blocks:
        try:
            compile(code_blocks[0], '<test>', 'exec')
            compiled = True
        except:
            pass
    
    # If no code blocks, try the whole content
    if not compiled:
        try:
            compile(content, '<test>', 'exec')
            compiled = True
        except:
            pass
    
    return {
        "pass": has_function and has_return and compiled,
        "has_function": has_function,
        "has_return": has_return,
        "has_dict_handling": has_dict,
        "compiled": compiled,
        "code_block_count": len(code_blocks),
    }


def evaluate_writer(content):
    """Evaluate the writer output qualitatively."""
    if not content:
        return {"pass": False, "reason": "empty"}
    
    tweets = content.count('"') // 2  # rough tweet indicator
    has_tweet1 = re.search(r'(?i)(tweet|thread|1[\.:]\s*|first)', content[:200])
    has_tweet2 = re.search(r'(?i)(2[\.:]\s*|second)', content)
    has_tweet3 = re.search(r'(?i)(3[\.:]\s*|third|call.to.action|CTA|try|sign.up)', content)
    has_cta = re.search(r'(?i)(try it|sign up|check it|get started|CTA)', content)
    
    return {
        "pass": bool(has_tweet1 and has_tweet3),
        "structure": bool(has_tweet1 and has_tweet2 and has_tweet3),
        "has_cta": bool(has_cta),
        "length": len(content),
    }


def evaluate_researcher(content):
    """Evaluate the researcher output for structure and coverage."""
    if not content:
        return {"pass": False, "reason": "empty"}
    
    has_coderabbit = re.search(r'(?i)code.?rabbit', content)
    has_graphite = re.search(r'(?i)graphite', content)
    has_qodo = re.search(r'(?i)qodo|codium', content)
    has_table = '|' in content and '---' in content
    has_pricing = re.search(r'(?i)(pricing|price|\$|free|paid|cost)', content)
    
    return {
        "pass": bool(has_coderabbit and has_graphite and has_pricing),
        "has_coderabbit": bool(has_coderabbit),
        "has_graphite": bool(has_graphite),
        "has_qodo": bool(has_qodo),
        "has_table": has_table,
        "has_pricing": bool(has_pricing),
    }


def extract_content_from_response(result):
    """Get clean content from API response, handling reasoning models."""
    if not result.get("success"):
        return ""
    content = result["content"]
    # Remove thinking/reasoning tags
    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
    content = re.sub(r'<thinking>.*?</thinking>', '', content, flags=re.DOTALL)
    return content.strip()


# === MAIN RUNNER ===
_apis_needed = {api for api, _ in MODELS}
_env_map = {
    "openrouter": ["OPENROUTER_API_KEY"],
    "nvidia": ["NVIDIA_API_KEY"],
    "mistral": ["MISTRAL_API_KEY"],
    "codestral": ["CODESTRAL_API_KEY"],
    "cloudflare": ["CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ACCOUNT_ID"],
}
for api_name in _apis_needed:
    for env_name in _env_map.get(api_name, []):
        _require_env(env_name)
    KEYS[api_name]["key"] = _require_env(_env_map[api_name][0])
    if api_name == "cloudflare":
        account = os.environ["CLOUDFLARE_ACCOUNT_ID"].strip()
        KEYS["cloudflare"]["url"] = (
            f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/v1/chat/completions"
        )

results = []
print(f"=== FREE MODEL DISCIPLINE TESTS ===")
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print(f"Models to test: {len(MODELS)}")
print(f"Disciplines: {', '.join(DISCIPLINES.keys())}")
print(f"{'='*60}")

for api_name, model_id in MODELS:
    print(f"\n--- {api_name}/{model_id} ---")
    model_result = {"api": api_name, "model": model_id, "disciplines": {}}
    
    for disc_name, disc in DISCIPLINES.items():
        print(f"  [{disc_name}] ", end="", flush=True)
        resp = call_model(api_name, model_id, disc["prompt"], disc["max_tokens"])
        
        content = extract_content_from_response(resp)
        
        if not resp.get("success"):
            print(f"❌ {resp.get('error', 'unknown')} ({resp.get('latency', 0)}s)")
            model_result["disciplines"][disc_name] = {
                "pass": False, "error": resp.get("error"),
                "latency": resp.get("latency"), "content": "",
            }
        else:
            # Evaluate
            if disc_name == "coder":
                eval_result = evaluate_coder(content)
            elif disc_name == "writer":
                eval_result = evaluate_writer(content)
            elif disc_name == "researcher":
                eval_result = evaluate_researcher(content)
            
            passed = eval_result.get("pass", False)
            symbol = "✅" if passed else "⚠️"
            print(f"{symbol} {resp['latency']}s | {len(content)} chars")
            
            model_result["disciplines"][disc_name] = {
                "pass": passed,
                "latency": resp["latency"],
                "eval": eval_result,
                "content_preview": content[:200],
            }
        
        time.sleep(1.5)  # throttle
    
    results.append(model_result)
    
    # Save incremental
    with open(os.path.join(BASE_DIR, "results", "discipline_results.json"), "w") as f:
        json.dump(results, f, indent=2)

# === SUMMARY ===
print(f"\n{'='*60}")
print(f"SUMMARY: {len(results)} models tested across 3 disciplines")
print(f"{'='*60}")

headers = ["API", "Model", "Coder", "Writer", "Researcher", "Score"]
print(f"{'|':>4} {'API':12s} | {'Model':45s} | {'Coder':6s} | {'Writer':6s} | {'Researcher':9s} | {'Score':6s} |")
print(f"{'|---'*7}")

buckets = {"coder": [], "writer": [], "researcher": [], "generalist": [], "nope": []}

for r in sorted(results, key=lambda x: sum(1 for d in x["disciplines"].values() if d.get("pass")), reverse=True):
    coder_pass = r["disciplines"].get("coder", {}).get("pass", False)
    writer_pass = r["disciplines"].get("writer", {}).get("pass", False)
    researcher_pass = r["disciplines"].get("researcher", {}).get("pass", False)
    score = sum([coder_pass, writer_pass, researcher_pass])
    
    symbol_c = "✅" if coder_pass else "❌"
    symbol_w = "✅" if writer_pass else "❌"
    symbol_r = "✅" if researcher_pass else "❌"
    
    print(f"  {r['api']:12s} | {r['model']:45s} |  {symbol_c}   |  {symbol_w}   |   {symbol_r}     |  {score}/3  |")
    
    # Bucket
    if score >= 2:
        buckets["generalist"].append(r)
    elif coder_pass:
        buckets["coder"].append(r)
    elif writer_pass:
        buckets["writer"].append(r)
    elif researcher_pass:
        buckets["researcher"].append(r)
    else:
        buckets["nope"].append(r)

print(f"\n{'='*60}")
print("BUCKET SUMMARY")
print(f"{'='*60}")
for bucket, models in buckets.items():
    print(f"\n{bucket.upper()} ({len(models)}):")
    for m in models:
        print(f"  - {m['api']}/{m['model']}")

# Save final
final = {"results": results, "buckets": {k: [{"api": m["api"], "model": m["model"]} for m in v] for k, v in buckets.items()}}
with open(os.path.join(BASE_DIR, "results", "final.json"), "w") as f:
    json.dump(final, f, indent=2)

print(f"\n\nResults saved to: {BASE_DIR}/results/")