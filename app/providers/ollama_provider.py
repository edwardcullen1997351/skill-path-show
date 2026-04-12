"""
Ollama LLM Provider.

This module provides integration with Ollama for running
local LLM models.
"""

import os
import json
import requests
from typing import Optional, Dict, Any, List
from app.providers.base import LLMProvider, LLMProviderConfig, LLMResponse


class OllamaConfig(LLMProviderConfig):
    """Configuration for Ollama provider."""
    model: str = "llama3"
    base_url: str = "http://localhost:11434"


class OllamaProvider(LLMProvider):
    """Provider for Ollama local models."""
    
    def __init__(self, config: Optional[OllamaConfig] = None):
        """Initialize Ollama provider."""
        super().__init__(config or OllamaConfig())
        self._base_url = self._config.base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    @property
    def provider_name(self) -> str:
        return "ollama"
    
    def is_available(self) -> bool:
        """Check if Ollama is available."""
        try:
            response = requests.get(f"{self._base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def _get_model_list(self) -> List[str]:
        """Get list of available models."""
        try:
            response = requests.get(f"{self._base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            pass
        return []
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Optional[LLMResponse]:
        """Generate response using Ollama."""
        if not self.is_available():
            return None
        
        try:
            payload = {
                "model": self._config.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature or self._config.temperature,
                    "num_predict": max_tokens or self._config.max_tokens
                }
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            response = requests.post(
                f"{self._base_url}/api/generate",
                json=payload,
                timeout=120
            )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            return LLMResponse(
                text=data.get("response", ""),
                raw_response=data,
                provider=self.provider_name,
                model=self._config.model
            )
        except Exception as e:
            print(f"Ollama API error: {e}")
            return None


def get_ollama_provider(config: Optional[OllamaConfig] = None) -> OllamaProvider:
    """Get Ollama provider instance."""
    return OllamaProvider(config)