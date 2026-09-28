import re
from typing import Optional
from backend.app.services.context.models import ContextItem


def estimate_tokens(text: Optional[str]) -> int:
    """
    Estimates token count for raw text using a local, deterministic heuristic strategy.
    
    ESTIMATION STRATEGY:
    - Standard English text / Markdown / JSON / Python code averages ~3.8 - 4.2 characters per token.
    - Word counts with punctuation average ~1.3 tokens per word.
    - We combine character length heuristics (len // 4) with word count boundaries:
        `ceil(max(len(text) / 4, len(words) * 1.3))`
    - An empty string yields 0 tokens.
    
    NOTE:
    This token estimator is intentionally approximate and local. It avoids introducing paid
    external tokenizer APIs (such as OpenAI tiktoken or remote tokenizer microservices)
    while maintaining reliable budget boundaries for context window safety.
    """
    if not text:
        return 0
    
    trimmed = text.strip()
    if not trimmed:
        return 0

    char_len = len(trimmed)
    # Split on whitespace to get word count
    words = re.findall(r"\S+", trimmed)
    word_count = len(words)

    # Blend character-based and word-based estimation
    char_estimate = (char_len + 3) // 4
    word_estimate = int(word_count * 1.33) + 1

    return max(char_estimate, word_estimate, 1)


def estimate_context_item_tokens(item: ContextItem) -> int:
    """
    Estimates token count for a complete ContextItem including its content,
    structural title delimiter overhead, and metadata attributes.
    """
    content_tokens = estimate_tokens(item.content)
    title_tokens = estimate_tokens(item.title)
    
    # Metadata overhead if present
    meta_tokens = 0
    if item.metadata:
        meta_str = " ".join(f"{k}:{v}" for k, v in item.metadata.items())
        meta_tokens = estimate_tokens(meta_str)

    # 4-token structural wrapper overhead per context item (header, delimiter lines, source label)
    structural_overhead = 4

    return content_tokens + title_tokens + meta_tokens + structural_overhead
