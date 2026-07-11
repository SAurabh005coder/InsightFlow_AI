import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.models import ChatSession, ChatMessage
from typing import List, Optional

class ChatPersistenceService:
    @staticmethod
    def create_session(db: Session, user_id: str, title: str = "New Chat", dataset_id: str = None) -> ChatSession:
        user_uuid = uuid.UUID(str(user_id))
        dataset_uuid = uuid.UUID(str(dataset_id)) if dataset_id else None
        
        session = ChatSession(
            user_id=user_uuid,
            dataset_id=dataset_uuid,
            title=title
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def list_sessions(db: Session, user_id: str) -> List[ChatSession]:
        user_uuid = uuid.UUID(str(user_id))
        return db.query(ChatSession).filter(ChatSession.user_id == user_uuid).order_by(ChatSession.updated_at.desc()).all()

    @staticmethod
    def get_session(db: Session, session_id: str, user_id: str) -> Optional[ChatSession]:
        try:
            session_uuid = uuid.UUID(str(session_id))
            user_uuid = uuid.UUID(str(user_id))
        except (ValueError, TypeError):
            return None
        return db.query(ChatSession).filter(
            ChatSession.session_id == session_uuid,
            ChatSession.user_id == user_uuid
        ).first()

    @staticmethod
    def get_messages(db: Session, session_id: str) -> List[ChatMessage]:
        session_uuid = uuid.UUID(str(session_id))
        return db.query(ChatMessage).filter(ChatMessage.session_id == session_uuid).order_by(ChatMessage.created_at.asc()).all()

    @staticmethod
    def save_message(db: Session, session_id: str, role: str, content: str) -> ChatMessage:
        session_uuid = uuid.UUID(str(session_id))
        message = ChatMessage(
            session_id=session_uuid,
            role=role,
            content=content
        )
        db.add(message)
        
        # Touch session updated_at time
        session = db.query(ChatSession).filter(ChatSession.session_id == session_uuid).first()
        if session:
            session.updated_at = datetime.now(timezone.utc)
            
        db.commit()
        db.refresh(message)
        return message
