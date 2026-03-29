"""
NLP utilities for text processing and keyword extraction.

This module provides simple NLP functions for processing curriculum text,
extracting keywords, and preparing text for skill mapping.
"""

import re
from typing import List, Set, Dict


def tokenize(text: str) -> List[str]:
    """
    Tokenize text into words.
    
    Args:
        text: Input text to tokenize
        
    Returns:
        List of tokens (lowercased, alpha-numeric)
    """
    # Convert to lowercase
    text = text.lower()
    
    # Remove special characters and split
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    
    # Split into words and filter empty strings
    tokens = [word.strip() for word in text.split() if word.strip()]
    
    return tokens


def extract_keywords(text: str, min_length: int = 3) -> Set[str]:
    """
    Extract keywords from text using simple frequency-based approach.
    
    Args:
        text: Input text to extract keywords from
        min_length: Minimum word length to consider
        
    Returns:
        Set of extracted keywords
    """
    tokens = tokenize(text)
    
    # Filter by minimum length
    keywords = {token for token in tokens if len(token) >= min_length}
    
    # Remove common stop words
    stop_words = {
        'the', 'and', 'for', 'with', 'from', 'this', 'that', 'are',
        'was', 'were', 'been', 'have', 'has', 'had', 'will', 'would',
        'could', 'should', 'might', 'may', 'can', 'must', 'shall',
        'course', 'class', 'subject', 'module', 'unit', '学习', '课程'
    }
    
    keywords = keywords - stop_words
    
    return keywords


def extract_phrases(text: str) -> List[str]:
    """
    Extract meaningful phrases from text.
    
    Looks for common patterns like:
    - "X with Y"
    - "X and Y"
    - "Introduction to X"
    
    Args:
        text: Input text
        
    Returns:
        List of extracted phrases
    """
    text = text.lower()
    phrases = []
    
    # Pattern: "with"
    pattern1 = re.findall(r'([a-z\s]+)\s+with\s+([a-z\s]+)', text)
    for p in pattern1:
        phrases.append(f"{p[0].strip()} {p[1].strip()}")
    
    # Pattern: "Introduction to X"
    pattern2 = re.findall(r'introduction to ([a-z\s]+)', text)
    for p in pattern2:
        phrases.append(p.strip())
    
    # Pattern: "Fundamentals of X"
    pattern3 = re.findall(r'fundamentals of ([a-z\s]+)', text)
    for p in pattern3:
        phrases.append(p.strip())
    
    # Pattern: "Basics of X"
    pattern4 = re.findall(r'basics of ([a-z\s]+)', text)
    for p in pattern4:
        phrases.append(p.strip())
    
    return phrases


def clean_text(text: str) -> str:
    """
    Clean and normalize text.
    
    Args:
        text: Input text
        
    Returns:
        Cleaned text
    """
    # Convert to lowercase
    text = text.lower()
    
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters (keep alphanumeric and spaces)
    text = re.sub(r'[^a-z0-9\s]', '', text)
    
    return text.strip()


def get_ngrams(text: str, n: int = 2) -> List[str]:
    """
    Get n-grams from text.
    
    Args:
        text: Input text
        n: Size of n-grams (2 for bigrams, 3 for trigrams)
        
    Returns:
        List of n-grams
    """
    tokens = tokenize(text)
    
    if len(tokens) < n:
        return []
    
    ngrams = []
    for i in range(len(tokens) - n + 1):
        ngram = ' '.join(tokens[i:i+n])
        ngrams.append(ngram)
    
    return ngrams


def detect_level(text: str) -> str:
    """
    Detect the difficulty level of a subject/course from text.
    
    Args:
        text: Subject or course description
        
    Returns:
        Level: 'beginner', 'intermediate', or 'advanced'
    """
    text = text.lower()
    
    advanced_keywords = ['advanced', 'expert', 'senior', 'master', 'deep', 'research']
    intermediate_keywords = ['intermediate', 'middle', 'moderate']
    beginner_keywords = ['beginner', 'intro', 'introduction', 'basic', 'fundamentals', 'foundational']
    
    if any(kw in text for kw in advanced_keywords):
        return 'advanced'
    elif any(kw in text for kw in intermediate_keywords):
        return 'intermediate'
    elif any(kw in text for kw in beginner_keywords):
        return 'beginner'
    
    # Default based on common patterns
    if '101' in text or '102' in text:
        return 'beginner'
    elif '201' in text or '202' in text or '301' in text:
        return 'intermediate'
    elif '401' in text or '402' in text or '4xx' in text:
        return 'advanced'
    
    return 'intermediate'


def extract_subject_codes(text: str) -> List[str]:
    """
    Extract subject codes from text.
    
    Common patterns: CS101, DA301, ML401, etc.
    
    Args:
        text: Input text containing subject codes
        
    Returns:
        List of extracted subject codes
    """
    # Pattern: 2-4 uppercase letters followed by 3 digits
    pattern = r'\b[A-Z]{2,4}\d{3}\b'
    codes = re.findall(pattern, text.upper())
    
    return list(set(codes))  # Remove duplicates