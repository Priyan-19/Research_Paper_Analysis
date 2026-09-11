from typing import Optional, Type, TypeVar
import httpx
from pydantic import BaseModel

from app.llm.base import BaseLLMProvider
from app.llm.structured_output import StructuredOutputParser
from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import LLMProviderError

T = TypeVar("T", bound=BaseModel)


class GroqProvider(BaseLLMProvider):
    """
    Cloud LLM Provider implementing Groq API (e.g. llama-3.3-70b-versatile, llama3-70b-8192).
    """
    def __init__(
        self,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: str = "https://api.groq.com/openai/v1"
    ):
        self.model_name = model_name or settings.GROQ_MODEL
        self.api_key = api_key or settings.GROQ_API_KEY
        self.base_url = base_url.rstrip("/")

    @property
    def provider_name(self) -> str:
        return "groq"

    def _ensure_configured(self):
        if not self.api_key or self.api_key.strip() in ("", "your_groq_api_key_here"):
            raise LLMProviderError(
                provider="Groq",
                message="GROQ_API_KEY is not configured in .env file."
            )

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2
    ) -> str:
        self._ensure_configured()

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

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        url = f"{self.base_url}/chat/completions"

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload, headers=headers)

                if response.status_code != 200:
                    raise LLMProviderError(
                        provider="Groq",
                        message=f"Groq API returned status {response.status_code}: {response.text}"
                    )

                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return content.strip()

        except Exception as e:
            if isinstance(e, LLMProviderError):
                raise e
            logger.error(f"Groq API request error to {url}: {str(e)}")
            raise LLMProviderError(provider="Groq", message=str(e))

    async def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.1
    ) -> T:
        self._ensure_configured()

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
