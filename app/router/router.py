"""
Router module for the educational assistant.

This module is responsible for routing user messages to the appropriate agent
based on the content and intent of the message.
"""

from enum import Enum
from typing import Any, Dict, Tuple

from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableBranch
from loguru import logger


class AgentType(str, Enum):
    """Types of agents available in the system."""

    CURSOS = "cursos"
    CARRERAS = "carreras"
    VENTAS = "ventas"


class Router:
    """Router for directing messages to the appropriate agent."""

    def __init__(self, agents: Dict[AgentType, Any]):
        """Initialize the router with keyword patterns for each agent."""
        self.agents = agents
        self.patterns = {
            AgentType.VENTAS: {
                "comprar": 15,
                "pagar": 15,
                "costo": 15,
                "precio": 15,
                "inscribir": 15,
                "inscripción": 15,
                "matricular": 15,
                "matrícula": 15,
                "adquirir": 15,
                "invertir": 15,
                "oferta": 10,
                "descuento": 10,
                "promoción": 10,
            },
            AgentType.CURSOS: {
                "curso": 5,
                "cursos": 5,
                "contenido": 5,
                "tema": 5,
                "material": 5,
                "clase": 5,
                "profesor": 5,
                "enseñar": 5,
                "aprender": 5,
                "formación": 5,
            },
            AgentType.CARRERAS: {
                "carrera": 10,
                "profesión": 10,
                "profesional": 10,
                "camino": 10,
                "ruta": 10,
                "convertir": 10,
                "convertirme": 10,
                "ser": 8,
                "trabajo": 8,
                "laboral": 8,
                "empleo": 8,
                "futuro": 8,
                "mercado": 8,
                "perfil": 8,
                "engineer": 10,
                "developer": 10,
                "scientist": 10,
                "analyst": 10,
            },
        }
        self.last_agent = None

        # Create prompt templates for each agent
        self.prompts = {
            agent_type: PromptTemplate(
                template=self._get_agent_prompt(agent_type), input_variables=["message"]
            )
            for agent_type in agents.keys()
        }

        # Use RunnableBranch with the runnable_agent attribute from each agent
        self.router = RunnableBranch(
            (
                lambda x: x["route"] == AgentType.CURSOS.value,
                self.agents[AgentType.CURSOS].runnable_agent,
            ),
            (
                lambda x: x["route"] == AgentType.CARRERAS.value,
                self.agents[AgentType.CARRERAS].runnable_agent,
            ),
            (
                lambda x: x["route"] == AgentType.VENTAS.value,
                self.agents[AgentType.VENTAS].runnable_agent,
            ),
            # Default case
            self.agents[AgentType.CURSOS].runnable_agent,
        )

    def _get_agent_prompt(self, agent_type: AgentType) -> str:
        """Get the prompt template for a specific agent type."""
        return f"""Eres un asistente especializado en {agent_type.value}.
Basándote en el siguiente mensaje del usuario, responde de manera apropiada:

{{message}}"""

    def calculate_scores(self, message: str) -> Dict[AgentType, int]:
        """Calculate routing scores for each agent type."""
        message = message.lower()
        scores = {agent_type: 0 for agent_type in AgentType}

        # Calculate base scores from keywords
        for agent_type, patterns in self.patterns.items():
            for keyword, weight in patterns.items():
                if keyword in message:
                    scores[agent_type] += weight
                    logger.debug(
                        f"Matched '{keyword}' for {agent_type}: +{weight} points"
                    )

        # Si hay intención de compra, dar prioridad al agente de ventas
        if scores[AgentType.VENTAS] > 0:
            scores[AgentType.VENTAS] += 10  # Bonus por intención de compra
            logger.debug("Purchase intent detected: +10 bonus points for ventas")

        # Context handling for short responses
        if len(message.split()) <= 2:  # Short response
            if self.last_agent:
                scores[self.last_agent] += 15
                logger.debug(
                    f"Short response context bonus for {self.last_agent}: +15 points"
                )

        # Special cases for better routing
        if any(keyword in message for keyword in ["si", "sí", "yes"]):
            if self.last_agent == AgentType.VENTAS:
                scores[AgentType.VENTAS] += (
                    25  # Mayor bonus para respuestas afirmativas en contexto de ventas
                )
                logger.debug(
                    "Affirmative response in sales context: +25 points for ventas"
                )
            elif self.last_agent:
                scores[self.last_agent] += 15
                logger.debug(
                    f"Affirmative response bonus for {self.last_agent}: +15 points"
                )

        # Si menciona un curso específico en contexto de compra, priorizar ventas
        if "curso" in message and scores[AgentType.VENTAS] > 0:
            scores[AgentType.VENTAS] += 15
            logger.debug("Course mention in purchase context: +15 points for ventas")

        logger.info(f"Final scores: {scores}")
        return scores

    async def route(self, message: str) -> Tuple[AgentType, Dict[AgentType, int]]:
        """Route the message to the appropriate agent."""
        scores = self.calculate_scores(message)
        selected_agent = max(scores.items(), key=lambda x: x[1])[0]

        # Update last agent only if we have a clear winner
        max_score = max(scores.values())
        if max_score > 0:
            self.last_agent = selected_agent

        # We only need to determine the best agent, actual processing
        # will be done directly by the Assistant
        logger.info(f"Selected agent: {selected_agent} with scores: {scores}")
        return selected_agent, scores


# Singleton instance
_router = None


def get_router(agents: Dict[AgentType, Any] = None) -> Router:
    """Get the singleton router instance."""
    global _router
    if _router is None:
        if agents is None:
            raise ValueError("Agents must be provided when initializing router")
        _router = Router(agents)
    return _router
