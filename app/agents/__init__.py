"""
Agents package initialization.
"""

from app.agents.base import BaseAgent
from app.agents.carreras import get_career_paths_agent
from app.agents.cursos import get_courses_agent
from app.agents.ventas import get_sales_agent

__all__ = [
    "BaseAgent",
    "get_career_paths_agent",
    "get_courses_agent",
    "get_sales_agent",
]
