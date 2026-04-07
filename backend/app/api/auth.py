from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.models.database import SessionLocal, User
from app.utils.auth import (
    get_password_hash,
    create_access_token,
    authenticate_user,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from datetime import timedelta
import uuid
import re

router = APIRouter()


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    username: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register", response_model=dict)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    # 验证用户名
    if len(request.username) < 3 or len(request.username) > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名长度必须在3-20个字符之间"
        )

    if not re.match(r'^[a-zA-Z0-9_]+$', request.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名只能包含字母、数字和下划线"
        )

    # 验证邮箱
    if "@" not in request.email or "." not in request.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱格式不正确"
        )

    # 验证密码
    if len(request.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码长度至少6位"
        )

    if not re.search(r'[a-zA-Z]', request.password) or not re.search(r'\d', request.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码必须包含字母和数字"
        )

    # 检查是否已存在
    existing_user = db.query(User).filter(
        (User.username == request.username) | (User.email == request.email)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名或邮箱已被注册"
        )

    # 创建用户
    hashed_password = get_password_hash(request.password)
    new_user = User(
        id=str(uuid.uuid4()),
        username=request.username,
        email=request.email,
        hashed_password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "注册成功", "user_id": new_user.id}


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, request.username, request.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已被禁用"
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username
    }


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "created_at": current_user.created_at.isoformat(),
        "total_questions": current_user.total_questions,
        "average_score": current_user.average_score
    }
