from .base import AIProvider
from .openai_provider import OpenAIProvider
from .gemini_provider import GeminiProvider
from .ollama_provider import OllamaProvider

PROVIDERS = {
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
    "ollama": OllamaProvider,
}

def get_provider(name: str, **kwargs) -> AIProvider:
    if name not in PROVIDERS:
        raise ValueError(f"Provider '{name}' not found. Available: {list(PROVIDERS.keys())}")
    return PROVIDERS[name](**kwargs)
