"""Curated keywords bank and extraction utilities."""

import re
from typing import Any

ROLE_KEYWORDS: dict[str, list[str]] = {
    "senior-full-stack-engineer": [
        "full stack",
        "senior software engineer",
        "react",
        "node.js",
        "typescript",
        "javascript",
        "api design",
        "rest",
        "graphql",
        "postgresql",
        "aws",
        "ci/cd",
        "docker",
        "system design",
        "microservices",
        "testing",
    ],
    "agentic-ai-systems-engineer": [
        "agentic",
        "ai agents",
        "llm",
        "mcp",
        "model context protocol",
        "tool calling",
        "function calling",
        "rag",
        "orchestration",
        "langchain",
        "openai",
        "anthropic",
        "claude",
        "prompt engineering",
        "evals",
        "multi-agent",
        "python",
        "typescript",
        "vector database",
    ],
    "ai-automation-consultant": [
        "ai automation",
        "workflow automation",
        "consultant",
        "llm integration",
        "business process",
        "roi",
        "n8n",
        "zapier",
        "make",
        "custom gpt",
        "chatbot",
        "api integration",
        "discovery",
        "solution architecture",
        "ai strategy",
        "client delivery",
    ],
    "react-python-php-engineer": [
        "react",
        "python",
        "php",
        "laravel",
        "wordpress",
        "django",
        "fastapi",
        "javascript",
        "typescript",
        "mysql",
        "rest api",
        "frontend",
        "backend",
        "full stack",
        "legacy modernization",
    ],
}

GENERIC_STRONG_SIGNALS = [
    "led",
    "built",
    "shipped",
    "scaled",
    "reduced",
    "increased",
    "launched",
    "migrated",
    "designed",
    "architected",
    "automated",
    "mentored",
]

WEAK_PHRASES = [
    "responsible for",
    "worked on",
    "helped with",
    "assisted",
    "duties included",
    "team player",
    "hard-working",
    "passionate",
    "results-driven",
    "synergy",
    "go-getter",
    "detail-oriented",
    "motivated professional",
]

STOP_WORDS = {
    "the",
    "and",
    "for",
    "with",
    "you",
    "our",
    "are",
    "will",
    "have",
    "this",
    "that",
    "your",
    "from",
    "not",
    "all",
    "can",
    "who",
    "what",
    "when",
    "how",
    "job",
    "role",
    "team",
    "work",
    "years",
    "experience",
    "skills",
    "ability",
    "strong",
    "including",
    "required",
    "preferred",
    "must",
    "plus",
    "etc",
    "about",
    "more",
    "than",
    "such",
    "other",
    "into",
    "across",
    "within",
}


def text_contains_keyword(text: str, keyword: str) -> bool:
    return keyword.lower() in text.lower()


def keyword_coverage(text: str, keywords: list[str]) -> dict[str, Any]:
    present = [k for k in keywords if text_contains_keyword(text, k)]
    missing = [k for k in keywords if not text_contains_keyword(text, k)]
    score = int((len(present) / len(keywords)) * 100) if keywords else 0
    return {"present": present, "missing": missing, "score": score}


def extract_keywords_from_jd(jd: str, limit: int = 40) -> list[str]:
    words = re.findall(r"[a-z0-9+#./-]+", jd.lower())
    filtered = [
        w for w in words if len(w) > 2 and w not in STOP_WORDS and not w.isdigit()
    ]
    counts: dict[str, int] = {}
    for w in filtered:
        counts[w] = counts.get(w, 0) + 1
    for i in range(len(filtered) - 1):
        bg = f"{filtered[i]} {filtered[i + 1]}"
        counts[bg] = counts.get(bg, 0) + 1
    candidates = [k for k, v in counts.items() if v >= 2]
    if len(candidates) < 5:
        candidates = [k for k, v in counts.items() if v >= 1]
    sorted_kws = sorted(candidates, key=lambda k: counts[k], reverse=True)
    return sorted_kws[:limit]


def optimize_keywords(text: str, target_role: str = "agentic-ai-systems-engineer") -> dict[str, Any]:
    role_kws = ROLE_KEYWORDS.get(target_role, ROLE_KEYWORDS.get("agentic-ai-systems-engineer", []))
    cov = keyword_coverage(text, role_kws)
    return {
        "density": float(cov["score"]),
        "present": cov["present"],
        "missing": cov["missing"],
    }

