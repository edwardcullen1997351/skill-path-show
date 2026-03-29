"""
Supabase client configuration.

This module provides the Supabase client for database operations.
"""

import os
from typing import Optional
from supabase import create_client, Client


_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """
    Get the Supabase client instance.
    
    Returns:
        Client: The Supabase client
    """
    global _supabase_client
    
    if _supabase_client is None:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_KEY environment variables must be set"
            )
        
        _supabase_client = create_client(supabase_url, supabase_key)
    
    return _supabase_client


def init_supabase(url: str, key: str) -> Client:
    """
    Initialize Supabase client with explicit credentials.
    
    Args:
        url: Supabase project URL
        key: Supabase anon key
        
    Returns:
        Client: The initialized Supabase client
    """
    global _supabase_client
    _supabase_client = create_client(url, key)
    return _supabase_client


# Set credentials from environment or provided values
def configure_supabase() -> None:
    """Configure Supabase client from environment variables."""
    get_supabase_client()
