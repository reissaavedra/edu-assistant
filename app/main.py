"""
Main module for the educational assistant.

This is the entry point for the application, connecting all the components
and providing the core functionality.
"""

import asyncio
import uuid
from typing import Dict

from loguru import logger

from app.agents.carreras import CarrerasAgent
from app.agents.cursos import CursosAgent
from app.agents.ventas import VentasAgent
from app.router.router import AgentType, get_router


class Assistant:
    """Main assistant class that orchestrates the components."""

    def __init__(self):
        # Create agents first
        self.agents = {
            AgentType.CURSOS: CursosAgent(),
            AgentType.CARRERAS: CarrerasAgent(),
            AgentType.VENTAS: VentasAgent(),
        }
        # Initialize router with agents
        self.router = get_router(agents=self.agents)
        self.session_id = str(uuid.uuid4())
        logger.info(f"Assistant initialized with session ID: {self.session_id}")

    async def process_message(self, message: str) -> Dict[str, str]:
        try:
            logger.info(f"Processing message: {message[:20]}...")

            # Route message
            agent_type, scores = await self.router.route(message)
            logger.info(f"Routing to agent: {agent_type.value}")
            logger.info(f"Routing scores: {scores}")

            # Get appropriate agent
            agent = self.agents[agent_type]

            # Process with agent
            response = await agent.process(message)
            logger.info(f"Raw response from agent: {response}")

            # Handle different response types
            if isinstance(response, str):
                text = response
            elif isinstance(response, dict) and "text" in response:
                text = response["text"]
            else:
                logger.error(f"Unexpected response format: {response}")
                text = "Lo siento, hubo un error al procesar tu mensaje."

            # Build response dictionary
            response_dict = {"text": str(text), "agent_type": str(agent_type.value)}
            logger.info(f"Structured response: {response_dict}")
            return response_dict

        except Exception as e:
            logger.error(f"Error in process_message: {str(e)}", exc_info=True)
            return {
                "text": f"Lo siento, hubo un error al procesar tu mensaje. Error: {str(e)}",
                "agent_type": "cursos",
            }

    def clear_history(self):
        for agent in self.agents.values():
            agent.clear_history()


def get_assistant() -> Assistant:
    """Get a new assistant instance."""
    return Assistant()


# For direct CLI usage
async def main_loop():
    """Run the assistant in a command-line interface loop."""
    print("=== Asistente Educativo ===")
    print("Escribe 'salir' para terminar, 'reiniciar' para limpiar el historial.")

    # Create assistant
    assistant = get_assistant()

    while True:
        # Get user input
        user_input = input("\nTú: ")

        if user_input.lower() == "salir":
            print("¡Hasta luego!")
            break

        if user_input.lower() == "reiniciar":
            assistant.clear_history()
            print("Historial de conversación borrado.")
            continue

        # Process message
        response = await assistant.process_message(user_input)

        # Print response
        print(f"\nAsistente ({response['agent_type']}): {response['text']}")


if __name__ == "__main__":
    # Run the CLI loop
    asyncio.run(main_loop())
