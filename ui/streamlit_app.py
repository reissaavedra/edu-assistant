"""
Streamlit UI for the educational assistant.

This module provides a web interface for the educational assistant using Streamlit.
"""

import os
from typing import Dict

import nest_asyncio
import streamlit as st
from loguru import logger

from app.main import get_assistant

# Force gRPC to use native DNS resolver instead of asyncio to avoid event loop issues
os.environ["GRPC_ENABLE_FORK_SUPPORT"] = "false"
os.environ["GRPC_DNS_RESOLVER"] = "native"

# Apply nest_asyncio to allow nested event loops in Streamlit threads
nest_asyncio.apply()

# Configure logger
logger.add("app.log", rotation="500 MB")

# Page config with proper caching settings
st.set_page_config(
    page_title="Asistente Educativo",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state with proper error handling
try:
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "processing" not in st.session_state:
        st.session_state.processing = False
    if "assistant" not in st.session_state:
        logger.info("Initializing new assistant")
        st.session_state.assistant = get_assistant()
except Exception as e:
    logger.error(f"Error initializing session state: {e}")
    st.error("Error initializing application. Please refresh the page.")
    st.stop()

# UI Layout
try:
    st.title("🎓 EDU-ASSISTANT")

    # Display chat history
    def display_message(msg: Dict):
        try:
            with st.chat_message(msg["role"]):
                if msg["role"] == "user":
                    st.write(f"👤 {msg['content']}")
                else:
                    agent_emoji = {
                        "cursos": "📚",
                        "carreras": "🎯",
                        "ventas": "💰",
                    }.get(msg.get("agent_type", ""), "🤖")
                    st.markdown(f"{agent_emoji} {msg['content']}")
        except Exception as e:
            logger.error(f"Error displaying message: {e}")
            st.error("Error displaying message")

    # Display existing chat history
    for message in st.session_state.chat_history:
        display_message(message)

    # Input area with error handling
    try:
        user_input = st.chat_input("Escribe tu mensaje:")
    except Exception as e:
        logger.error(f"Error creating chat input: {e}")
        user_input = None

    # Reset button in sidebar
    with st.sidebar:
        if st.button("Reiniciar conversación"):
            try:
                st.session_state.chat_history = []
                st.session_state.assistant.clear_history()
                st.rerun()
            except Exception as e:
                logger.error(f"Error resetting conversation: {e}")
                st.error("Error resetting conversation")

        # Descripción simple del sistema
        st.markdown("---")
        st.markdown("### 🎓 EDU-ASSISTANT")
        st.markdown("""
        Este asistente utiliza un sistema multi-agente para responder a tus consultas sobre:
        
        - 📚 **Información de cursos** disponibles
        - 🎯 **Orientación profesional** y carreras
        - 💰 **Procesos de inscripción** y precios
        
        El sistema selecciona automáticamente el agente más adecuado según tu consulta, manteniendo el contexto de la conversación.
        """)

    # Process user input with proper error handling
    if user_input and not st.session_state.processing:
        try:
            # Set processing flag
            st.session_state.processing = True

            # Add user message to history
            user_message = {"role": "user", "content": user_input}
            st.session_state.chat_history.append(user_message)
            display_message(user_message)

            # Process message
            with st.spinner("Procesando..."):
                # Use the synchronous processing pathway
                # First, determine which agent to use
                router = st.session_state.assistant.router
                scores = router.calculate_scores(user_input)
                selected_agent = max(scores.items(), key=lambda x: x[1])[0]

                # Update last agent in router
                max_score = max(scores.values())
                if max_score > 0:
                    router.last_agent = selected_agent

                # Get the agent
                agent = st.session_state.assistant.agents[selected_agent]

                # Update context in all agents based on this message to maintain shared context
                for (
                    agent_type,
                    agent_instance,
                ) in st.session_state.assistant.agents.items():
                    agent_instance.update_context(user_input)

                # Use agent's synchronous process_sync method directly
                text_response = agent.process_sync(user_input)

                # Format response dictionary
                response = {
                    "text": text_response,
                    "agent_type": selected_agent.value,
                }

                logger.info(f"Got response: {response}")

                # Create assistant message
                assistant_message = {
                    "role": "assistant",
                    "content": str(response.get("text", "")),
                    "agent_type": str(response.get("agent_type", "cursos")),
                }

                # Add to history and display
                st.session_state.chat_history.append(assistant_message)
                display_message(assistant_message)

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            st.error(f"Error: {str(e)}")
        finally:
            st.session_state.processing = False

except Exception as e:
    logger.error(f"Critical error in Streamlit app: {e}")
    st.error("Critical error. Please refresh the page.")
