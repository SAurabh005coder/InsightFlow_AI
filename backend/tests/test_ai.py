import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.services.ai.context_builder import ContextBuilder
from app.services.ai.prompt_manager import PromptManager
from app.services.ai.response_validator import ResponseValidator
from app.models.models import Role, Dataset, User
import uuid

# Set up test database (SQLite file for testing)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_db.sqlite"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        # Seed default roles
        for r_name in ["CEO", "Store_Manager", "Sales_Manager", "Data_Analyst"]:
            db.add(Role(role_name=r_name, description=r_name))
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
        
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    import os
    if os.path.exists("./test_db.sqlite"):
        try:
            os.remove("./test_db.sqlite")
        except Exception:
            pass

def test_prompt_manager_rules():
    context = "KPI: Gross Revenue = $1,500.25"
    messages = PromptManager.build_messages(context, [], "What is the revenue?")
    
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert "Under no circumstances should you calculate" in messages[0]["content"]
    assert "What is the revenue?" in messages[1]["content"]

def test_response_validator_grounding():
    context = "=== DASHBOARD KPIS ===\n- Gross Revenue: $1,500.25 (Formula: SUM(sales))\n- Net Profit: $350.00"
    
    # 1. Grounded response with correct number
    grounded_res = "The calculated Gross Revenue is $1500.25."
    validated_res = ResponseValidator.validate(grounded_res, context)
    assert validated_res == grounded_res
    
    # 2. Hallucinated response with fake number
    hallucinated_res = "The calculated Gross Revenue is $23,450.00."
    validated_res2 = ResponseValidator.validate(hallucinated_res, context)
    assert validated_res2 == "I cannot find that information in the analytical results."

def test_ai_chat_endpoints():
    # 1. Register user
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": "ai_engineer@insightflowai.com",
            "password": "securepassword",
            "first_name": "AI",
            "last_name": "Engineer",
            "role_name": "CEO"
        }
    )
    assert reg.status_code == 200
    
    # 2. Login to get token
    log = client.post(
        "/api/v1/auth/login",
        data={
            "username": "ai_engineer@insightflowai.com",
            "password": "securepassword"
        }
    )
    assert log.status_code == 200
    token = log.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Create a chat session
    sess_res = client.post(
        "/api/v1/ai/chat/session",
        json={"title": "Test AI Chat"},
        headers=headers
    )
    assert sess_res.status_code == 200
    session_id = sess_res.json()["session_id"]
    
    # 4. List sessions
    list_res = client.get("/api/v1/ai/chat/sessions", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1
    
    # 5. Send message
    msg_res = client.post(
        f"/api/v1/ai/chat/sessions/{session_id}/message",
        json={"content": "Summarize dataset"},
        headers=headers
    )
    assert msg_res.status_code == 200
    res_data = msg_res.json()
    assert "assistant_response" in res_data
    assert len(res_data["messages"]) == 2  # user and assistant messages
