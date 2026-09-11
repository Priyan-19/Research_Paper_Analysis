from abc import ABC, abstractmethod
from typing import Optional, Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseLLMProvider(ABC):
    """
    Abstract Base Class defining standard interface for all LLM providers (Gemini, Llama/Ollama, OpenAI, etc.).
    """
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Returns human-readable name of the LLM provider."""
        pass

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2
    ) -> str:
        """Generates natural language text response for a given prompt."""
        pass

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2
    ) -> str:
        """Alias for generate_text."""
        return await self.generate_text(prompt=prompt, system_prompt=system_prompt, temperature=temperature)

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.1
    ) -> T:
        """Generates structured output matching a Pydantic BaseModel schema."""
        pass
