from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core import security
from app.core.config import settings
from app.core.database import get_db
from app.models.models import User, Role
from app.schemas.schemas import Token, UserCreate, UserResponse
from app.api.deps import get_current_user

router = APIRouter()

def ensure_roles_seeded(db: Session):
    roles = ["CEO", "Store_Manager", "Sales_Manager", "Data_Analyst"]
    for role_name in roles:
        role = db.query(Role).filter(Role.role_name == role_name).first()
        if not role:
            new_role = Role(
                role_name=role_name,
                description=f"Role for {role_name.replace('_', ' ')}"
            )
            db.add(new_role)
    db.commit()

@router.post("/register", response_model=UserResponse)
def register(user_in: UserCreate, db: Session = Depends(get_db)) -> Any:
    # Seed roles if they don't exist yet
    ensure_roles_seeded(db)
    
    # Check if user already exists
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists.",
        )
    
    # Fetch role
    role = db.query(Role).filter(Role.role_name == user_in.role_name).first()
    if not role:
        raise HTTPException(
            status_code=400,
            detail=f"Role '{user_in.role_name}' is invalid. Options are: CEO, Store_Manager, Sales_Manager, Data_Analyst.",
        )
        
    db_user = User(
        email=user_in.email,
        password_hash=security.get_password_hash(user_in.password),
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        role_id=role.role_id,
        is_active=True,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Attach role_name dynamically for response parsing
    db_user.role_name = role.role_name
    return db_user

@router.post("/login", response_model=Token)
def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    ensure_roles_seeded(db)
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )
    
    # Create Access Token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        user.user_id, expires_delta=access_token_expires
    )
    
    role = db.query(Role).filter(Role.role_id == user.role_id).first()
    role_name = role.role_name if role else "Data_Analyst"
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": role_name,
        "user": {
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "user_id": str(user.user_id),
        }
    }

@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    role = db.query(Role).filter(Role.role_id == current_user.role_id).first()
    current_user.role_name = role.role_name if role else "Data_Analyst"
    return current_user
