"""
Courses agent for the educational assistant.

This agent specializes in providing information about courses, their content,
structure, and other course-related details.
"""

from langchain.prompts import PromptTemplate

from app.agents.base import BaseAgent


class CursosAgent(BaseAgent):
    """Agent for handling course-related queries."""

    def __init__(self):
        """Initialize the courses agent."""
        super().__init__(agent_type="cursos")

        # Set up Langchain components specific to this agent
        cursos_prompt_template = """
        Eres un asistente especializado en cursos y programas educativos.
        Basándote en la siguiente información de nuestra base de conocimientos:
        
        {knowledge_base_text}
        
        Contexto de la conversación:
        {context}
        
        Historial de la conversación:
        {conversation_history}
        
        Por favor responde a la siguiente consulta del usuario:
        {user_query}
        
        Si el usuario hace preguntas sobre un curso sin especificar cuál, debes usar el curso actual 
        que figura en el contexto de la conversación. Si no hay un curso actual, pregúntale a cuál se refiere.
        
        Los cursos disponibles son:
        - Data Mining y Análisis de Datos
        - Gestión de Bases de Datos con SQL
        - Power BI para la Gestión de Datos (Grupo 1)
        """

        # Create specific prompt template for this agent
        self.prompt = PromptTemplate(
            input_variables=[
                "conversation_history",
                "knowledge_base_text",
                "user_query",
                "context",
            ],
            template=cursos_prompt_template,
        )

        # Create specific runnable chain for this agent using pipe operator
        self.runnable = self.prompt | self.llm

    async def process(self, message: str) -> str:
        """
        Process a course-related query.

        Args:
            message: The user's message

        Returns:
            str: The response to the user
        """
        return await super().process(message)


# Singleton instance
_courses_agent = None


def get_courses_agent() -> CursosAgent:
    """Get the singleton courses agent instance.

    Returns:
        CursosAgent: The courses agent instance
    """
    global _courses_agent
    if _courses_agent is None:
        _courses_agent = CursosAgent()
    return _courses_agent
