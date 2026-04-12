"""
Gemini LLM Provider.

This module provides integration with Google Gemini models
using the genai library.
"""

import os
import json
from typing import Optional, Dict, Any, List
from app.providers.base import LLMProvider, LLMProviderConfig, LLMResponse


class GeminiConfig(LLMProviderConfig):
    """Configuration for Gemini provider."""
    model: str = "gemini-1.5-flash"
    api_key: Optional[str] = None


class GeminiProvider(LLMProvider):
    """Provider for Google Gemini models."""
    
    def __init__(self, config: Optional[GeminiConfig] = None):
        """Initialize Gemini provider."""
        super().__init__(config or GeminiConfig())
        self._client = None
    
    @property
    def provider_name(self) -> str:
        return "gemini"
    
    def is_available(self) -> bool:
        """Check if Gemini is available."""
        api_key = self._config.api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return False
        
        if self._client is None:
            try:
                import google.genai as genai
                genai.configure(api_key=api_key)
                self._client = genai
            except ImportError:
                return False
            except Exception:
                return False
        
        return True
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Optional[LLMResponse]:
        """Generate response using Gemini."""
        if not self.is_available():
            return None
        
        try:
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            
            model = self._client.GenerativeModel(self._config.model)
            response = model.generate_content(
                full_prompt,
                generation_config={
                    "temperature": temperature or self._config.temperature,
                    "max_output_tokens": max_tokens or self._config.max_tokens
                }
            )
            
            return LLMResponse(
                text=response.text,
                raw_response=response.model_dump(),
                provider=self.provider_name,
                model=self._config.model
            )
        except Exception as e:
            print(f"Gemini API error: {e}")
            return None


def get_gemini_provider(config: Optional[GeminiConfig] = None) -> GeminiProvider:
    """Get Gemini provider instance."""
    return GeminiProvider(config)