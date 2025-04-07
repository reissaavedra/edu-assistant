"""
Career agent module for handling career-related queries.
"""

from langchain.prompts import PromptTemplate

from app.agents.base import BaseAgent


class CarrerasAgent(BaseAgent):
    """Agent for handling career-related queries."""

    def __init__(self):
        super().__init__(agent_type="carreras")

        # Set up Langchain components specific to this agent
        carreras_prompt_template = """
        Eres un asistente especializado en rutas profesionales y carreras educativas.
        Tu trabajo es ayudar a los usuarios a encontrar el mejor camino educativo para 
        su desarrollo profesional.
        
        Basándote en la siguiente información de nuestra base de conocimientos:
        {knowledge_base_text}
        
        Contexto de la conversación:
        {context}
        
        Historial de la conversación:
        {conversation_history}
        
        Por favor responde a la siguiente consulta del usuario sobre carreras:
        {user_query}
        
        Cuando sugieras rutas de aprendizaje, prioriza los cursos que ya han sido mencionados en la conversación
        y que aparecen en el contexto. Si el usuario muestra interés en una carrera específica, recomienda una ruta
        basada en los cursos disponibles:
        
        - Data Mining y Análisis de Datos (www.datamining.com) 
        - Gestión de Bases de Datos con SQL (www.sql.com)
        - Power BI para la Gestión de Datos (www.powerbi.com)
        """

        # Create specific prompt template for this agent
        self.prompt = PromptTemplate(
            input_variables=[
                "conversation_history",
                "knowledge_base_text",
                "user_query",
                "context",
            ],
            template=carreras_prompt_template,
        )

        # Create specific runnable chain for this agent using pipe operator
        self.runnable = self.prompt | self.llm

    async def process(self, message: str) -> str:
        """
        Process a career-related query.

        Args:
            message: The user's message

        Returns:
            str: The response to the user
        """
        return await super().process(message)


# Singleton instance
_career_paths_agent = None


def get_career_paths_agent() -> CarrerasAgent:
    """Get the singleton career paths agent instance.

    Returns:
        CarrerasAgent: The career paths agent instance
    """
    global _career_paths_agent
    if _career_paths_agent is None:
        _career_paths_agent = CarrerasAgent()
    return _career_paths_agent
