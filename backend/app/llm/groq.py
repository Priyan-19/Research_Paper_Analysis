import asyncio
import random
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
    Cloud LLM Provider implementing Groq API (e.g. llama-3.3-70b-versatile, llama3-70b-8192)
    with exponential backoff, rate-limit retry resilience, and structured output parsing.
    """
    def __init__(
        self,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: str = "https://api.groq.com/openai/v1",
        max_retries: int = 3
    ):
        self.model_name = model_name or settings.GROQ_MODEL
        self._api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries

    @property
    def api_key(self) -> str:
        return self._api_key or settings.GROQ_API_KEY

    @property
    def provider_name(self) -> str:
        return "groq"

    def _ensure_configured(self):
        if not self.api_key or self.api_key.strip() in ("", "your_groq_api_key_here"):
            raise LLMProviderError(
                provider="Groq",
                message="GROQ_API_KEY is not configured in .env file."
            )

    async def _post_with_retry(self, url: str, payload: dict, headers: dict) -> dict:
        """
        Executes HTTP POST request with exponential backoff and jitter for HTTP 429 and 5xx errors.
        """
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(url, json=payload, headers=headers)

                    if response.status_code == 200:
                        return response.json()

                    # Handle Rate Limiting (429) or Transient Server Errors (5xx)
                    if response.status_code in (429, 502, 503, 504) and attempt < self.max_retries:
                        backoff = (2 ** attempt) + random.uniform(0.1, 0.5)
                        logger.warning(
                            f"Groq API returned HTTP {response.status_code}. "
                            f"Applying exponential backoff ({backoff:.2f}s, attempt {attempt + 1}/{self.max_retries})..."
                        )
                        await asyncio.sleep(backoff)
                        continue

                    raise LLMProviderError(
                        provider="Groq",
                        message=f"Groq API returned status {response.status_code}: {response.text}"
                    )
            except httpx.RequestError as req_err:
                if attempt < self.max_retries:
                    backoff = (2 ** attempt) + random.uniform(0.1, 0.5)
                    logger.warning(f"Groq network error: {req_err}. Retrying in {backoff:.2f}s...")
                    await asyncio.sleep(backoff)
                    continue
                raise LLMProviderError(provider="Groq", message=f"Network error after {self.max_retries} retries: {str(req_err)}")

        raise LLMProviderError(provider="Groq", message="Exceeded maximum retries for Groq API request.")

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
            data = await self._post_with_retry(url, payload, headers)
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
            f"\n\nCRITICAL REQUIREMENT: Output valid JSON matching this schema:\n"
            f"{schema_json}\n"
            f"Do not output markdown codeblocks, commentary, or text outside the raw JSON object."
        )

        full_prompt = prompt + json_instruction
        raw_text = await self.generate_text(
            prompt=full_prompt,
            system_prompt=system_prompt,
            temperature=temperature
        )

        return StructuredOutputParser.parse(raw_text, response_schema)
