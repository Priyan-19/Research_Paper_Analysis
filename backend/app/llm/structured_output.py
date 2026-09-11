import json
import re
from typing import Type, TypeVar
from pydantic import BaseModel, ValidationError

from app.core.logging import logger
from app.core.exceptions import LLMProviderError

T = TypeVar("T", bound=BaseModel)


class StructuredOutputParser:
    """
    Utility parser converting raw LLM JSON strings into validated Pydantic models.
    Handles code block stripping (```json ... ```) and syntax cleanup.
    """
    @staticmethod
    def parse_json_response(raw_text: str, response_schema: Type[T]) -> T:
        if not raw_text or not raw_text.strip():
            raise LLMProviderError(provider="Parser", message="Received empty response from LLM.")

        # 1. Clean markdown JSON blocks
        cleaned = raw_text.strip()
        if "```json" in cleaned:
            cleaned = re.search(r'```json\s*(.*?)\s*```', cleaned, re.DOTALL)
            cleaned = cleaned.group(1) if cleaned else raw_text
        elif "```" in cleaned:
            cleaned = re.search(r'```\s*(.*?)\s*```', cleaned, re.DOTALL)
            cleaned = cleaned.group(1) if cleaned else raw_text

        cleaned = cleaned.strip()

        # 2. Parse JSON
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM response: {cleaned[:200]}...")
            raise LLMProviderError(
                provider="JSONParser",
                message=f"LLM did not output valid JSON syntax: {str(e)}"
            )

        # 3. Validate with Pydantic Schema
        try:
            return response_schema.model_validate(data)
        except ValidationError as val_err:
            logger.error(f"Pydantic schema validation failed for {response_schema.__name__}: {val_err.json()}")
            raise LLMProviderError(
                provider="SchemaValidator",
                message=f"LLM output failed Pydantic validation for {response_schema.__name__}."
            )
