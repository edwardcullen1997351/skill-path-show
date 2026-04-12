"""
Anthropic LLM Provider.

This module provides integration with Anthropic's Claude models
using the Anthropic API.
"""

import os
import json
from typing import Optional, Dict, Any, List
from app.providers.base import LLMProvider, LLMProviderConfig, LLMResponse


class AnthropicConfig(LLMProviderConfig):
    """Configuration for Anthropic provider."""
    model: str = "claude-3-haiku-20240307"
    api_key: Optional[str] = None


class AnthropicProvider(LLMProvider):
    """Provider for Anthropic Claude models."""
    
    def __init__(self, config: Optional[AnthropicConfig] = None):
        """Initialize Anthropic provider."""
        super().__init__(config or AnthropicConfig())
        self._client = None
    
    @property
    def provider_name(self) -> str:
        return "anthropic"
    
    def is_available(self) -> bool:
        """Check if Anthropic is available."""
        api_key = self._config.api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return False
        
        if self._client is None:
            try:
                from anthropic import Anthropic
                self._client = Anthropic(api_key=api_key)
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
        """Generate response using Anthropic."""
        if not self.is_available():
            return None
        
        try:
            messages = [{"role": "user", "content": prompt}]
            
            response = self._client.messages.create(
                model=self._config.model,
                system=system_prompt or "",
                messages=messages,
                temperature=temperature or self._config.temperature,
                max_tokens=max_tokens or self._config.max_tokens
            )
            
            text = response.content[0].text if response.content else ""
            
            return LLMResponse(
                text=text,
                raw_response=response.model_dump(),
                provider=self.provider_name,
                model=self._config.model,
                usage={
                    "input_tokens": response.usage.input_tokens if response.usage else 0,
                    "output_tokens": response.usage.output_tokens if response.usage else 0
                }
            )
        except Exception as e:
            print(f"Anthropic API error: {e}")
            return None


def get_anthropic_provider(config: Optional[AnthropicConfig] = None) -> AnthropicProvider:
    """Get Anthropic provider instance."""
    return AnthropicProvider(config)