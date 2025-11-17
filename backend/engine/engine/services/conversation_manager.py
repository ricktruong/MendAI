"""
Conversation Manager Service
Manages conversation history and context for chat sessions
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


class ConversationManager:
    """
    Manages conversation history with session-based storage
    
    Features:
    - Session-based conversation history
    - Automatic cleanup of old sessions
    - Context window management (token limit handling)
    - Conversation summarization for long histories
    """
    
    def __init__(self, max_history_per_session: int = 50, session_ttl_hours: int = 24):
        """
        Initialize conversation manager
        
        Args:
            max_history_per_session: Maximum number of messages to keep per session
            session_ttl_hours: Hours before a session expires
        """
        self.conversations: Dict[str, Dict] = defaultdict(dict)
        self.max_history = max_history_per_session
        self.session_ttl = timedelta(hours=session_ttl_hours)
        logger.info(f"ConversationManager initialized with max_history={max_history_per_session}, ttl={session_ttl_hours}h")
    
    def get_conversation_history(self, session_id: str) -> List[Dict[str, str]]:
        """
        Get conversation history for a session
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            List of message dicts with 'role' and 'content'
        """
        if session_id not in self.conversations:
            logger.info(f"No conversation history found for session {session_id}")
            return []
        
        session = self.conversations[session_id]
        
        # Check if session has expired
        if self._is_session_expired(session):
            logger.info(f"Session {session_id} has expired, clearing history")
            del self.conversations[session_id]
            return []
        
        messages = session.get("messages", [])
        logger.info(f"Retrieved {len(messages)} messages for session {session_id}")
        return messages
    
    def add_message(self, session_id: str, role: str, content: str, patient_id: Optional[str] = None):
        """
        Add a message to conversation history
        
        Args:
            session_id: Unique session identifier
            role: Message role ('user' or 'assistant')
            content: Message content
            patient_id: Optional patient ID for context
        """
        if session_id not in self.conversations:
            self.conversations[session_id] = {
                "messages": [],
                "created_at": datetime.now(),
                "last_updated": datetime.now(),
                "patient_id": patient_id
            }
            logger.info(f"Created new conversation session: {session_id}")
        
        session = self.conversations[session_id]
        session["last_updated"] = datetime.now()
        
        # Update patient_id if provided
        if patient_id and not session.get("patient_id"):
            session["patient_id"] = patient_id
        
        # Add message
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        session["messages"].append(message)
        
        # Trim history if too long
        if len(session["messages"]) > self.max_history:
            # Keep system messages and recent history
            trimmed = self._trim_history(session["messages"])
            session["messages"] = trimmed
            logger.info(f"Trimmed conversation history for session {session_id} to {len(trimmed)} messages")
        
        logger.info(f"Added {role} message to session {session_id} (total: {len(session['messages'])} messages)")
    
    def get_context_for_llm(self, session_id: str, max_tokens: int = 3000) -> List[Dict[str, str]]:
        """
        Get conversation history optimized for LLM context window
        
        This method intelligently manages the conversation history to fit within
        token limits while preserving important context.
        
        Args:
            session_id: Unique session identifier
            max_tokens: Maximum tokens to use (rough estimate: 1 token ≈ 4 chars)
            
        Returns:
            List of messages optimized for LLM context
        """
        history = self.get_conversation_history(session_id)
        
        if not history:
            return []
        
        # Rough token estimation (1 token ≈ 4 characters)
        max_chars = max_tokens * 4
        
        # Always include recent messages
        recent_messages = history[-10:]  # Last 10 messages
        
        # Calculate total characters
        total_chars = sum(len(msg["content"]) for msg in recent_messages)
        
        if total_chars <= max_chars:
            logger.info(f"Returning {len(recent_messages)} recent messages for session {session_id}")
            return recent_messages
        
        # If too long, summarize older messages and keep recent ones
        summary = self._summarize_old_messages(history[:-10])
        if summary:
            summarized_messages = [
                {
                    "role": "system",
                    "content": f"[Previous conversation summary: {summary}]"
                }
            ] + history[-5:]  # Keep only last 5 messages
            logger.info(f"Returning summarized context for session {session_id}")
            return summarized_messages
        
        # Fallback: just return most recent messages
        logger.info(f"Returning last 5 messages only for session {session_id}")
        return history[-5:]
    
    def clear_session(self, session_id: str):
        """Clear conversation history for a session"""
        if session_id in self.conversations:
            del self.conversations[session_id]
            logger.info(f"Cleared conversation history for session {session_id}")
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions to free memory"""
        expired_sessions = []
        
        for session_id, session in self.conversations.items():
            if self._is_session_expired(session):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.conversations[session_id]
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    def get_session_stats(self) -> Dict:
        """Get statistics about active sessions"""
        return {
            "total_sessions": len(self.conversations),
            "total_messages": sum(len(s.get("messages", [])) for s in self.conversations.values()),
            "avg_messages_per_session": sum(len(s.get("messages", [])) for s in self.conversations.values()) / max(len(self.conversations), 1)
        }
    
    def _is_session_expired(self, session: Dict) -> bool:
        """Check if a session has expired"""
        last_updated = session.get("last_updated")
        if not last_updated:
            return True
        return datetime.now() - last_updated > self.session_ttl
    
    def _trim_history(self, messages: List[Dict]) -> List[Dict]:
        """
        Trim history while preserving important context
        
        Strategy:
        - Keep first 2 messages (usually greeting/context)
        - Keep last max_history-2 messages (recent conversation)
        """
        if len(messages) <= self.max_history:
            return messages
        
        # Keep first 2 and last (max_history - 2) messages
        return messages[:2] + messages[-(self.max_history - 2):]
    
    def _summarize_old_messages(self, messages: List[Dict]) -> str:
        """
        Create a brief summary of old messages
        
        This is a simple implementation. For production, you might want to:
        - Use LLM to generate better summaries
        - Extract key medical findings
        - Preserve critical information
        """
        if not messages:
            return ""
        
        # Simple summary: count messages and extract key topics
        user_messages = [m for m in messages if m.get("role") == "user"]
        
        if len(user_messages) <= 2:
            # Just return the content if only a few messages
            return " | ".join(m.get("content", "")[:100] for m in user_messages)
        
        return f"User asked {len(user_messages)} questions about patient data and medical analysis."


# Global instance
_conversation_manager: Optional[ConversationManager] = None


def get_conversation_manager() -> ConversationManager:
    """Get or create the global conversation manager instance"""
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = ConversationManager()
    return _conversation_manager
