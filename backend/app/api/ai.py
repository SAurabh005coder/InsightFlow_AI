from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.schemas.schemas import (
    ChatSessionCreate,
    ChatSessionResponse,
    ChatMessageCreate,
    ChatMessageResponse,
    ChatResponseWrapper
)
from app.services.ai.chat_persistence import ChatPersistenceService
from app.services.ai.context_builder import ContextBuilder
from app.services.ai.prompt_manager import PromptManager
from app.services.ai.llm_bridge import LLMBridge
from app.services.ai.response_validator import ResponseValidator
from typing import List

router = APIRouter()

@router.post("/chat/session", response_model=ChatSessionResponse)
def create_session(
    session_in: ChatSessionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:
        return ChatPersistenceService.create_session(
            db=db,
            user_id=str(current_user.user_id),
            title=session_in.title,
            dataset_id=session_in.dataset_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create chat session: {str(e)}")

@router.get("/chat/sessions", response_model=List[ChatSessionResponse])
def list_sessions(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:
        return ChatPersistenceService.list_sessions(db=db, user_id=str(current_user.user_id))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list chat sessions: {str(e)}")

@router.get("/chat/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
def get_messages(
    session_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    session = ChatPersistenceService.get_session(db, session_id, str(current_user.user_id))
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found or unauthorized")
    return ChatPersistenceService.get_messages(db, session_id)

@router.post("/chat/sessions/{session_id}/message", response_model=ChatResponseWrapper)
def send_message(
    session_id: str,
    message_in: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # 1. Validate session ownership
    session = ChatPersistenceService.get_session(db, session_id, str(current_user.user_id))
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found or unauthorized")
        
    # 2. Save user message to database
    ChatPersistenceService.save_message(db, session_id, role="user", content=message_in.content)
    
    # 3. Pull conversation history (including the message we just saved)
    history = ChatPersistenceService.get_messages(db, session_id)
    
    # 4. Compile context
    dataset_id_str = str(session.dataset_id) if session.dataset_id else None
    context = ContextBuilder.build_context(db, dataset_id_str, user_id=str(current_user.user_id))
    
    # 5. Build prompt messages (we exclude the latest user message from the history block
    # so we don't repeat it, since it's passed explicitly in the current query parameter)
    prompt_messages = PromptManager.build_messages(context, history[:-1], message_in.content)
    
    # 6. Invoke LLM Bridge
    raw_response = LLMBridge.invoke(prompt_messages, context)
    
    # 7. Validate response (hallucination checks)
    validated_response = ResponseValidator.validate(raw_response, context)
    
    # 8. Save assistant response to database
    ChatPersistenceService.save_message(db, session_id, role="assistant", content=validated_response)
    
    # 9. Return current message history
    updated_history = ChatPersistenceService.get_messages(db, session_id)
    return {
        "assistant_response": validated_response,
        "session_id": session.session_id,
        "messages": updated_history
    }
