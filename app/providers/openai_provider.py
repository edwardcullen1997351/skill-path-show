"""
OpenAI LLM Provider.

This module provides integration with OpenAI's GPT models
using the OpenAI API.
"""

import os
import json
from typing import Optional, Dict, Any, List
from app.providers.base import LLMProvider, LLMProviderConfig, LLMResponse


class OpenAIConfig(LLMProviderConfig):
    """Configuration for OpenAI provider."""
    model: str = "gpt-4o-mini"
    api_key: Optional[str] = None
    base_url: Optional[str] = None  # For custom endpoints


class OpenAIProvider(LLMProvider):
    """Provider for OpenAI GPT models."""
    
    def __init__(self, config: Optional[OpenAIConfig] = None):
        """Initialize OpenAI provider."""
        super().__init__(config or OpenAIConfig())
        self._client = None
    
    @property
    def provider_name(self) -> str:
        return "openai"
    
    def is_available(self) -> bool:
        """Check if OpenAI is available."""
        api_key = self._config.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            return False
        
        if self._client is None:
            try:
                from openai import OpenAI
                base_url = self._config.base_url or os.getenv("OPENAI_BASE_URL")
                self._client = OpenAI(
                    api_key=api_key,
                    base_url=base_url if base_url else "https://api.openai.com/v1"
                )
            except ImportError:
                return False
            except Exception:
                return False
        
        return self._client is not None
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Optional[LLMResponse]:
        """Generate response using OpenAI."""
        if not self.is_available():
            return None
        
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self._client.chat.completions.create(
                model=self._config.model,
                messages=messages,
                temperature=temperature or self._config.temperature,
                max_tokens=max_tokens or self._config.max_tokens
            )
            
            return LLMResponse(
                text=response.choices[0].message.content or "",
                raw_response=response.model_dump(),
                provider=self.provider_name,
                model=self._config.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                }
            )
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return None


def get_openai_provider(config: Optional[OpenAIConfig] = None) -> OpenAIProvider:
    """Get OpenAI provider instance."""
    return OpenAIProvider(config)