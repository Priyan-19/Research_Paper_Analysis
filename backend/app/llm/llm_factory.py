from typing import Optional
from app.llm.base import BaseLLMProvider
from app.llm.gemini import GeminiProvider
from app.llm.llama import LlamaProvider
from app.llm.groq import GroqProvider
from app.core.config import settings
from app.core.logging import logger

_llm_provider_instance: Optional[BaseLLMProvider] = None


def get_llm_provider(provider_type: Optional[str] = None) -> BaseLLMProvider:
    """
    Factory function returning configured LLM provider instance (Groq, Gemini, or Llama).
    """
    global _llm_provider_instance
    target_provider = (provider_type or settings.LLM_PROVIDER).lower()

    if target_provider == "groq":
        if _llm_provider_instance is None or _llm_provider_instance.provider_name != "groq":
            logger.info("Initializing Groq Cloud LLM Provider...")
            _llm_provider_instance = GroqProvider()
        return _llm_provider_instance

    if target_provider == "llama":
        logger.info("Initializing Llama/Ollama Local LLM Provider...")
        return LlamaProvider()
    
    # Default to Gemini
    if _llm_provider_instance is None or _llm_provider_instance.provider_name != "gemini":
        logger.info("Initializing Google Gemini Cloud LLM Provider...")
        _llm_provider_instance = GeminiProvider()

    return _llm_provider_instance
