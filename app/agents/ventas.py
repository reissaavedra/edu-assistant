"""
Sales agent module for handling sales-related queries.
"""

from langchain.prompts import PromptTemplate

from app.agents.base import BaseAgent


class VentasAgent(BaseAgent):
    """Agent for handling sales-related queries."""

    def __init__(self):
        super().__init__(agent_type="ventas")

        # Set up Langchain components specific to this agent
        ventas_prompt_template = """
        Eres un asistente especializado en ventas y matrículas de cursos.
        Basándote en la siguiente información de nuestra base de conocimientos:
        
        {knowledge_base_text}
        
        Contexto de la conversación:
        {context}
        
        Historial de la conversación:
        {conversation_history}
        
        Por favor responde a la siguiente consulta del usuario sobre precios, 
        inscripciones o pagos:
        {user_query}

        Si el usuario quiere comprar un curso pero no especifica cuál, debes usar el curso actual en discusión
        que aparece en el contexto. Si no hay un curso actual, entonces pregúntale cuál quiere comprar.
        
        Si el curso es "Data Mining y Análisis de Datos", el link es www.datamining.com y cuesta 1800 soles.
        Si el curso es "Gestión de Bases de Datos con SQL", el link es www.sql.com y cuesta 1100 soles.
        Si el curso es "Power BI para la Gestión de Datos (Grupo 1)", el link es www.powerbi.com y cuesta 1800 soles.
        """

        # Create specific prompt template for this agent
        self.prompt = PromptTemplate(
            input_variables=[
                "conversation_history",
                "knowledge_base_text",
                "user_query",
                "context",
            ],
            template=ventas_prompt_template,
        )

        # Create specific runnable chain for this agent using pipe operator
        self.runnable = self.prompt | self.llm

    async def process(self, message: str) -> str:
        """
        Process a sales-related query.

        Args:
            message: The user's message

        Returns:
            str: The response to the user
        """
        return await super().process(message)


# Singleton instance
_sales_agent = None


def get_sales_agent() -> VentasAgent:
    """Get the singleton sales agent instance.

    Returns:
        VentasAgent: The sales agent instance
    """
    global _sales_agent
    if _sales_agent is None:
        _sales_agent = VentasAgent()
    return _sales_agent
