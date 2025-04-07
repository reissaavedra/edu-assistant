"""
Base agent class for the educational assistant.

This module provides a base class that all specialized agents should inherit from,
containing common functionality and abstract methods that must be implemented.
"""

import os
import time
from abc import ABC
from typing import Any, Dict, Optional

import nest_asyncio
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_google_genai import ChatGoogleGenerativeAI
from loguru import logger

from app.config import settings
from app.utils.data_loader import get_knowledge_base
from app.utils.helpers import calculate_elapsed_time

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Set this environment variable to prevent gRPC asyncio issues
# This forces gRPC to use the threading executor instead of asyncio for DNS resolution
os.environ["GRPC_ENABLE_FORK_SUPPORT"] = "false"
os.environ["GRPC_DNS_RESOLVER"] = "native"


class BaseAgent(ABC):
    """Base class for all agents in the educational assistant."""

    # Base prompt template that all agents will use
    BASE_PROMPT_TEMPLATE = """
Historial de conversación:
{conversation_history}

Usa la siguiente información para responder la consulta:
{knowledge_base_text}

Contexto adicional:
{context}

Consulta: {user_query}
Respuesta:"""

    def __init__(self, agent_type: str):
        """Initialize the agent."""
        self.agent_type = agent_type
        self.conversation_history = []
        self.knowledge_base = get_knowledge_base()
        # Track current context like the current course being discussed
        self.current_course = None
        self.mentioned_courses = []

        # Configure Langchain with Google API
        try:
            # Use async_api=False to avoid gRPC asyncio issues
            self.llm = ChatGoogleGenerativeAI(
                model=settings.gemini_model,
                temperature=settings.gemini_temperature,
                google_api_key=settings.gemini_api_key,
                async_api=False,  # Use synchronous API to avoid asyncio issues
            )

            self.prompt = PromptTemplate(
                input_variables=[
                    "conversation_history",
                    "knowledge_base_text",
                    "user_query",
                    "context",
                ],
                template=self.BASE_PROMPT_TEMPLATE,
            )

            # Create a runnable chain using the modern approach (pipe operator)
            self.runnable = self.prompt | self.llm

            # Create a wrapper for process function to be used with Langchain router
            # Use synchronous process method instead of async to avoid event loop issues
            self.runnable_agent = RunnableLambda(
                lambda x: self.process_sync(x["message"])
            )

            logger.info(
                f"Successfully initialized {settings.gemini_model} for {agent_type} agent using Langchain"
            )
        except Exception as e:
            logger.error(f"Error configuring Langchain with Gemini API: {e}")
            raise RuntimeError(
                "Failed to initialize Langchain with Gemini API. Please check your API key."
            )

    def get_history(self) -> str:
        """Get formatted conversation history."""
        return "\n".join(self.conversation_history)

    def get_knowledge_base(self) -> str:
        """Get formatted knowledge base content."""
        try:
            # Get courses from the DataFrame
            df = self.knowledge_base.get_courses()
            if df is None or df.empty:
                return "No hay información de cursos disponible."

            formatted_courses = []
            for _, row in df.iterrows():
                course_info = (
                    f"Curso: {row['Nombre del curso']}\n"
                    f"Formato: {row['Formato']}\n"
                    f"Costo: {row['Costo (soles)']} soles\n"
                    f"Objetivo: {row['Objetivo']}\n"
                    f"Link: {row['Link para inscripcion']}\n"
                )
                formatted_courses.append(course_info)

            return "\n\n".join(formatted_courses)
        except Exception as e:
            logger.error(f"Error formatting knowledge base: {e}")
            return "Error al acceder a la base de conocimientos."

    def update_context(self, message: str) -> None:
        """
        Update conversation context like currently discussed course.
        This will extract course names from a message and from knowledge base.
        """
        try:
            # Get all course names from the knowledge base
            df = self.knowledge_base.get_courses()
            courses = df["Nombre del curso"].tolist()

            # Check if any course is mentioned in the message
            for course in courses:
                if course.lower() in message.lower():
                    if course not in self.mentioned_courses:
                        self.mentioned_courses.append(course)
                    self.current_course = course
                    logger.info(f"Current course set to: {self.current_course}")
                    return

            # Check for partial matches or key phrases
            course_keywords = {
                "Data Mining": "Data Mining y Análisis de Datos",
                "SQL": "Gestión de Bases de Datos con SQL",
                "Power BI": "Power BI para la Gestión de Datos (Grupo 1)",
            }

            for keyword, full_name in course_keywords.items():
                if keyword.lower() in message.lower():
                    if full_name not in self.mentioned_courses:
                        self.mentioned_courses.append(full_name)
                    self.current_course = full_name
                    logger.info(
                        f"Current course set to: {self.current_course} (matched by keyword)"
                    )
                    return

            # Check for generic references to previous course
            reference_keywords = [
                "curso",
                "comprar",
                "pagar",
                "inscribirme",
                "matricularme",
                "ese",
                "este curso",
            ]

            if (
                any(keyword in message.lower() for keyword in reference_keywords)
                and self.current_course
            ):
                # If the user is referring to a course generically, keep the current course
                logger.info(
                    f"Maintaining current course context: {self.current_course}"
                )
                return

        except Exception as e:
            logger.error(f"Error updating context: {e}")

    def update_context_from_history(self):
        """Update context by processing the conversation history"""
        # First process the last 4 messages if they exist
        for message in self.conversation_history[-4:]:
            if message:
                self.update_context(message)

    def get_context(self) -> str:
        """Get the current conversation context."""
        context = []
        if self.current_course:
            context.append(f"Curso actual en discusión: {self.current_course}")
        if self.mentioned_courses:
            context.append(
                f"Cursos mencionados previamente: {', '.join(self.mentioned_courses)}"
            )

        if not context:
            return "No hay contexto adicional."

        return "\n".join(context)

    def process_sync(self, message: str) -> str:
        """
        Process a message synchronously.
        This avoids issues with event loops by using nest_asyncio.
        """
        try:
            # Update context from history
            self.update_context_from_history()

            # Update context based on current message
            self.update_context(message)

            # Instead of using the async API, just use the sync API directly
            history = self.get_history()
            knowledge_base = self.get_knowledge_base()
            context = self.get_context()

            # Use synchronous invoke instead of async
            response = self.runnable.invoke(
                {
                    "conversation_history": history,
                    "knowledge_base_text": knowledge_base,
                    "user_query": message,
                    "context": context,
                }
            )

            # Extract text from response
            if hasattr(response, "content"):
                text_response = response.content
            else:
                text_response = str(response)

            # Update conversation history
            self.conversation_history.append(f"User: {message}")
            self.conversation_history.append(f"Assistant: {text_response}")

            return text_response
        except Exception as e:
            logger.error(f"Error in synchronous processing: {str(e)}", exc_info=True)
            return "Lo siento, hubo un error al procesar tu mensaje. Por favor, intenta de nuevo."

    def process_message(self, message: str) -> str:
        """
        Process a message synchronously.
        Use direct synchronous processing to avoid event loop issues.
        """
        try:
            return self.process_sync(message)
        except Exception as e:
            logger.error(f"Error in process_message: {str(e)}")
            return "Lo siento, hubo un error al procesar tu mensaje. Por favor, intenta de nuevo."

    async def process(self, message: str) -> str:
        """Process a message and return a response."""
        try:
            # For async contexts, just delegate to the synchronous method
            # to avoid event loop issues
            return self.process_sync(message)
        except Exception as e:
            logger.error(f"Error in {self.agent_type} agent: {str(e)}", exc_info=True)
            return "Lo siento, hubo un error al procesar tu mensaje. Por favor, intenta de nuevo."

    def clear_history(self):
        """Clear the conversation history."""
        self.conversation_history = []
        self.current_course = None
        self.mentioned_courses = []

    async def process_query(
        self, user_query: str, conversation_history: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process user query and generate a response."""
        start_time = time.time()
        logger.info(
            f"Processing query with {self.agent_type} agent: {user_query[:50]}..."
        )

        try:
            # Update context based on message
            self.update_context(user_query)

            # Use synchronous version to avoid event loop issues
            history = (
                conversation_history if conversation_history else self.get_history()
            )
            knowledge_base = self.get_knowledge_base()
            context = self.get_context()

            # Use synchronous invoke
            response = self.runnable.invoke(
                {
                    "conversation_history": history,
                    "knowledge_base_text": knowledge_base,
                    "user_query": user_query,
                    "context": context,
                }
            )

            # Extract text from response
            if hasattr(response, "content"):
                text_response = response.content
            else:
                text_response = str(response)

            # Calculate processing time
            elapsed_time = calculate_elapsed_time(start_time)
            logger.info(f"Processing completed in {elapsed_time:.2f} seconds")

            # Update conversation history
            self.conversation_history.append(f"User: {user_query}")
            self.conversation_history.append(f"Assistant: {text_response}")

            return {
                "text": text_response,
                "agent_type": self.agent_type,
                "processing_time": elapsed_time,
                "model_name": settings.gemini_model,
                "tokens_used": None,
            }

        except Exception as e:
            logger.error(f"Error in {self.agent_type} agent: {e}")
            logger.exception("Full error traceback:")
            elapsed_time = calculate_elapsed_time(start_time)

            return {
                "text": "Lo siento, no pude procesar tu consulta en este momento. Por favor, intenta de nuevo.",
                "agent_type": self.agent_type,
                "processing_time": elapsed_time,
                "error": str(e),
            }
