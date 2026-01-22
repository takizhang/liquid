"""LLM client wrapper supporting multiple providers."""
import os
import json
import re
from typing import Optional, Type
from pydantic import BaseModel
import httpx

from backend.core import AnalysisResult


class LLMClient:
    """Unified LLM client supporting multiple providers."""

    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or os.getenv("LLM_PROVIDER", "deepseek")
        self._client = None
        self._init_client()

    def _init_client(self):
        """Initialize the appropriate client."""
        if self.provider == "anthropic":
            from anthropic import AsyncAnthropic
            self._client = AsyncAnthropic()
            self.model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
        elif self.provider == "openai":
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI()
            self.model = os.getenv("OPENAI_MODEL", "gpt-4o")
        elif self.provider == "deepseek":
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(
                api_key=os.getenv("DEEPSEEK_API_KEY", ""),
                base_url="https://api.deepseek.com"
            )
            self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        elif self.provider == "ollama":
            self._client = None  # Use httpx directly
            self.model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
            self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}")

    async def analyze(
        self,
        system_prompt: str,
        user_content: str,
        response_model: Type[BaseModel] = AnalysisResult
    ) -> AnalysisResult:
        """Perform analysis with structured output."""
        if self.provider == "anthropic":
            return await self._analyze_anthropic(system_prompt, user_content, response_model)
        elif self.provider == "ollama":
            return await self._analyze_ollama(system_prompt, user_content, response_model)
        else:
            # OpenAI-compatible (OpenAI, DeepSeek, Groq)
            return await self._analyze_openai(system_prompt, user_content, response_model)

    async def _analyze_anthropic(
        self,
        system_prompt: str,
        user_content: str,
        response_model: Type[BaseModel]
    ) -> AnalysisResult:
        """Analyze using Anthropic Claude."""
        response = await self._client.messages.create(
            model=self.model,
            max_tokens=2000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}]
        )

        text = response.content[0].text
        return self._parse_response(text, response_model)

    async def _analyze_openai(
        self,
        system_prompt: str,
        user_content: str,
        response_model: Type[BaseModel]
    ) -> AnalysisResult:
        """Analyze using OpenAI."""
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            max_tokens=2000
        )

        text = response.choices[0].message.content
        return self._parse_response(text, response_model)

    async def _analyze_ollama(
        self,
        system_prompt: str,
        user_content: str,
        response_model: Type[BaseModel]
    ) -> AnalysisResult:
        """Analyze using local Ollama."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    "stream": False
                },
                timeout=120.0
            )
            response.raise_for_status()
            data = response.json()

        text = data.get("message", {}).get("content", "")
        return self._parse_response(text, response_model)

    def _parse_response(self, text: str, response_model: Type[BaseModel]) -> AnalysisResult:
        """Parse LLM response into structured format."""
        # Try to extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                data = json.loads(json_match.group())
                return response_model(**data)
            except (json.JSONDecodeError, ValueError):
                pass

        # Fallback: create result from text
        return AnalysisResult(
            summary=text[:500] if len(text) > 500 else text,
            signals=[],
            risk_level="medium",
            recommendations=["请查看详细分析"],
            confidence=0.5,
            reasoning=text
        )

    async def chat(self, messages: list[dict], system: Optional[str] = None) -> str:
        """Simple chat completion."""
        if self.provider == "anthropic":
            response = await self._client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=system or "You are a helpful assistant.",
                messages=messages
            )
            return response.content[0].text
        elif self.provider == "ollama":
            msgs = []
            if system:
                msgs.append({"role": "system", "content": system})
            msgs.extend(messages)
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_url}/api/chat",
                    json={"model": self.model, "messages": msgs, "stream": False},
                    timeout=120.0
                )
                response.raise_for_status()
                return response.json().get("message", {}).get("content", "")
        else:
            # OpenAI-compatible
            msgs = []
            if system:
                msgs.append({"role": "system", "content": system})
            msgs.extend(messages)
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=msgs,
                max_tokens=2000
            )
            return response.choices[0].message.content
