from typing import Optional, Type, TypeVar
from pydantic import BaseModel

from app.llm.base import BaseLLMProvider
from app.llm.structured_output import StructuredOutputParser
from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import LLMProviderError

T = TypeVar("T", bound=BaseModel)


class GeminiProvider(BaseLLMProvider):
    """
    Cloud LLM Provider implementing Google Gemini API (gemini-1.5-flash).
    """
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        self.model_name = model_name

    @property
    def provider_name(self) -> str:
        return "gemini"

    def _ensure_configured(self):
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY.strip() == "your_gemini_api_key_here":
            raise LLMProviderError(
                provider="Gemini",
                message="GEMINI_API_KEY is not configured in .env file."
            )

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2
    ) -> str:
        self._ensure_configured()
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)

            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_prompt if system_prompt else None
            )

            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(temperature=temperature)
            )

            if response and response.text:
                return response.text.strip()
            
            raise LLMProviderError(provider="Gemini", message="Gemini returned an empty text response.")

        except Exception as e:
            if isinstance(e, LLMProviderError):
                raise e
            logger.error(f"Gemini API generate_text error: {str(e)}")
            raise LLMProviderError(provider="Gemini", message=str(e))

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
            f"\n\nIMPORTANT: Return your response strictly as a JSON object matching this schema:\n"
            f"```json\n{schema_json}\n```\nDo not include any explanation outside the JSON block."
        )

        full_prompt = prompt + json_instruction
        raw_text = await self.generate_text(
            prompt=full_prompt,
            system_prompt=system_prompt,
            temperature=temperature
        )

        return StructuredOutputParser.parse_json_response(raw_text, response_schema)
