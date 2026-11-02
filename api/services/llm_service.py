
"""
LLM Service — Gemini API wrapper for all AI interactions.
"""

import json
import logging

from google import genai
from google.genai import types

from api.core.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GEMINI_FAST_MODEL,
)

logger = logging.getLogger(__name__)


class LLMService:
    """Async Gemini API client for LLM interactions."""

    def __init__(self):
        if not GEMINI_API_KEY or GEMINI_API_KEY.startswith("your_"):
            raise ValueError(
                "GEMINI_API_KEY is not configured or is a placeholder. "
                "Please add a valid GEMINI_API_KEY to your .env file. "
                "You can get a free key from Google AI Studio: https://aistudio.google.com/"
            )
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model = GEMINI_MODEL
        self.fast_model = GEMINI_FAST_MODEL

    async def _generate_with_fallback(self, model: str, contents, config: types.GenerateContentConfig):
        """Execute generate_content with automatic fallback if the selected model is unavailable."""
        models_to_try = [model]
        for fallback in [self.fast_model, "gemini-flash-latest", "gemini-3.5-flash-lite"]:
            if fallback and fallback not in models_to_try:
                models_to_try.append(fallback)

        last_error = None
        for attempt_model in models_to_try:
            try:
                response = await self.client.aio.models.generate_content(
                    model=attempt_model,
                    contents=contents,
                    config=config,
                )
                return response
            except Exception as e:
                last_error = e
                err_str = str(e)
                if any(code in err_str for code in ["503", "404", "UNAVAILABLE", "NOT_FOUND"]):
                    logger.warning(
                        f"Model {attempt_model} unavailable ({err_str[:80]}...). Trying fallback model..."
                    )
                    continue
                # For auth or client validation errors, raise immediately
                logger.error(f"Gemini API call failed for {attempt_model}: {e}")
                raise

        logger.error(f"All Gemini models failed. Last error: {last_error}")
        raise last_error

    async def call(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        use_fast_model: bool = False,
    ) -> str:

        model = self.fast_model if use_fast_model else self.model

        try:
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=max_tokens,
                temperature=temperature,
            )
            response = await self._generate_with_fallback(
                model=model,
                contents=user_message,
                config=config,
            )

            return response.text or ""

        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise

    async def call_with_history(
        self,
        system_prompt: str,
        messages: list[dict],
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:

        try:
            history = []

            for message in messages:
                role = message.get("role", "user")
                role = "model" if role == "assistant" else role

                history.append({
                    "role": role,
                    "parts": [{"text": message.get("content", "")}],
                })

            response = await self._generate_with_fallback(
                model=self.model,
                contents=history,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    max_output_tokens=max_tokens,
                    temperature=temperature,
                ),
            )

            return response.text or ""

        except Exception as e:
            logger.error(f"Gemini API history call failed: {e}")
            raise

    async def call_with_tools(
        self,
        system_prompt: str,
        user_message: str,
        tools: list[dict],
        max_tokens: int = 2048,
        temperature: float = 0.3,
    ) -> dict:

        try:
            function_declarations = []

            for tool in tools:
                if tool.get("type") != "function":
                    continue

                function = tool.get("function", {})

                function_declarations.append(
                    types.FunctionDeclaration(
                        name=function["name"],
                        description=function.get("description", ""),
                        parameters_json_schema=function.get(
                            "parameters",
                            {"type": "object", "properties": {}},
                        ),
                    )
                )

            gemini_tools = (
                [types.Tool(function_declarations=function_declarations)]
                if function_declarations
                else None
            )

            response = await self._generate_with_fallback(
                model=self.model,
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    max_output_tokens=max_tokens,
                    temperature=temperature,
                    tools=gemini_tools,
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(
                        disable=True
                    ),
                ),
            )

            content = ""
            tool_calls = []

            if response.candidates:
                candidate = response.candidates[0]

                if candidate.content and candidate.content.parts:
                    for part in candidate.content.parts:
                        if part.text:
                            content += part.text

                        if part.function_call:
                            function_call = part.function_call

                            tool_calls.append({
                                "id": function_call.id or function_call.name,
                                "function_name": function_call.name,
                                "arguments": json.dumps(
                                    dict(function_call.args or {})
                                ),
                            })

            return {
                "content": content or None,
                "tool_calls": tool_calls,
            }

        except Exception as e:
            logger.error(f"Gemini API tool call failed: {e}")
            raise

    async def classify(
        self,
        text: str,
        categories: list[str],
    ) -> str:

        categories_str = ", ".join(categories)

        prompt = (
            f"Classify the following text into exactly ONE of these categories: "
            f"{categories_str}\n\n"
            f'Text: "{text}"\n\n'
            f"Respond with ONLY the category name, nothing else."
        )

        response = await self.call(
            system_prompt=(
                "You are a precise text classifier. "
                "Respond with only the category name."
            ),
            user_message=prompt,
            max_tokens=50,
            temperature=0.0,
            use_fast_model=True,
        )

        return response.strip()
