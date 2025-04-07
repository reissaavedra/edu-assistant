"""
Conversation history management for the educational assistant.

This module handles tracking, storing, and retrieving conversation history
between users and the assistant, including metadata like which agent responded.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from langchain.memory import ConversationBufferMemory
from langchain.memory.chat_message_histories import RedisChatMessageHistory
from loguru import logger


@dataclass
class Message:
    """Represents a single message in the conversation history."""

    content: str
    role: str  # "user" or "assistant"
    timestamp: datetime = field(default_factory=datetime.now)
    agent_type: Optional[str] = (
        None  # Which agent generated this message (if assistant)
    )
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional metadata

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation
        """
        return {
            "content": self.content,
            "role": self.role,
            "timestamp": self.timestamp.isoformat(),
            "agent_type": self.agent_type,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create message from dictionary.

        Args:
            data: Dictionary with message data

        Returns:
            Message: Created message
        """
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        return cls(
            content=data["content"],
            role=data["role"],
            timestamp=timestamp or datetime.now(),
            agent_type=data.get("agent_type"),
            metadata=data.get("metadata", {}),
        )


class ConversationHistory:
    """Manages conversation history for a single session."""

    def __init__(self, session_id: Optional[str] = None):
        """Initialize conversation history.

        Args:
            session_id: Optional ID for the session. Generated if not provided.
        """
        self.session_id = session_id or str(uuid4())
        self.messages: List[Message] = []
        self.metadata: Dict[str, Any] = {
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
        }

        # Initialize Langchain memory
        self.memory = ConversationBufferMemory(
            memory_key="conversation_history",
            return_messages=True,
            chat_memory=RedisChatMessageHistory(session_id=self.session_id),
        )

    def add_user_message(
        self, content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """Add a user message to the history.

        Args:
            content: Message content
            metadata: Optional metadata

        Returns:
            Message: The created message
        """
        message = Message(content=content, role="user", metadata=metadata or {})
        self.messages.append(message)
        self.memory.chat_memory.add_user_message(content)
        self._update_last_updated()
        return message

    def add_assistant_message(
        self, content: str, agent_type: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """Add an assistant message to the history.

        Args:
            content: Message content
            agent_type: Type of agent that generated the response
            metadata: Optional metadata

        Returns:
            Message: The created message
        """
        message = Message(
            content=content,
            role="assistant",
            agent_type=agent_type,
            metadata=metadata or {},
        )
        self.messages.append(message)
        self.memory.chat_memory.add_ai_message(content)
        self._update_last_updated()
        return message

    def get_messages(self, last_n: Optional[int] = None) -> List[Message]:
        """Get all or the last N messages.

        Args:
            last_n: Number of most recent messages to retrieve. All if None.

        Returns:
            List[Message]: Requested messages
        """
        if last_n is None:
            return self.messages.copy()

        return self.messages[-last_n:]

    def get_formatted_history(self, last_n: Optional[int] = None) -> str:
        """Get formatted history as a string, suitable for LLM context.

        Args:
            last_n: Number of most recent messages to include. All if None.

        Returns:
            str: Formatted conversation history
        """
        messages = self.get_messages(last_n)
        formatted_messages = []

        for msg in messages:
            if msg.role == "user":
                formatted_messages.append(f"Usuario: {msg.content}")
            else:
                role = (
                    f"Asistente ({msg.agent_type})" if msg.agent_type else "Asistente"
                )
                formatted_messages.append(f"{role}: {msg.content}")

        return "\n".join(formatted_messages)

    def clear(self) -> None:
        """Clear all messages in the history."""
        self.messages = []
        self.memory.clear()
        self._update_last_updated()
        logger.info(f"Cleared conversation history for session {self.session_id}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation history to dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation
        """
        return {
            "session_id": self.session_id,
            "messages": [msg.to_dict() for msg in self.messages],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationHistory":
        """Create conversation history from dictionary.

        Args:
            data: Dictionary with conversation data

        Returns:
            ConversationHistory: Created conversation history
        """
        history = cls(session_id=data.get("session_id"))
        history.metadata = data.get("metadata", history.metadata)

        for msg_data in data.get("messages", []):
            msg = Message.from_dict(msg_data)
            history.messages.append(msg)
            if msg.role == "user":
                history.memory.chat_memory.add_user_message(msg.content)
            else:
                history.memory.chat_memory.add_ai_message(msg.content)

        return history

    def _update_last_updated(self) -> None:
        """Update the last_updated timestamp in metadata."""
        self.metadata["last_updated"] = datetime.now().isoformat()


# Dictionary to store active conversation histories by session ID
_active_histories: Dict[str, ConversationHistory] = {}


def get_conversation_history(session_id: Optional[str] = None) -> ConversationHistory:
    """Get or create a conversation history for the given session ID.

    Args:
        session_id: Session ID to get history for. Generated if None.

    Returns:
        ConversationHistory: The conversation history
    """
    global _active_histories

    if session_id is None:
        # Generate a new session ID and create a new history
        history = ConversationHistory()
        _active_histories[history.session_id] = history
        return history

    # Get or create history for the given session ID
    if session_id not in _active_histories:
        _active_histories[session_id] = ConversationHistory(session_id=session_id)

    return _active_histories[session_id]
