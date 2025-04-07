"""
Helper utilities for the educational assistant.

This module provides general utility functions for formatting,
text processing, and other helper functionalities.
"""

import json
import re
import time
from typing import Any, Dict, List, Optional


def sanitize_text(text: str) -> str:
    """Clean and normalize text for consistent processing.

    Args:
        text: Text to sanitize

    Returns:
        str: Sanitized text
    """
    if not text:
        return ""

    # Convert to string if not already
    text = str(text)

    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Other normalizations as needed
    # text = text.lower()  # Uncomment if case-insensitive processing is needed

    return text


def format_agent_response(agent_type: str, response: str) -> str:
    """Format the agent response based on agent type.

    Args:
        agent_type: Type of agent (e.g., 'cursos', 'carreras', 'ventas')
        response: The raw response text

    Returns:
        str: Formatted response
    """
    response = response.strip()

    # Add different formatting based on agent type if needed
    if agent_type == "ventas":
        # Maybe add a CTA for sales agent
        response += (
            "\n\n¿Te gustaría recibir más información sobre nuestros precios y ofertas?"
        )
    elif agent_type == "cursos":
        # Maybe add a note about courses
        response += (
            "\n\n¿Hay algún aspecto específico del curso que te interese conocer?"
        )
    elif agent_type == "carreras":
        # Maybe add a note about career paths
        response += "\n\n¿Quieres conocer más sobre las oportunidades laborales de esta carrera?"

    return response


def calculate_elapsed_time(start_time: float) -> float:
    """Calculate elapsed time since start.

    Args:
        start_time: Start time from time.time()

    Returns:
        float: Elapsed time in seconds
    """
    return round(time.time() - start_time, 3)


def extract_json_from_response(response: str) -> Optional[Dict[str, Any]]:
    """Extract JSON object from a string, even if it's mixed with other text.

    Args:
        response: String potentially containing JSON

    Returns:
        Optional[Dict]: Extracted JSON as a dictionary, or None if not found
    """
    # Find JSON-like structures between curly braces
    json_matches = re.findall(r"\{.*?\}", response, re.DOTALL)

    if not json_matches:
        return None

    # Try to parse each match as JSON
    for match in json_matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue

    return None


def chunk_text(text: str, chunk_size: int = 1500, overlap: int = 100) -> List[str]:
    """Split text into chunks for processing by LLMs with token limits.

    Args:
        text: Text to chunk
        chunk_size: Maximum characters per chunk
        overlap: Character overlap between chunks

    Returns:
        List[str]: List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        # Find the end position for this chunk
        end = min(start + chunk_size, len(text))

        # If we're not at the end of the text, try to find a good break point
        if end < len(text):
            # Try to break at a sentence end
            sentence_break = text.rfind(". ", start, end)
            if sentence_break > start + chunk_size // 2:
                end = sentence_break + 1  # Include the period
            else:
                # Otherwise break at a space
                space_break = text.rfind(" ", start, end)
                if space_break > start + chunk_size // 2:
                    end = space_break

        # Add the chunk
        chunks.append(text[start:end])

        # Move the start position, accounting for overlap
        start = max(start, end - overlap)

        # If we can't make progress, force a break
        if start >= end:
            start = end

    return chunks
