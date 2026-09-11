from typing import Optional, Type, TypeVar
import httpx
from pydantic import BaseModel

from app.llm.base import BaseLLMProvider
from app.llm.structured_output import StructuredOutputParser
from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import LLMProviderError

T = TypeVar("T", bound=BaseModel)


class LlamaProvider(BaseLLMProvider):
    """
    Local LLM Provider implementing Ollama / OpenAI-compatible Llama API (e.g. llama3, mistral).
    Default endpoint: http://localhost:11434/v1
    """
    def __init__(self, model_name: str = "llama3", base_url: str = "http://localhost:11434/v1"):
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")

    @property
    def provider_name(self) -> str:
        return "llama"

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "stream": False
        }

        url = f"{self.base_url}/chat/completions"
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload)
                
                if response.status_code != 200:
                    raise LLMProviderError(
                        provider="Llama/Ollama",
                        message=f"Local Llama API returned status {response.status_code}: {response.text}"
                    )

                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return content.strip()

        except Exception as e:
            if isinstance(e, LLMProviderError):
                raise e
            logger.error(f"Llama/Ollama connection error to {url}: {str(e)}")
            raise LLMProviderError(
                provider="Llama/Ollama",
                message=f"Failed to connect to local Llama/Ollama instance at {url}. Ensure Ollama is running."
            )

    async def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.1
    ) -> T:
        schema_json = response_schema.model_json_schema()
        json_instruction = (
            f"\n\nIMPORTANT: Return your response strictly as a valid JSON object matching this schema:\n"
            f"```json\n{schema_json}\n```\nDo not include any explanation outside the JSON block."
        )

        full_prompt = prompt + json_instruction
        raw_text = await self.generate_text(
            prompt=full_prompt,
            system_prompt=system_prompt,
            temperature=temperature
        )

        return StructuredOutputParser.parse_json_response(raw_text, response_schema)
