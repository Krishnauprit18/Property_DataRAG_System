"""
Conversation Memory & Context Manager
Enables multi-turn conversations with memory and context tracking
"""

import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict
import threading
import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConversationMessage:
    """Represents a single message in a conversation"""

    def __init__(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ):
        self.role = role  # 'user' or 'assistant'
        self.content = content
        self.metadata = metadata or {}
        self.timestamp = timestamp or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            'role': self.role,
            'content': self.content,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationMessage':
        """Create message from dictionary"""
        return cls(
            role=data['role'],
            content=data['content'],
            metadata=data.get('metadata', {}),
            timestamp=datetime.fromisoformat(data['timestamp'])
        )


class ConversationSession:
    """Manages a single conversation session with context"""

    def __init__(self, session_id: str, max_history: int = 10):
        self.session_id = session_id
        self.messages: List[ConversationMessage] = []
        self.max_history = max_history
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        self.metadata: Dict[str, Any] = {
            'query_count': 0,
            'total_properties_viewed': 0,
            'filters_used': set(),
            'topics': set(),
            'user_preferences': {}
        }

    def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationMessage:
        """Add a message to the conversation"""
        message = ConversationMessage(role, content, metadata)
        self.messages.append(message)

        # Update session metadata
        if role == 'user':
            self.metadata['query_count'] += 1

        if metadata:
            # Track filters used
            if ('filters' in metadata and metadata['filters'] is not None and 
                metadata['filters']):
                for key in metadata['filters'].keys():
                    self.metadata['filters_used'].add(key)

            # Track properties viewed
            if 'num_results' in metadata:
                self.metadata['total_properties_viewed'] += metadata['num_results']

            # Extract topics (simplified keyword extraction)
            if 'topics' in metadata:
                for topic in metadata['topics']:
                    self.metadata['topics'].add(topic)

        # Trim history if needed
        if len(self.messages) > self.max_history * 2:  # Keep user + assistant pairs
            self.messages = self.messages[-(self.max_history * 2):]

        self.last_accessed = datetime.now()
        return message

    def get_conversation_history(
        self,
        limit: Optional[int] = None,
        include_metadata: bool = False
    ) -> List[Dict[str, Any]]:
        """Get conversation history"""
        messages = self.messages[-limit:] if limit else self.messages

        if include_metadata:
            return [msg.to_dict() for msg in messages]
        else:
            return [
                {'role': msg.role, 'content': msg.content}
                for msg in messages
            ]

    def get_context_summary(self) -> str:
        """Generate a summary of conversation context for LLM"""
        if not self.messages:
            return ""

        summary_parts = []

        # Recent interactions
        recent_messages = self.messages[-6:]  # Last 3 exchanges
        if recent_messages:
            summary_parts.append("=== Recent Conversation ===")
            for msg in recent_messages:
                summary_parts.append(f"{msg.role.upper()}: {msg.content[:200]}")
            summary_parts.append("")

        # User preferences and patterns
        if self.metadata['filters_used']:
            summary_parts.append("=== User Preferences ===")
            summary_parts.append(f"Filters used: {', '.join(self.metadata['filters_used'])}")

        if self.metadata['topics']:
            summary_parts.append(f"Topics of interest: {', '.join(list(self.metadata['topics'])[:5])}")

        return "\n".join(summary_parts)

    def extract_context_from_previous(self) -> Dict[str, Any]:
        """Extract relevant context from previous messages"""
        context = {
            'has_history': len(self.messages) > 0,
            'previous_queries': [],
            'mentioned_filters': {},
            'mentioned_locations': [],
            'mentioned_types': [],
            'price_ranges': []
        }

        for msg in self.messages[-10:]:  # Look at last 10 messages
            if msg.role == 'user':
                content_lower = msg.content.lower()

                # Extract query
                context['previous_queries'].append(msg.content)

                # Extract filters from metadata
                if (msg.metadata and 'filters' in msg.metadata and 
                    msg.metadata['filters'] is not None and msg.metadata['filters']):
                    context['mentioned_filters'].update(msg.metadata['filters'])

                # Extract locations (simple keyword matching)
                common_locations = ['london', 'manchester', 'birmingham', 'leeds', 'liverpool', 'bristol']
                for loc in common_locations:
                    if loc in content_lower:
                        context['mentioned_locations'].append(loc)

                # Extract property types
                property_types = ['apartment', 'house', 'flat', 'studio', 'terraced', 'detached', 'semi-detached']
                for ptype in property_types:
                    if ptype in content_lower:
                        context['mentioned_types'].append(ptype)

        return context

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary"""
        return {
            'session_id': self.session_id,
            'messages': [msg.to_dict() for msg in self.messages],
            'created_at': self.created_at.isoformat(),
            'last_accessed': self.last_accessed.isoformat(),
            'metadata': {
                **self.metadata,
                'filters_used': list(self.metadata['filters_used']),
                'topics': list(self.metadata['topics'])
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationSession':
        """Create session from dictionary"""
        session = cls(data['session_id'])
        session.messages = [
            ConversationMessage.from_dict(msg_data)
            for msg_data in data['messages']
        ]
        session.created_at = datetime.fromisoformat(data['created_at'])
        session.last_accessed = datetime.fromisoformat(data['last_accessed'])

        # Restore metadata
        metadata = data['metadata']
        metadata['filters_used'] = set(metadata.get('filters_used', []))
        metadata['topics'] = set(metadata.get('topics', []))
        session.metadata = metadata

        return session


class ConversationManager:
    """Manages multiple conversation sessions with persistence"""

    def __init__(
        self,
        persist_directory: str = "analytics/conversations",
        session_timeout_minutes: int = 60,
        max_sessions: int = 1000
    ):
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        self.sessions: Dict[str, ConversationSession] = {}
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self.max_sessions = max_sessions
        self.lock = threading.Lock()

        # Load existing sessions
        self._load_sessions()

        logger.info(f"ConversationManager initialized with {len(self.sessions)} active sessions")

    def create_session(self, session_id: Optional[str] = None) -> str:
        """Create a new conversation session"""
        with self.lock:
            if session_id is None:
                session_id = str(uuid.uuid4())

            if session_id not in self.sessions:
                self.sessions[session_id] = ConversationSession(session_id)
                logger.info(f"Created new session: {session_id}")

            return session_id

    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Get an existing session"""
        with self.lock:
            session = self.sessions.get(session_id)

            if session:
                # Check if session expired
                if datetime.now() - session.last_accessed > self.session_timeout:
                    logger.info(f"Session {session_id} expired, creating new one")
                    del self.sessions[session_id]
                    return None

                session.last_accessed = datetime.now()
                return session

            return None

    def get_or_create_session(self, session_id: Optional[str] = None) -> tuple[str, ConversationSession]:
        """Get existing session or create new one"""
        if session_id:
            session = self.get_session(session_id)
            if session:
                return session_id, session

        # Create new session
        new_id = self.create_session(session_id)
        return new_id, self.sessions[new_id]

    def add_message_to_session(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationMessage:
        """Add a message to a session"""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found or expired")

        message = session.add_message(role, content, metadata)

        # Persist session
        self._save_session(session)

        return message

    def get_conversation_history(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get conversation history for a session"""
        session = self.get_session(session_id)
        if not session:
            return []

        return session.get_conversation_history(limit)

    def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """Get contextual information from session for enhanced queries"""
        session = self.get_session(session_id)
        if not session:
            return {'has_history': False}

        return {
            'has_history': True,
            'conversation_summary': session.get_context_summary(),
            'previous_context': session.extract_context_from_previous(),
            'session_metadata': {
                'query_count': session.metadata['query_count'],
                'total_properties_viewed': session.metadata['total_properties_viewed']
            }
        }

    def clear_session(self, session_id: str) -> bool:
        """Clear a conversation session"""
        with self.lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                session_file = self.persist_directory / f"{session_id}.json"
                if session_file.exists():
                    session_file.unlink()
                logger.info(f"Cleared session: {session_id}")
                return True
            return False

    def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        with self.lock:
            expired = []
            current_time = datetime.now()

            for session_id, session in self.sessions.items():
                if current_time - session.last_accessed > self.session_timeout:
                    expired.append(session_id)

            for session_id in expired:
                del self.sessions[session_id]
                session_file = self.persist_directory / f"{session_id}.json"
                if session_file.exists():
                    session_file.unlink()

            if expired:
                logger.info(f"Cleaned up {len(expired)} expired sessions")

    def get_active_sessions_count(self) -> int:
        """Get number of active sessions"""
        return len(self.sessions)

    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about all sessions"""
        with self.lock:
            total_messages = sum(len(s.messages) for s in self.sessions.values())
            total_queries = sum(s.metadata['query_count'] for s in self.sessions.values())

            return {
                'active_sessions': len(self.sessions),
                'total_messages': total_messages,
                'total_queries': total_queries,
                'avg_messages_per_session': total_messages / len(self.sessions) if self.sessions else 0
            }

    def _save_session(self, session: ConversationSession):
        """Persist session to disk"""
        try:
            session_file = self.persist_directory / f"{session.session_id}.json"
            with open(session_file, 'w') as f:
                json.dump(session.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Error saving session {session.session_id}: {e}")

    def _load_sessions(self):
        """Load sessions from disk"""
        try:
            for session_file in self.persist_directory.glob("*.json"):
                try:
                    with open(session_file, 'r') as f:
                        data = json.load(f)
                        session = ConversationSession.from_dict(data)

                        # Only load non-expired sessions
                        if datetime.now() - session.last_accessed <= self.session_timeout:
                            self.sessions[session.session_id] = session
                        else:
                            # Delete expired session file
                            session_file.unlink()

                except Exception as e:
                    logger.error(f"Error loading session from {session_file}: {e}")

        except Exception as e:
            logger.error(f"Error loading sessions: {e}")


# Global conversation manager instance
conversation_manager = ConversationManager()


if __name__ == "__main__":
    # Test conversation manager
    manager = ConversationManager()

    # Create session
    session_id = manager.create_session()
    print(f"Created session: {session_id}")

    # Add messages
    manager.add_message_to_session(
        session_id, 
        'user', 
        'Show me 2 bedroom apartments',
        {'filters': {'bedrooms': 2}}
    )

    manager.add_message_to_session(
        session_id,
        'assistant',
        'Found 5 properties matching your criteria...'
    )

    manager.add_message_to_session(
        session_id,
        'user',
        'What about ones under £1000?'
    )

    # Get context
    context = manager.get_session_context(session_id)
    print("\n=== Session Context ===")
    print(json.dumps(context, indent=2, default=str))

    # Get history
    history = manager.get_conversation_history(session_id)
    print("\n=== Conversation History ===")
    for msg in history:
        print(f"{msg['role']}: {msg['content']}")

    # Stats
    print("\n=== Stats ===")
    print(json.dumps(manager.get_session_stats(), indent=2))
