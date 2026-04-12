"""
LLM Provider Factory and Registry.

This module provides a factory for creating LLM providers and
a registry for managing available providers.
"""

import os
from typing import Dict, Optional, Any
from app.providers.base import LLMProvider
from app.providers.gemini_provider import GeminiProvider, GeminiConfig, get_gemini_provider
from app.providers.openai_provider import OpenAIProvider, OpenAIConfig, get_openai_provider
from app.providers.anthropic_provider import AnthropicProvider, AnthropicConfig, get_anthropic_provider
from app.providers.ollama_provider import OllamaProvider, OllamaConfig, get_ollama_provider


class LLMProviderRegistry:
    """Registry for managing LLM providers."""
    
    def __init__(self):
        """Initialize the registry."""
        self._providers: Dict[str, LLMProvider] = {}
        self._default_provider: Optional[str] = None
    
    def register(self, name: str, provider: LLMProvider) -> None:
        """
        Register a provider.
        
        Args:
            name: Provider name
            provider: Provider instance
        """
        self._providers[name] = provider
        if self._default_provider is None:
            self._default_provider = name
    
    def get(self, name: str) -> Optional[LLMProvider]:
        """
        Get a provider by name.
        
        Args:
            name: Provider name
            
        Returns:
            Provider or None if not found
        """
        return self._providers.get(name)
    
    def get_default(self) -> Optional[LLMProvider]:
        """
        Get the default provider.
        
        Returns:
            Default provider or None
        """
        if self._default_provider:
            return self._providers.get(self._default_provider)
        return None
    
    def list_providers(self) -> Dict[str, Dict[str, Any]]:
        """
        List all registered providers with their status.
        
        Returns:
            Dict of provider info
        """
        result = {}
        for name, provider in self._providers.items():
            result[name] = {
                "name": name,
                "available": provider.is_available(),
                "model": provider.model
            }
        return result
    
    def set_default(self, name: str) -> bool:
        """
        Set the default provider.
        
        Args:
            name: Provider name
            
        Returns:
            True if successful, False otherwise
        """
        if name in self._providers:
            self._default_provider = name
            return True
        return False


def create_provider(
    provider_name: str,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None
) -> Optional[LLMProvider]:
    """
    Create an LLM provider by name.
    
    Args:
        provider_name: Name of the provider (gemini, openai, anthropic, ollama)
        model: Optional model override
        api_key: Optional API key override
        base_url: Optional base URL override
        
    Returns:
        Provider instance or None if invalid name
    """
    provider_name = provider_name.lower()
    
    if provider_name == "gemini":
        config = GeminiConfig(model=model or "gemini-1.5-flash", api_key=api_key)
        return get_gemini_provider(config)
    
    elif provider_name == "openai":
        config = OpenAIConfig(model=model or "gpt-4o-mini", api_key=api_key, base_url=base_url)
        return get_openai_provider(config)
    
    elif provider_name == "anthropic":
        config = AnthropicConfig(model=model or "claude-3-haiku-20240307", api_key=api_key)
        return get_anthropic_provider(config)
    
    elif provider_name == "ollama":
        config = OllamaConfig(
            model=model or os.getenv("OLLAMA_MODEL", "llama3"),
            base_url=base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        )
        return get_ollama_provider(config)
    
    return None


def get_provider_registry() -> LLMProviderRegistry:
    """
    Get the global provider registry.
    
    Returns:
        LLMProviderRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = LLMProviderRegistry()
        
        gemini = get_gemini_provider()
        _registry.register("gemini", gemini)
        
        openai = get_openai_provider()
        _registry.register("openai", openai)
        
        anthropic = get_anthropic_provider()
        _registry.register("anthropic", anthropic)
        
        ollama = get_ollama_provider()
        _registry.register("ollama", ollama)
        
        _registry.set_default("gemini")
    
    return _registry


def get_provider(name: Optional[str] = None) -> Optional[LLMProvider]:
    """
    Get a provider by name or the default.
    
    Args:
        name: Optional provider name
        
    Returns:
        Provider or None
    """
    registry = get_provider_registry()
    
    if name:
        return registry.get(name.lower())
    
    return registry.get_default()


def is_provider_available(name: str) -> bool:
    """
    Check if a provider is available.
    
    Args:
        name: Provider name
        
    Returns:
        True if available
    """
    provider = get_provider(name)
    return provider.is_available() if provider else False


def list_available_providers() -> Dict[str, bool]:
    """
    List all providers and their availability.
    
    Returns:
        Dict of provider name to availability
    """
    registry = get_provider_registry()
    return {
        name: provider.is_available()
        for name, provider in registry._providers.items()
    }


_registry: Optional[LLMProviderRegistry] = None