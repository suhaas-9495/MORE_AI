import tiktoken
from typing import Tuple

# Groq pricing as of 2025 - per 1m tokens
GROQ_PRICING = {
    "llama-3.3-70b-versatile": {"input": 0.59, "output": 0.79},
    "llama3-70b-8192":         {"input": 0.59, "output": 0.79},
    "llama3-8b-8192":          {"input": 0.05, "output": 0.08},
    "mixtral-8x7b-32768":      {"input": 0.24, "output": 0.24},
}


def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    """
    Estimates token count using tiktoken.
    Groq uses same tokenizer as OpenAI for LLaMA — close enough for cost tracking.
    """
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


def estimate_cost(
    input_text: str,
    output_text: str,
    model: str = "llama-3.3-70b-versatile",
) -> Tuple[float, int, int]:
    """
    Returns (cost_usd, tokens_in, tokens_out).
    Logged per request — gives you cost-per-task visibility in Langfuse.
    """
    pricing = GROQ_PRICING.get(model, {"input": 0.59, "output": 0.79})
    tokens_in = count_tokens(input_text)
    tokens_out = count_tokens(output_text)

    cost = (tokens_in * pricing["input"] + tokens_out * pricing["output"]) / 1_000_000
    return round(cost, 8), tokens_in, tokens_out